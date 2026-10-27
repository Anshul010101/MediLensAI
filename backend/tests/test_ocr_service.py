import pytest

from backend.app.services.ocr_service import OCRService


def test_ocr_unavailable_behavior():
    # Service with non-existent executable
    service = OCRService(tesseract_cmd="non_existent_tesseract_binary_xyz")
    assert service.is_available() is False
    status = service.get_status()
    assert status["ocr_available"] is False
    assert "not found" in status["version_info"].lower() or "error" in status["version_info"].lower()

    # When extracting text while unavailable, returns transparent warning and no hallucinated text
    text, success, warning = service.extract_text_from_image_bytes(b"dummy_png_bytes")
    assert text == ""
    assert success is False
    assert warning is not None
    assert "not available" in warning
