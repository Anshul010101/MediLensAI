import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_synthetic_pdf(filepath: str, title: str, subtitle: str, test_rows: list):
    """Generate a clean synthetic medical lab report PDF."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    # Synthetic banner style
    banner_style = ParagraphStyle(
        'SyntheticBanner',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor("#7c2d12"),
        backColor=colors.HexColor("#ffedd5"),
        borderColor=colors.HexColor("#f97316"),
        borderWidth=1,
        borderPadding=6,
        spaceAfter=12,
        alignment=1, # Center
    )

    story.append(Paragraph("<b>DEMONSTRATION ONLY — SYNTHETIC HEALTH DATASET — NOT A REAL PATIENT REPORT</b>", banner_style))
    story.append(Paragraph(f"<b>{title}</b>", styles['Title']))
    story.append(Paragraph(f"<b>Panel:</b> {subtitle} | <b>Facility:</b> Synthetic Demo Health Lab | <b>Date:</b> 2026-10-26", styles['Normal']))
    story.append(Spacer(1, 12))

    # Table of tests
    table_data = [["Test / Analyte", "Result", "Flag", "Units", "Reference Interval"]]
    for row in test_rows:
        table_data.append(row)

    table = Table(table_data, colWidths=[180, 70, 50, 90, 130])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Notice:</b> This document was synthetically generated for software testing and verification purposes.", styles['Italic']))

    doc.build(story)
    print(f"Generated synthetic report: {filepath}")


def create_all_samples():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. CBC
    cbc_rows = [
        ["White Blood Cells (WBC)", "7.2", "", "10^3/uL", "4.0 - 10.5"],
        ["Red Blood Cells (RBC)", "4.80", "", "10^6/uL", "4.10 - 5.60"],
        ["Hemoglobin", "14.5", "", "g/dL", "13.5 - 17.5"],
        ["Hematocrit", "42.1", "", "%", "38.5 - 50.0"],
        ["Platelets", "240", "", "10^3/uL", "140 - 400"],
        ["Mean Corpuscular Volume", "88.2", "", "fL", "80.0 - 100.0"],
    ]
    generate_synthetic_pdf(
        os.path.join(base_dir, "synthetic_cbc_report.pdf"),
        "Comprehensive Complete Blood Count (CBC)",
        "Routine Hematology",
        cbc_rows
    )

    # 2. CMP / Glucose
    cmp_rows = [
        ["Glucose", "106", "H", "mg/dL", "70 - 99"],
        ["Calcium", "9.4", "", "mg/dL", "8.6 - 10.2"],
        ["Sodium", "139", "", "mmol/L", "135 - 145"],
        ["Potassium", "4.3", "", "mmol/L", "3.5 - 5.0"],
        ["Chloride", "101", "", "mmol/L", "96 - 106"],
        ["Carbon Dioxide", "24", "", "mmol/L", "20 - 29"],
        ["Blood Urea Nitrogen", "16", "", "mg/dL", "7 - 20"],
        ["Creatinine", "0.95", "", "mg/dL", "0.60 - 1.20"],
        ["eGFR", "98", "", "mL/min/1.73m2", "> 60"],
    ]
    generate_synthetic_pdf(
        os.path.join(base_dir, "synthetic_cmp_glucose_report.pdf"),
        "Comprehensive Metabolic Panel (CMP)",
        "Serum Chemistry",
        cmp_rows
    )

    # 3. Lipid Profile
    lipid_rows = [
        ["Total Cholesterol", "215", "H", "mg/dL", "< 200"],
        ["Triglycerides", "165", "H", "mg/dL", "< 150"],
        ["HDL Cholesterol", "48", "", "mg/dL", "> 40"],
        ["LDL Cholesterol", "134", "H", "mg/dL", "< 100"],
    ]
    generate_synthetic_pdf(
        os.path.join(base_dir, "synthetic_lipid_panel_report.pdf"),
        "Lipid Profile",
        "Cardiovascular Risk Biomarkers",
        lipid_rows
    )

    # 4. Thyroid
    thyroid_rows = [
        ["TSH", "2.10", "", "uIU/mL", "0.45 - 4.50"],
        ["Free T4", "1.25", "", "ng/dL", "0.82 - 1.77"],
    ]
    generate_synthetic_pdf(
        os.path.join(base_dir, "synthetic_thyroid_report.pdf"),
        "Thyroid Function Panel",
        "Endocrinology",
        thyroid_rows
    )


if __name__ == "__main__":
    create_all_samples()
