import time
from typing import List, Optional, Tuple
import pymupdf
from pydantic import BaseModel, Field

from backend.app.core.security import validate_pdf_signature, InvalidPDFError
from backend.app.models.report import ExtractionMetadata
from backend.app.services.ocr_service import ocr_service
from backend.app.utils.logger import logger, log_processing_event


class ExtractedPage(BaseModel):
    """Container for single-page extracted text and spatial lines."""
    page_number: int  # 1-indexed
    text: str
    lines: List[str]
    has_images: bool = False
    ocr_applied: bool = False


class PDFExtractionResult(BaseModel):
    """Top-level container for multi-page extraction result."""
    pages: List[ExtractedPage]
    metadata: ExtractionMetadata
    raw_full_text: str


class PDFExtractionError(Exception):
    """Raised when PDF extraction encounters fatal parsing errors."""
    pass


class PDFPasswordProtectedError(PDFExtractionError):
    """Raised when uploaded PDF is encrypted with a password."""
    pass


class EmptyPDFError(PDFExtractionError):
    """Raised when uploaded PDF has zero pages or zero readable content."""
    pass


class PDFExtractor:
    """
    Extracts text, lines, and layout metadata from PDF byte streams entirely in-memory.
    Never persists raw PDFs to disk.
    """

    MIN_DIGITAL_TEXT_CHARS = 50

    def extract_from_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> PDFExtractionResult:
        """
        Parse PDF byte stream using PyMuPDF, performing digital extraction and
        conditional OCR fallback when scanned image pages are detected.
        """
        start_time = time.time()

        # Step 1: Validate PDF magic bytes
        if not validate_pdf_signature(pdf_bytes):
            raise InvalidPDFError("The provided file does not have a valid PDF header signature (%PDF-).")

        extracted_pages: List[ExtractedPage] = []
        warnings: List[str] = []
        total_chars = 0
        is_scanned = False
        ocr_applied = False

        try:
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        except Exception as ex:
            raise PDFExtractionError(f"Corrupt or unreadable PDF: {str(ex)}")

        try:
            if doc.is_encrypted:
                raise PDFPasswordProtectedError("The uploaded PDF is password-protected and cannot be analyzed.")

            page_count = len(doc)
            if page_count == 0:
                raise EmptyPDFError("The uploaded PDF contains zero pages.")

            for page_idx in range(page_count):
                page_num = page_idx + 1
                page = doc[page_idx]

                # Extract digital text
                page_text = page.get_text("text") or ""
                lines = [line.strip() for line in page_text.splitlines() if line.strip()]
                image_list = page.get_images(full=True)
                has_images = len(image_list) > 0

                page_ocr_applied = False

                # Check if this page appears to be a scanned image with minimal text
                if len(page_text.strip()) < self.MIN_DIGITAL_TEXT_CHARS and has_images:
                    is_scanned = True
                    if ocr_service.is_available():
                        # Render page to pixmap for OCR
                        pix = page.get_pixmap(dpi=200)
                        img_bytes = pix.tobytes("png")
                        ocr_text, ocr_success, ocr_warn = ocr_service.extract_text_from_image_bytes(img_bytes)
                        if ocr_success and ocr_text.strip():
                            page_text = ocr_text
                            lines = [line.strip() for line in ocr_text.splitlines() if line.strip()]
                            page_ocr_applied = True
                            ocr_applied = True
                        elif ocr_warn:
                            warnings.append(f"Page {page_num}: {ocr_warn}")
                    else:
                        warnings.append(
                            f"Page {page_num} appears to be a scanned image, but OCR is not available on this server."
                        )

                total_chars += len(page_text)
                extracted_pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text=page_text,
                        lines=lines,
                        has_images=has_images,
                        ocr_applied=page_ocr_applied,
                    )
                )

            # Global scan check
            if total_chars < self.MIN_DIGITAL_TEXT_CHARS and not ocr_applied:
                is_scanned = True
                warnings.append("Document text content is very sparse or scanned; standard parsing may be limited.")

            full_text = "\n\n".join([f"--- PAGE {p.page_number} ---\n" + p.text for p in extracted_pages])
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            metadata = ExtractionMetadata(
                page_count=page_count,
                extracted_character_count=total_chars,
                is_scanned=is_scanned,
                ocr_applied=ocr_applied,
                ocr_available=ocr_service.is_available(),
                warnings=warnings,
                processing_time_ms=elapsed_ms,
                is_synthetic=False,
            )

            log_processing_event("pdf_extracted", {
                "file_name": filename,
                "page_count": page_count,
                "ocr_used": ocr_applied,
                "latency_ms": elapsed_ms,
                "status": "success",
            })

            return PDFExtractionResult(
                pages=extracted_pages,
                metadata=metadata,
                raw_full_text=full_text,
            )

        finally:
            doc.close()


pdf_extractor = PDFExtractor()
