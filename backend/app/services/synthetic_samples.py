from datetime import datetime
from typing import Dict, List, Optional
import uuid

from backend.app.models.report import (
    AIExplanation,
    AIExplanationStatus,
    EducationalContent,
    ExtractionMetadata,
    FlagStatus,
    ReferenceInterval,
    ReportSummary,
    TestResult,
)
from backend.app.services.parser import ANALYTE_KNOWLEDGE_BASE


def _build_educational_notes(canonical_names: List[str]) -> List[EducationalContent]:
    notes = []
    for name in sorted(set(canonical_names)):
        if name in ANALYTE_KNOWLEDGE_BASE:
            notes.append(
                EducationalContent(
                    analyte_name=name,
                    source="MediLens Deterministic Knowledge Base",
                    physiological_role=ANALYTE_KNOWLEDGE_BASE[name]["role"],
                )
            )
    return notes


def get_synthetic_cbc_summary() -> ReportSummary:
    """Pre-built verified synthetic Complete Blood Count report."""
    tests = [
        TestResult(
            name="White Blood Cells (WBC)",
            canonical_name="White Blood Cells (WBC)",
            category="Complete Blood Count (CBC)",
            value_text="7.2",
            value_numeric=7.2,
            unit="10^3/uL",
            reference_interval=ReferenceInterval(raw_text="4.0 - 10.5", low=4.0, high=10.5, is_numeric=True),
            flag=FlagStatus.NORMAL,
            flag_reason="7.2 is within stated reference interval [4.0 - 10.5]",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="Red Blood Cells (RBC)",
            canonical_name="Red Blood Cells (RBC)",
            category="Complete Blood Count (CBC)",
            value_text="4.80",
            value_numeric=4.80,
            unit="10^6/uL",
            reference_interval=ReferenceInterval(raw_text="4.10 - 5.60", low=4.10, high=5.60, is_numeric=True),
            flag=FlagStatus.NORMAL,
            flag_reason="4.8 is within stated reference interval [4.1 - 5.6]",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="Hemoglobin",
            canonical_name="Hemoglobin",
            category="Complete Blood Count (CBC)",
            value_text="14.5",
            value_numeric=14.5,
            unit="g/dL",
            reference_interval=ReferenceInterval(raw_text="13.5 - 17.5", low=13.5, high=17.5, is_numeric=True),
            flag=FlagStatus.NORMAL,
            flag_reason="14.5 is within stated reference interval [13.5 - 17.5]",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="Hematocrit",
            canonical_name="Hematocrit",
            category="Complete Blood Count (CBC)",
            value_text="42.1",
            value_numeric=42.1,
            unit="%",
            reference_interval=ReferenceInterval(raw_text="38.5 - 50.0", low=38.5, high=50.0, is_numeric=True),
            flag=FlagStatus.NORMAL,
            flag_reason="42.1 is within stated reference interval [38.5 - 50.0]",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="Platelets",
            canonical_name="Platelets",
            category="Complete Blood Count (CBC)",
            value_text="240",
            value_numeric=240.0,
            unit="10^3/uL",
            reference_interval=ReferenceInterval(raw_text="140 - 400", low=140.0, high=400.0, is_numeric=True),
            flag=FlagStatus.NORMAL,
            flag_reason="240.0 is within stated reference interval [140.0 - 400.0]",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="Mean Corpuscular Volume (MCV)",
            canonical_name="Mean Corpuscular Volume (MCV)",
            category="Complete Blood Count (CBC)",
            value_text="88.2",
            value_numeric=88.2,
            unit="fL",
            reference_interval=ReferenceInterval(raw_text="80.0 - 100.0", low=80.0, high=100.0, is_numeric=True),
            flag=FlagStatus.NORMAL,
            flag_reason="88.2 is within stated reference interval [80.0 - 100.0]",
            source_page=1,
            is_synthetic=True,
        ),
    ]

    return ReportSummary(
        id="demo-cbc-" + str(uuid.uuid4())[:8],
        filename="synthetic_cbc_sample.pdf",
        upload_timestamp=datetime.utcnow(),
        metadata=ExtractionMetadata(
            page_count=1,
            extracted_character_count=450,
            is_scanned=False,
            ocr_applied=False,
            ocr_available=False,
            is_synthetic=True,
        ),
        tests=tests,
        educational_notes=_build_educational_notes([t.canonical_name for t in tests]),
        ai_explanation=AIExplanation(
            status=AIExplanationStatus.AI_UNAVAILABLE,
            status_reason="Generative AI explanations are configured in Phase 3. Deterministic summary active."
        ),
        total_tests_detected=len(tests),
        in_range_count=len(tests),
        out_of_range_count=0,
        inconclusive_count=0,
        is_synthetic=True,
    )


