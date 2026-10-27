from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class FlagStatus(str, Enum):
    """
    Deterministic classification of a test value against the report's stated reference interval.
    NOTE: CRITICAL status is never inferred without an explicit, validated panic-value threshold.
    """
    NORMAL = "NORMAL"
    LOW = "LOW"
    HIGH = "HIGH"
    INCONCLUSIVE = "INCONCLUSIVE"      # Range or value exists but is non-numeric/textual (e.g. "Negative")
    AMBIGUOUS = "AMBIGUOUS"            # Multiple conflicting values or parse ambiguity
    UNSUPPORTED = "UNSUPPORTED"        # Detected test without verifiable bounds
    CRITICAL_LOW = "CRITICAL_LOW"      # Reserved ONLY for validated panic values
    CRITICAL_HIGH = "CRITICAL_HIGH"    # Reserved ONLY for validated panic values


class ReferenceInterval(BaseModel):
    """
    Laboratory stated reference range extracted directly from the document.
    Never fabricated or guessed.
    """
    raw_text: str = Field(description="Exact reference range text as extracted from the report")
    low: Optional[float] = Field(default=None, description="Parsed numeric lower bound")
    high: Optional[float] = Field(default=None, description="Parsed numeric upper bound")
    unit: Optional[str] = Field(default=None, description="Unit stated with reference range")
    is_numeric: bool = Field(default=True, description="True if range has numeric boundary")
    comparator: Optional[str] = Field(default=None, description="E.g., '<', '<=', '>', '>=' for single-sided bounds")


class TestResult(BaseModel):
    """
    Structured laboratory analyte result extracted deterministically.
    Preserves original text representations alongside numeric parses.
    """
    __test__ = False  # Prevent pytest from treating model as test class
    name: str = Field(description="Test name as extracted from the report")

    canonical_name: str = Field(description="Normalized medical analyte identifier (e.g., 'Hemoglobin', 'Glucose')")
    category: str = Field(default="General", description="Lab panel category: CBC, CMP, Lipid Profile, Thyroid, etc.")
    value_text: str = Field(description="Exact raw value as extracted from document")
    value_numeric: Optional[float] = Field(default=None, description="Parsed floating-point value if numeric")
    unit: Optional[str] = Field(default=None, description="Exact unit as extracted from document")
    reference_interval: Optional[ReferenceInterval] = Field(
        default=None,
        description="Reference interval stated by the laboratory. None if absent in report."
    )
    flag: FlagStatus = Field(
        default=FlagStatus.INCONCLUSIVE,
        description="Deterministic classification against stated reference interval"
    )
    flag_reason: str = Field(
        default="",
        description="Clear explanation of how the flag was evaluated (e.g., '14.2 within [13.5 - 17.5] g/dL')"
    )
    source_page: Optional[int] = Field(
        default=None,
        description="1-indexed PDF page where this test result was located"
    )
    uncertainty_notes: List[str] = Field(
        default_factory=list,
        description="Notes regarding extraction ambiguity, missing units, or atypical format"
    )
    is_synthetic: bool = Field(
        default=False,
        description="Visually identifies if this result is from a synthetic demonstration dataset"
    )


class ExtractionMetadata(BaseModel):
    """Operational and technical details of the document processing."""
    page_count: int
    extracted_character_count: int
    is_scanned: bool = False
    ocr_applied: bool = False
    ocr_available: bool = False
    warnings: List[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0
    is_synthetic: bool = False


class EducationalContent(BaseModel):
    """
    Rule-based, static physiological information explaining what an analyte is.
    Explicitly decoupled from generative AI output.
    """
    analyte_name: str
    source: str = "MediLens Deterministic Knowledge Base"
    physiological_role: str
    clinical_disclaimer: str = (
        "Educational content only. Analyte roles can vary with health conditions. "
        "Consult your healthcare provider for clinical interpretation."
    )


class AIExplanationStatus(str, Enum):
    AI_UNAVAILABLE = "ai_unavailable"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class AIExplanation(BaseModel):
    """
    Generative AI explanation produced by Google Gemini.
    Explicitly tracked with status and provider metadata.
    """
    status: AIExplanationStatus = AIExplanationStatus.AI_UNAVAILABLE
    provider: Optional[str] = None
    model: Optional[str] = None
    summary_text: Optional[str] = None
    per_test_explanations: Dict[str, str] = Field(
        default_factory=dict,
        description="Plain-language educational context for specific analytes"
    )
    limitations_and_uncertainty: List[str] = Field(
        default_factory=list,
        description="Explicit documentation of missing ranges, units, or parsing uncertainty"
    )
    questions_for_doctor: List[str] = Field(default_factory=list)
    status_reason: Optional[str] = None
    disclaimer: str = (
        "This AI summary is informational and non-diagnostic. "
        "Never alter medication or treatment without consulting a licensed physician."
    )



class ReportSummary(BaseModel):
    """Top-level aggregate response for a processed lab report."""
    id: str
    filename: str
    upload_timestamp: datetime
    metadata: ExtractionMetadata
    tests: List[TestResult]
    educational_notes: List[EducationalContent] = Field(default_factory=list)
    ai_explanation: AIExplanation = Field(
        default_factory=lambda: AIExplanation(
            status=AIExplanationStatus.AI_UNAVAILABLE,
            status_reason="Gemini service not yet configured or executed."
        )
    )
    total_tests_detected: int = 0
    in_range_count: int = 0
    out_of_range_count: int = 0
    inconclusive_count: int = 0
    is_synthetic: bool = False
    disclaimer: str = (
        "MediLens AI is an informational communication aid, not a medical diagnostic or treatment system. "
        "Always review laboratory findings directly with a qualified healthcare professional."
    )


class ReportListItem(BaseModel):
    """Lightweight summary of a report for list views and history tables."""
    id: str
    filename: str
    upload_timestamp: datetime
    total_tests_detected: int
    in_range_count: int
    out_of_range_count: int
    inconclusive_count: int
    is_synthetic: bool = False
    ai_status: AIExplanationStatus = AIExplanationStatus.AI_UNAVAILABLE


class ReportListResponse(BaseModel):
    """Paginated list of historical reports."""
    items: List[ReportListItem]
    total: int
    page: int
    limit: int
    has_more: bool
    history_enabled: bool = True

