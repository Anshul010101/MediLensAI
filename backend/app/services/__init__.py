"""Service layer modules for MediLens AI."""
from backend.app.services.ocr_service import ocr_service, OCRService
from backend.app.services.pdf_extractor import pdf_extractor, PDFExtractor, PDFExtractionResult
from backend.app.services.reference_ranges import (
    parse_reference_interval,
    evaluate_reference_range,
)
from backend.app.services.parser import (
    deterministic_parser,
    DeterministicLabParser,
    ANALYTE_KNOWLEDGE_BASE,
)
from backend.app.services.privacy_sanitizer import (
    privacy_sanitizer,
    PrivacySanitizer,
    SanitizedPayload,
    SanitizedAnalyte,
)
from backend.app.services.gemini_prompt import (
    GeminiStructuredResponse,
    build_gemini_prompt,
)
from backend.app.services.gemini_service import (
    gemini_service,
    GeminiService,
)
from backend.app.services.storage import (
    storage_repo,
    StorageRepository,
)
from backend.app.services.export_service import (
    export_service,
    ExportService,
)

__all__ = [
    "ocr_service",
    "OCRService",
    "pdf_extractor",
    "PDFExtractor",
    "PDFExtractionResult",
    "parse_reference_interval",
    "evaluate_reference_range",
    "deterministic_parser",
    "DeterministicLabParser",
    "ANALYTE_KNOWLEDGE_BASE",
    "privacy_sanitizer",
    "PrivacySanitizer",
    "SanitizedPayload",
    "SanitizedAnalyte",
    "GeminiStructuredResponse",
    "build_gemini_prompt",
    "gemini_service",
    "GeminiService",
    "storage_repo",
    "StorageRepository",
    "export_service",
    "ExportService",
]


