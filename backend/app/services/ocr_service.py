import shutil
import subprocess
from typing import Optional, Tuple
from PIL import Image
import io

from backend.app.config import settings
from backend.app.utils.logger import logger


class OCRService:
    """
    Manages optional OCR operations using Tesseract.
    Explicitly detects whether Tesseract is installed and available,
    and returns transparent warnings instead of inventing text.
    """

    def __init__(self, tesseract_cmd: Optional[str] = None):
        self.custom_cmd = tesseract_cmd or settings.tesseract_cmd
        self._availability_checked = False
        self._is_available = False
        self._version_info = "Not installed"

    def is_available(self) -> bool:
        """Check if tesseract binary is accessible and executable."""
        if not self._availability_checked:
            self._check_availability()
        return self._is_available

    def get_status(self) -> dict:
        """Return diagnostic status information about OCR capability."""
        return {
            "ocr_available": self.is_available(),
            "tesseract_cmd": self.custom_cmd or "system PATH",
            "version_info": self._version_info,
        }

    def _check_availability(self) -> None:
        cmd = self.custom_cmd if self.custom_cmd else "tesseract"
        # Check if command is in PATH or exists as file
        resolved_cmd = shutil.which(cmd) or (cmd if cmd and shutil.which(cmd) else None)
        
        if not resolved_cmd:
            self._is_available = False
            self._version_info = "Tesseract executable not found in PATH or configured path"
            self._availability_checked = True
            return

        try:
            result = subprocess.run(
                [resolved_cmd, "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self._is_available = True
                self._version_info = result.stdout.splitlines()[0] if result.stdout else "Available"
                import pytesseract
                if self.custom_cmd:
                    pytesseract.pytesseract.tesseract_cmd = self.custom_cmd
            else:
                self._is_available = False
                self._version_info = f"Tesseract error: return code {result.returncode}"
        except Exception as ex:
            self._is_available = False
            self._version_info = f"Failed to execute tesseract: {str(ex)}"
        finally:
            self._availability_checked = True

    def extract_text_from_image_bytes(self, image_bytes: bytes) -> Tuple[str, bool, Optional[str]]:
        """
        Run OCR on image bytes.
        Returns (extracted_text, success, error_or_warning_message).
        """
        if not self.is_available():
            warning = "OCR is not available on this server. Scanned text could not be extracted."
            logger.warning(warning)
            return ("", False, warning)

        try:
            import pytesseract
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return (text, True, None)
        except Exception as ex:
            err_msg = f"OCR processing failed: {str(ex)}"
            logger.error(err_msg)
            return ("", False, err_msg)


ocr_service = OCRService()
