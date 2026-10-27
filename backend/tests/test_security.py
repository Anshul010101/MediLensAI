import pytest
from backend.app.core.security import (
    validate_pdf_signature,
    validate_file_size,
    sanitize_filename,
)


def test_validate_pdf_signature_valid():
    valid_pdf_content = b"%PDF-1.4\n%some binary data\n%%EOF"
    assert validate_pdf_signature(valid_pdf_content) is True


def test_validate_pdf_signature_invalid():
    assert validate_pdf_signature(b"") is False
    assert validate_pdf_signature(b"GIF89a...") is False
    assert validate_pdf_signature(b"<html><body>Not a PDF</body></html>") is False
    assert validate_pdf_signature(b"PK\x03\x04") is False  # ZIP


def test_validate_file_size():
    data_1mb = b"0" * (1024 * 1024)
    is_valid, size = validate_file_size(data_1mb, max_size_mb=10)
    assert is_valid is True
    assert size == 1024 * 1024

    data_11mb = b"0" * (11 * 1024 * 1024)
    is_valid_large, size_large = validate_file_size(data_11mb, max_size_mb=10)
    assert is_valid_large is False
    assert size_large == 11 * 1024 * 1024


def test_sanitize_filename():
    assert sanitize_filename("normal_report.pdf") == "normal_report.pdf"
    assert sanitize_filename("../../../etc/passwd.pdf") == "passwd.pdf"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.pdf") == "cmd.pdf"
    assert sanitize_filename("patient@#$report!2026.pdf") == "patientreport2026.pdf"
    assert sanitize_filename("") == "unnamed_report.pdf"
    assert sanitize_filename("report_without_ext") == "report_without_ext.pdf"
