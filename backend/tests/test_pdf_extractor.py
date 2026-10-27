import os
import pymupdf
import pytest


from backend.app.core.security import InvalidPDFError
from backend.app.services.pdf_extractor import (
    EmptyPDFError,
    PDFExtractionError,
    pdf_extractor,
)


@pytest.fixture
def sample_cbc_pdf_bytes():
    path = os.path.join(os.path.dirname(__file__), "..", "sample_reports", "synthetic_cbc_report.pdf")
    with open(path, "rb") as f:
        return f.read()


def test_extract_valid_pdf(sample_cbc_pdf_bytes):
    result = pdf_extractor.extract_from_bytes(sample_cbc_pdf_bytes, filename="test_cbc.pdf")
    assert result.metadata.page_count >= 1
    assert result.metadata.extracted_character_count > 100
    assert result.metadata.is_scanned is False
    assert len(result.pages) == result.metadata.page_count
    assert result.pages[0].page_number == 1
    assert any("Hemoglobin" in line for line in result.pages[0].lines)


def test_extract_invalid_signature():
    with pytest.raises(InvalidPDFError):
        pdf_extractor.extract_from_bytes(b"INVALID_HEADER_DATA")


def test_extract_corrupt_pdf():
    # Header says %PDF- but rest is invalid/corrupt
    with pytest.raises(PDFExtractionError):
        pdf_extractor.extract_from_bytes(b"%PDF-1.4\nBROKEN_CORRUPT_BYTES")


def test_extract_empty_pdf():
    # Valid PDF container with zero pages
    zero_page_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [] /Count 0>> endobj\n"
        b"xref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000057 00000 n \n"
        b"trailer <</Size 3 /Root 1 0 R>>\nstartxref\n107\n%%EOF"
    )
    with pytest.raises(EmptyPDFError):
        pdf_extractor.extract_from_bytes(zero_page_pdf)

