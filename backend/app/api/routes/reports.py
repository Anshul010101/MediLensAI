from datetime import datetime
import re
from typing import Optional
import uuid
from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.core.security import (
    FileTooLargeError,
    InvalidPDFError,
    sanitize_filename,
    validate_file_size,
    validate_pdf_signature,
)
from backend.app.models.report import (
    AIExplanation,
    AIExplanationStatus,
    FlagStatus,
    ReportListItem,
    ReportListResponse,
    ReportSummary,
)
from backend.app.services.export_service import export_service
from backend.app.services.gemini_service import gemini_service
from backend.app.services.parser import deterministic_parser
from backend.app.services.pdf_extractor import (
    EmptyPDFError,
    PDFExtractionError,
    PDFPasswordProtectedError,
    pdf_extractor,
)
from backend.app.services.storage import storage_repo
from backend.app.services.synthetic_samples import get_synthetic_sample
from backend.app.utils.logger import log_processing_event, logger


router = APIRouter(prefix="/reports", tags=["Reports"])



class SampleRequest(BaseModel):
    sample_type: str = "cmp"  # cbc, cmp, glucose, lipid


@router.post("/upload", response_model=ReportSummary)
async def upload_and_process_report(
    file: UploadFile = File(..., description="PDF laboratory report file")
) -> ReportSummary:
    """
    Upload and parse a laboratory report PDF strictly in-memory.
    Performs deterministic extraction and bounds checks.
    Raw PDF is not saved to disk.
    """
    clean_name = sanitize_filename(file.filename or "report.pdf")

    # Read file content into memory
    content = await file.read()
    
    # Check file size limit
    is_valid_size, size_bytes = validate_file_size(content, settings.max_upload_size_mb)
    if not is_valid_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file ({round(size_bytes / (1024*1024), 2)}MB) exceeds maximum allowed size of {settings.max_upload_size_mb}MB."
        )

    # Validate PDF magic bytes
    if not validate_pdf_signature(content):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document signature: uploaded file is not a valid PDF."
        )

    # Extract text using PyMuPDF
    try:
        extraction_result = pdf_extractor.extract_from_bytes(content, filename=clean_name)
    except PDFPasswordProtectedError as ex:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot process encrypted report: {str(ex)}"
        )
    except EmptyPDFError as ex:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Empty report: {str(ex)}"
        )
    except (InvalidPDFError, PDFExtractionError) as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extraction failed: {str(ex)}"
        )
    except Exception as ex:
        logger.error(f"Unexpected error during extraction: {str(ex)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected internal error occurred while reading the document."
        )

    # Deterministic parsing
    test_results, educational_notes = deterministic_parser.parse_pages(extraction_result.pages)

    # Compute aggregate counts
    in_range = sum(1 for t in test_results if t.flag == FlagStatus.NORMAL)
    out_of_range = sum(1 for t in test_results if t.flag in (FlagStatus.LOW, FlagStatus.HIGH, FlagStatus.CRITICAL_LOW, FlagStatus.CRITICAL_HIGH))
    inconclusive = sum(1 for t in test_results if t.flag in (FlagStatus.INCONCLUSIVE, FlagStatus.AMBIGUOUS, FlagStatus.UNSUPPORTED))

    # Phase 3: AI Explanation generation (safe, minimized, non-diagnostic)
    ai_explanation = gemini_service.generate_explanation(test_results)

    report_id = "rep-" + str(uuid.uuid4())

    log_processing_event("report_processed", {
        "file_name": clean_name,
        "page_count": extraction_result.metadata.page_count,
        "test_count": len(test_results),
        "ai_status": ai_explanation.status.value,
        "status": "success",
    })

    summary = ReportSummary(
        id=report_id,
        filename=clean_name,
        upload_timestamp=datetime.utcnow(),
        metadata=extraction_result.metadata,
        tests=test_results,
        educational_notes=educational_notes,
        ai_explanation=ai_explanation,
        total_tests_detected=len(test_results),
        in_range_count=in_range,
        out_of_range_count=out_of_range,
        inconclusive_count=inconclusive,
        is_synthetic=False,
    )

    # Persist structured report to history storage if enabled
    if settings.enable_history_persistence:
        storage_repo.save(summary)

    return summary


@router.post("/sample", response_model=ReportSummary)
def load_synthetic_sample(request: SampleRequest) -> ReportSummary:
    """Load a verified pre-parsed synthetic demonstration report."""
    if not settings.enable_demo_mode:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Synthetic demonstration mode is currently disabled in backend configuration."
        )

    sample = get_synthetic_sample(request.sample_type)
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown synthetic sample type '{request.sample_type}'. Available: cbc, cmp, glucose, lipid."
        )

    # Persist synthetic sample to history storage if enabled
    if settings.enable_history_persistence:
        storage_repo.save(sample)

    return sample


@router.get("", response_model=ReportListResponse)
def list_saved_reports(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Optional search query across filenames and report IDs"),
) -> ReportListResponse:
    """
    List historical analyzed reports with pagination and optional search filter.
    Returns lightweight report summaries for dashboard and history table views.
    """
    items, total = storage_repo.list_reports(page=page, limit=limit, search=search)
    has_more = (page * limit) < total
    return ReportListResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        has_more=has_more,
        history_enabled=settings.enable_history_persistence,
    )


@router.get("/{report_id}", response_model=ReportSummary)
def get_report_by_id(report_id: str) -> ReportSummary:
    """
    Retrieve full structured report findings and AI explanation by report ID.
    """
    clean_id = re.sub(r"[^\w-]", "", report_id)
    report = storage_repo.get(clean_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found in storage.",
        )
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report_by_id(report_id: str):
    """
    Permanently delete a saved report and all its structured findings from history.
    """
    clean_id = re.sub(r"[^\w-]", "", report_id)
    deleted = storage_repo.delete(clean_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found in storage.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{report_id}/export")
def export_report(
    report_id: str,
    format: str = Query("pdf", description="Export format: 'pdf' or 'json'"),
):
    """
    Export a structured report summary as a formatted, clinical-grade PDF or JSON file.
    Does not invent reference intervals or alter deterministic status.
    """
    fmt = format.lower().strip()
    if fmt not in ("pdf", "json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export format '{format}'. Valid options: 'pdf', 'json'.",
        )

    clean_id = re.sub(r"[^\w-]", "", report_id)
    report = storage_repo.get(clean_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' was not found for export.",
        )

    if fmt == "pdf":
        try:
            pdf_bytes = export_service.generate_pdf(report)
            filename = f"medilens_{clean_id}.pdf"
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                },
            )
        except Exception as ex:
            logger.error(f"Error generating PDF export: {str(ex)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while generating the PDF export.",
            )
    else:
        try:
            json_str = export_service.generate_json(report)
            filename = f"medilens_{clean_id}.json"
            return Response(
                content=json_str,
                media_type="application/json",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                },
            )
        except Exception as ex:
            logger.error(f"Error generating JSON export: {str(ex)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred while generating the JSON export.",
            )