def get_synthetic_cmp_summary() -> ReportSummary:
    """Pre-built verified synthetic Comprehensive Metabolic Panel report with elevated Glucose."""
    tests = [
        TestResult(
            name="Glucose",
            canonical_name="Glucose",
            category="Metabolic Panel (CMP)",
            value_text="106*",
            value_numeric=106.0,
            unit="mg/dL",
            reference_interval=ReferenceInterval(raw_text="70 - 99", low=70.0, high=99.0, is_numeric=True),
            flag=FlagStatus.HIGH,
            flag_reason="106.0 is above stated reference upper bound (99.0)",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="Calcium",
            canonical_name="Calcium",
            category="Metabolic Panel (CMP)",
            value_text="9.4",
            value_numeric=9.4,
            unit="mg/dL",
            reference_interval=ReferenceInterval(raw_text="8.6 - 10.2", low=8.6, high=10.2, is_numeric=True),
            flag=FlagStatus.NORMAL,
            flag_reason="9.4 is within stated reference interval [8.6 - 10.2]",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="Sodium",
            canonical_name="Sodium",
            category="Metabolic Panel (CMP)",
            value_text="139",
            value_numeric=139.0,
            unit="mmol/L",
            reference_interval=ReferenceInterval(raw_text="135 - 145", low=135.0, high=145.0, is_numeric=True),
            flag=FlagStatus.NORMAL,
            flag_reason="139.0 is within stated reference interval [135.0 - 145.0]",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="Potassium",
            canonical_name="Potassium",
            category="Metabolic Panel (CMP)",
            value_text="4.3",
            value_numeric=4.3,
            unit="mmol/L",
            reference_interval=ReferenceInterval(raw_text="3.5 - 5.0", low=3.5, high=5.0, is_numeric=True),
            flag=FlagStatus.NORMAL,
            flag_reason="4.3 is within stated reference interval [3.5 - 5.0]",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="Creatinine",
            canonical_name="Creatinine",
            category="Metabolic Panel (CMP)",
            value_text="0.95",
            value_numeric=0.95,
            unit="mg/dL",
            reference_interval=ReferenceInterval(raw_text="0.60 - 1.20", low=0.60, high=1.20, is_numeric=True),
            flag=FlagStatus.NORMAL,
            flag_reason="0.95 is within stated reference interval [0.6 - 1.2]",
            source_page=1,
            is_synthetic=True,
        ),
    ]

    return ReportSummary(
        id="demo-cmp-" + str(uuid.uuid4())[:8],
        filename="synthetic_cmp_glucose_sample.pdf",
        upload_timestamp=datetime.utcnow(),
        metadata=ExtractionMetadata(
            page_count=1,
            extracted_character_count=520,
            is_scanned=False,
            ocr_applied=False,
            ocr_available=False,
            is_synthetic=True,
        ),
        tests=tests,
        educational_notes=_build_educational_notes([t.canonical_name for t in tests]),
        ai_explanation=AIExplanation(
            status=AIExplanationStatus.AI_UNAVAILABLE,
            status_reason="Generative AI explanations are configured in Phase 3. Deterministic summary active."
        ),
        total_tests_detected=len(tests),
        in_range_count=4,
        out_of_range_count=1,
        inconclusive_count=0,
        is_synthetic=True,
    )


def get_synthetic_lipid_summary() -> ReportSummary:
    """Pre-built verified synthetic Lipid Profile report with elevated Cholesterol and Triglycerides."""
    tests = [
        TestResult(
            name="Total Cholesterol",
            canonical_name="Total Cholesterol",
            category="Lipid Profile",
            value_text="215*",
            value_numeric=215.0,
            unit="mg/dL",
            reference_interval=ReferenceInterval(raw_text="< 200", high=200.0, is_numeric=True, comparator="<"),
            flag=FlagStatus.HIGH,
            flag_reason="215.0 exceeds stated upper threshold (< 200.0)",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="Triglycerides",
            canonical_name="Triglycerides",
            category="Lipid Profile",
            value_text="165*",
            value_numeric=165.0,
            unit="mg/dL",
            reference_interval=ReferenceInterval(raw_text="< 150", high=150.0, is_numeric=True, comparator="<"),
            flag=FlagStatus.HIGH,
            flag_reason="165.0 exceeds stated upper threshold (< 150.0)",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="HDL Cholesterol",
            canonical_name="HDL Cholesterol",
            category="Lipid Profile",
            value_text="48",
            value_numeric=48.0,
            unit="mg/dL",
            reference_interval=ReferenceInterval(raw_text="> 40", low=40.0, is_numeric=True, comparator=">"),
            flag=FlagStatus.NORMAL,
            flag_reason="48.0 meets stated lower threshold (> 40.0)",
            source_page=1,
            is_synthetic=True,
        ),
        TestResult(
            name="LDL Cholesterol",
            canonical_name="LDL Cholesterol",
            category="Lipid Profile",
            value_text="134*",
            value_numeric=134.0,
            unit="mg/dL",
            reference_interval=ReferenceInterval(raw_text="< 100", high=100.0, is_numeric=True, comparator="<"),
            flag=FlagStatus.HIGH,
            flag_reason="134.0 exceeds stated upper threshold (< 100.0)",
            source_page=1,
            is_synthetic=True,
        ),
    ]

    return ReportSummary(
        id="demo-lipid-" + str(uuid.uuid4())[:8],
        filename="synthetic_lipid_sample.pdf",
        upload_timestamp=datetime.utcnow(),
        metadata=ExtractionMetadata(
            page_count=1,
            extracted_character_count=410,
            is_scanned=False,
            ocr_applied=False,
            ocr_available=False,
            is_synthetic=True,
        ),
        tests=tests,
        educational_notes=_build_educational_notes([t.canonical_name for t in tests]),
        ai_explanation=AIExplanation(
            status=AIExplanationStatus.AI_UNAVAILABLE,
            status_reason="Generative AI explanations are configured in Phase 3. Deterministic summary active."
        ),
        total_tests_detected=len(tests),
        in_range_count=1,
        out_of_range_count=3,
        inconclusive_count=0,
        is_synthetic=True,
    )


def get_synthetic_sample(sample_type: str) -> Optional[ReportSummary]:
    """Retrieve sample by key (cbc, cmp, lipid, thyroid)."""
    mapping = {
        "cbc": get_synthetic_cbc_summary,
        "cmp": get_synthetic_cmp_summary,
        "glucose": get_synthetic_cmp_summary,
        "lipid": get_synthetic_lipid_summary,
    }
    factory = mapping.get(sample_type.lower())
    if factory:
        return factory()
    return None
