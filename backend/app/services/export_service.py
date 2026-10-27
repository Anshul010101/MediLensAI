from datetime import datetime
import io
import json
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from backend.app.models.report import (
    AIExplanationStatus,
    FlagStatus,
    ReportSummary,
)
from backend.app.utils.logger import log_processing_event, logger


class ExportService:
    """
    Produces deterministic, clinical-grade summary PDF and JSON exports
    directly from structured ReportSummary models.
    """

    def generate_pdf(self, report: ReportSummary) -> bytes:
        """
        Generate a branded, professional, non-diagnostic laboratory summary PDF
        using ReportLab directly in-memory.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        story = []
        styles = getSampleStyleSheet()

        # Custom Styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#475569"),
        )
        disclaimer_banner_style = ParagraphStyle(
            "DisclaimerBanner",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#0369a1"),
            backColor=colors.HexColor("#f0f9ff"),
            borderColor=colors.HexColor("#bae6fd"),
            borderWidth=1,
            borderPadding=6,
            spaceAfter=10,
            alignment=1,  # Center
        )
        synthetic_banner_style = ParagraphStyle(
            "SyntheticBanner",
            parent=styles["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#9a3412"),
            backColor=colors.HexColor("#ffedd5"),
            borderColor=colors.HexColor("#fdba74"),
            borderWidth=1,
            borderPadding=5,
            spaceAfter=8,
            alignment=1,
        )
        section_heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
        )
        box_style = ParagraphStyle(
            "Box",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1e293b"),
            backColor=colors.HexColor("#f8fafc"),
            borderColor=colors.HexColor("#cbd5e1"),
            borderWidth=0.5,
            borderPadding=8,
            spaceAfter=8,
        )

        # 1. Non-Diagnostic Disclaimer Banner (Top)
        story.append(Paragraph(
            "<b>INFORMATIONAL SUPPORT AID ONLY — NOT A CLINICAL DIAGNOSTIC OR TREATMENT TOOL</b><br/>"
            "This summary translates laboratory terminology into everyday language. Always review findings directly with a qualified healthcare provider.",
            disclaimer_banner_style
        ))

        # 2. Synthetic Indicator (if applicable)
        if report.is_synthetic:
            story.append(Paragraph(
                "<b>DEMONSTRATION NOTICE:</b> This report contains synthetic test data generated for software evaluation.",
                synthetic_banner_style
            ))

        # 3. Header
        story.append(Paragraph("MediLens AI — Laboratory Report Summary", title_style))
        gen_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        story.append(Paragraph(
            f"<b>Report ID:</b> {report.id} &nbsp;|&nbsp; <b>Source Document:</b> {report.filename} &nbsp;|&nbsp; <b>Exported:</b> {gen_time}",
            subtitle_style
        ))
        story.append(Spacer(1, 10))

        # 4. Summary Metrics Row
        metrics_text = (
            f"<b>Total Tests Analyzed:</b> {report.total_tests_detected} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Within Reference Interval:</b> {report.in_range_count} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Outside Interval:</b> {report.out_of_range_count} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Inconclusive / Qualitative:</b> {report.inconclusive_count}"
        )
        story.append(Paragraph(metrics_text, box_style))

        # 5. Structured Table of Analytes
        story.append(Paragraph("Laboratory Test Results (Deterministic Analysis)", section_heading_style))
        table_data = [
            ["Analyte / Test Name", "Result", "Flag", "Units", "Stated Reference Interval", "Page"]
        ]

        for test in report.tests:
            # Deterministic status badge representation
            flag_str = test.flag.value
            ref_text = test.reference_interval.raw_text if test.reference_interval else "Not stated"
            unit_text = test.unit if test.unit else "—"
            page_text = str(test.source_page) if test.source_page else "—"

            table_data.append([
                test.canonical_name,
                test.value_text,
                flag_str,
                unit_text,
                ref_text,
                page_text,
            ])

        col_widths = [160, 65, 75, 65, 135, 40]
        results_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        results_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(results_table)
        story.append(Spacer(1, 10))

        # 6. Uncertainties & Limitations
        all_uncertainties = []
        for t in report.tests:
            for note in t.uncertainty_notes:
                all_uncertainties.append(f"• <b>{t.canonical_name}:</b> {note}")

        if all_uncertainties:
            story.append(Paragraph("Extraction & Reference Interval Uncertainties", section_heading_style))
            uncertainty_content = "<br/>".join(all_uncertainties[:8])
            story.append(Paragraph(uncertainty_content, box_style))

        # 7. AI Explanation Section (Strictly when completed)
        story.append(Paragraph("Educational Context & Physician Questions", section_heading_style))
        ai = report.ai_explanation
        if ai.status == AIExplanationStatus.COMPLETED and ai.summary_text:
            story.append(Paragraph(
                f"<b>AI Plain-Language Summary ({ai.provider or 'Google Gemini'}):</b><br/>{ai.summary_text}",
                box_style
            ))
            if ai.questions_for_doctor:
                q_lines = ["<b>Suggested Questions to Ask Your Doctor:</b>"]
                for i, q in enumerate(ai.questions_for_doctor, start=1):
                    q_lines.append(f"{i}. {q}")
                story.append(Paragraph("<br/>".join(q_lines), box_style))
        else:
            reason = ai.status_reason or "AI explanation was not generated."
            story.append(Paragraph(
                f"<b>AI Summary Status: Unavailable</b><br/>"
                f"<i>{reason}</i><br/>"
                "Deterministic laboratory extraction and range comparisons above remain fully verified and unaffected.",
                box_style
            ))

        # 8. Deterministic Educational Knowledge Notes
        if report.educational_notes:
            story.append(Paragraph("Physiological Reference Guide (Static Knowledge Base)", section_heading_style))
            edu_lines = []
            for note in report.educational_notes[:6]:
                edu_lines.append(f"• <b>{note.analyte_name}:</b> {note.physiological_role} <i>(Source: {note.source})</i>")
            story.append(Paragraph("<br/>".join(edu_lines), box_style))

        # 9. Bottom Disclaimer
        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"<b>Final Clinical Notice:</b> {report.disclaimer}",
            ParagraphStyle("FooterNote", parent=styles["Italic"], fontSize=7.5, textColor=colors.HexColor("#64748b"))
        ))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        log_processing_event("report_pdf_exported", {
            "file_name": report.filename,
            "status": "success",
        })
        return pdf_bytes

    def generate_json(self, report: ReportSummary) -> str:
        """
        Generate a structured JSON export of the report.
        """
        log_processing_event("report_json_exported", {
            "file_name": report.filename,
            "status": "success",
        })
        return report.model_dump_json(indent=2)


export_service = ExportService()
