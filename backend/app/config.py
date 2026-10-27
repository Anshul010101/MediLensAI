from pathlib import Path
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Application settings with environment variable overrides."""

    app_name: str = "MediLens AI Backend"
    environment: str = "development"
    debug: bool = False

    # Security & PDF limits
    max_upload_size_mb: int = Field(default=10, description="Maximum permitted PDF size in megabytes")
    allowed_extensions: List[str] = [".pdf"]
    
    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Optional OCR configuration
    tesseract_cmd: str = Field(
        default="",
        description="Optional absolute path to tesseract executable if not in PATH"
    )

    # AI Configuration (Gemini) - Phase 3
    gemini_api_key: str = Field(
        default="",
        description="Google Gemini API key (kept confidential; never committed or logged)"
    )
    gemini_model: str = Field(
        default="gemini-3.5-flash",
        description="Validated Google Gemini model identifier"
    )
    gemini_timeout_seconds: float = Field(
        default=30.0,
        description="Timeout in seconds for Gemini API generation requests"
    )
    gemini_max_retries: int = Field(
        default=2,
        description="Maximum bounded retries for transient network/rate-limit errors"
    )
    gemini_temperature: float = Field(
        default=0.2,
        description="Sampling temperature for deterministic, factual explanations"
    )


    # History Persistence Configuration - Phase 4
    enable_history_persistence: bool = Field(
        default=True,
        description="Enable SQLite storage for structured report history"
    )
    sqlite_db_path: str = Field(
        default="medilens_history.db",
        description="Path to SQLite database file for report history"
    )

    # Demo mode
    enable_demo_mode: bool = True


    model_config = SettingsConfigDict(
        env_file=(
            str(ROOT_DIR / ".env"),
            str(BACKEND_DIR / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
