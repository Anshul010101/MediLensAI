import os
import re
from typing import Tuple


class SecurityValidationError(Exception):
    """Base exception for file and upload validation failures."""
    pass


class InvalidPDFError(SecurityValidationError):
    """Raised when file content is not a valid PDF."""
    pass


class FileTooLargeError(SecurityValidationError):
    """Raised when uploaded file exceeds maximum allowed size."""
    pass


def validate_pdf_signature(content: bytes) -> bool:
    """
    Validate that the uploaded byte content begins with the valid PDF magic bytes.
    The PDF specification requires '%PDF-' to appear within the first 1024 bytes.
    """
    if not content or len(content) < 5:
        return False
    # PDF magic signature is %PDF- (hex: 25 50 44 46 2d)
    header = content[:1024]
    return b"%PDF-" in header


def validate_file_size(content: bytes, max_size_mb: int = 10) -> Tuple[bool, int]:
    """
    Validate file size against the allowed threshold.
    Returns (is_valid, size_in_bytes).
    """
    size_bytes = len(content)
    max_bytes = max_size_mb * 1024 * 1024
    return (size_bytes <= max_bytes, size_bytes)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize uploaded filename to prevent directory traversal and special character injection.
    """
    # Extract only the base name (remove directory components)
    basename = os.path.basename(filename)
    # Remove null bytes and non-printable characters
    cleaned = re.sub(r"[^\w\s\.-]", "", basename)
    # Strip leading/trailing dots or spaces
    cleaned = cleaned.strip(". ")
    if not cleaned:
        cleaned = "unnamed_report.pdf"
    if not cleaned.lower().endswith(".pdf"):
        cleaned += ".pdf"
    # Limit length
    return cleaned[:100]
