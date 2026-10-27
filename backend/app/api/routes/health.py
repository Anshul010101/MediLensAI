from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.services.ocr_service import ocr_service

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    ocr_status: dict
    gemini_configured: bool
    version: str = "0.1.0"


@router.get("", response_model=HealthResponse)
def get_health_status() -> HealthResponse:
    """Return backend operational status and service availability."""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        environment=settings.environment,
        ocr_status=ocr_service.get_status(),
        gemini_configured=bool(settings.gemini_api_key),
    )
