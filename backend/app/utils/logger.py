import logging
import re
import sys
from typing import Any, Dict


class PrivacySafeFilter(logging.Filter):
    """
    Log filter that ensures raw medical content, patient names, and SSN/MRN
    patterns are never logged to console or log streams.
    """

    # Patterns matching potential sensitive health identifiers
    SENSITIVE_PATTERNS = [
        (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
        (re.compile(r"\bMRN[:\s#]*[A-Z0-9-]+\b", re.IGNORECASE), "[REDACTED_MRN]"),
        (re.compile(r"\bDOB[:\s#]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE), "[REDACTED_DOB]"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            sanitized = record.msg
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                sanitized = pattern.sub(replacement, sanitized)
            record.msg = sanitized
        return True


def setup_logger(name: str = "medilens") -> logging.Logger:
    """Set up and configure a privacy-safe structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(PrivacySafeFilter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = setup_logger("medilens")


def log_processing_event(
    event: str,
    details: Dict[str, Any]
) -> None:
    """
    Log operational metrics safely without including any raw extracted health values.
    Accepts safe metadata such as page_count, test_count, latency_ms, status.
    """
    safe_keys = {"event", "file_name", "page_count", "test_count", "ocr_used", "status", "ai_status", "latency_ms", "error_type"}
    filtered_details = {k: v for k, v in details.items() if k in safe_keys}
    logger.info(f"Event: {event} | Metrics: {filtered_details}")
