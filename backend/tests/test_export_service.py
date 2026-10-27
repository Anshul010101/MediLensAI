import datetime
import json
import pytest

from backend.app.core.security import validate_pdf_signature
from backend.app.models.report import (
    AIExplanation,
    AIExplanationStatus,
    ExtractionMetadata,
    FlagStatus,
    ReferenceInterval,
    ReportSummary,
    TestResult,
)
from backend.app.services.export_service import export_service


@pytest.fixture
def export_sample_report():
    return ReportSummary(
        id="rep-export-test",
        filename="cbc_sample.pdf",
        upload_timestamp=datetime.datetime(2026, 10, 27, 11, 0, 0),
        metadata=ExtractionMetadata(
            page_count=1,
            extracted_character_count=400,
            is_scanned=False,
            ocr_applied=False,
            ocr_available=False,
            is_synthetic=True,
        ),
        tests=[
            TestResult(
                name="Hemoglobin",
                canonical_name="Hemoglobin",
                category="Complete Blood Count",
                value_text="14.5",
                value_numeric=14.5,
                unit="g/dL",
                reference_interval=ReferenceInterval(raw_text="13.5 - 17.5", low=13.5, high=17.5, is_numeric=True),
                flag=FlagStatus.NORMAL,
                source_page=1,
            ),
            TestResult(
                name="Platelets",
                canonical_name="Platelets",
                category="Complete Blood Count",
                value_text="130*",
                value_numeric=130.0,
                unit="10^3/uL",
                reference_interval=ReferenceInterval(raw_text="140 - 400", low=140.0, high=400.0, is_numeric=True),
                flag=FlagStatus.LOW,
                source_page=1,
                uncertainty_notes=["Result slightly below standard lab threshold."],
            ),
        ],
        educational_notes=[],
        ai_explanation=AIExplanation(
            status=AIExplanationStatus.COMPLETED,
            provider="Google Gemini",
            summary_text="Your hemoglobin is normal, while platelets are slightly below standard reference intervals.",
            questions_for_doctor=["Should we recheck my platelet count in 4 weeks?"],
        ),
        total_tests_detected=2,
        in_range_count=1,
        out_of_range_count=1,
        inconclusive_count=0,
        is_synthetic=True,
    )


def test_pdf_export_structure_and_signature(export_sample_report):
    pdf_bytes = export_service.generate_pdf(export_sample_report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # Must have valid PDF magic signature %PDF-
    assert validate_pdf_signature(pdf_bytes) is True


def test_pdf_export_with_ai_unavailable(export_sample_report):
    # Set AI status to unavailable
    export_sample_report.ai_explanation = AIExplanation(
        status=AIExplanationStatus.AI_UNAVAILABLE,
        status_reason="Gemini API key is not configured.",
    )
    pdf_bytes = export_service.generate_pdf(export_sample_report)
    assert validate_pdf_signature(pdf_bytes) is True


def test_json_export_structure(export_sample_report):
    json_str = export_service.generate_json(export_sample_report)
    assert isinstance(json_str, str)
    data = json.loads(json_str)
    assert data["id"] == "rep-export-test"
    assert data["filename"] == "cbc_sample.pdf"
    assert len(data["tests"]) == 2
    assert data["tests"][0]["canonical_name"] == "Hemoglobin"
    assert data["tests"][1]["flag"] == "LOW"
    assert data["ai_explanation"]["status"] == "completed"
