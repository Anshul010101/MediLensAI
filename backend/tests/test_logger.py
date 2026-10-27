import logging
import pytest

from backend.app.utils.logger import PrivacySafeFilter, log_processing_event


def test_privacy_safe_filter_redaction():
    filter_instance = PrivacySafeFilter()
    
    # Test record containing SSN
    record_ssn = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Patient file with SSN 123-45-6789 processed",
        args=(), exc_info=None
    )
    filter_instance.filter(record_ssn)
    assert "123-45-6789" not in record_ssn.msg
    assert "[REDACTED_SSN]" in record_ssn.msg

    # Test record containing MRN
    record_mrn = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Found record MRN: 98765-AB in system",
        args=(), exc_info=None
    )
    filter_instance.filter(record_mrn)
    assert "[REDACTED_MRN]" in record_mrn.msg

    # Test record containing DOB
    record_dob = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Patient info DOB: 05/14/1982 matched",
        args=(), exc_info=None
    )
    filter_instance.filter(record_dob)
    assert "[REDACTED_DOB]" in record_dob.msg


def test_log_processing_event_filters_unauthorized_fields(caplog):
    with caplog.at_level(logging.INFO):
        log_processing_event("test_event", {
            "file_name": "clean_report.pdf",
            "page_count": 2,
            "patient_name": "John Doe",  # should be filtered out
            "lab_result_values": "Glucose: 150",  # should be filtered out
            "status": "success",
        })
    log_text = caplog.text
    assert "clean_report.pdf" in log_text
    assert "John Doe" not in log_text
    assert "Glucose: 150" not in log_text
