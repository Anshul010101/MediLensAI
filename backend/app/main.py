from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.reports import router as reports_router
from backend.app.config import settings
from backend.app.core.security import SecurityValidationError
from backend.app.utils.logger import logger

app = FastAPI(
    title=settings.app_name,
    description="MediLens AI — Deterministic Laboratory Report Parsing & Educational Communication Engine",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security exception handler
@app.exception_handler(SecurityValidationError)
async def security_validation_handler(request: Request, exc: SecurityValidationError):
    logger.warning(f"Security validation rejected request: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )

# Include API v1 routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "MediLens AI API is running.",
        "status": "online",
        "docs": "/docs",
        "version": "0.1.0",
    }
