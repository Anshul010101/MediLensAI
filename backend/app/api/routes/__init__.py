"""API route registration."""
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.reports import router as reports_router

__all__ = ["health_router", "reports_router"]
