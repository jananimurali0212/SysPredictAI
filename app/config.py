"""Configuration settings for the System Monitoring Platform."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    APP_NAME: str = "AI-Powered Real-Time System Monitoring Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Base directory
    BASE_DIR: Path = Path(__file__).resolve().parent.parent

    # Database
    DATABASE_PATH: str = str(Path(__file__).resolve().parent.parent / "system_metrics.db")
    DB_PRAGMA_WAL: bool = True

    # Monitoring cadence
    METRICS_INTERVAL_SECONDS: float = 1.0
    HISTORY_RETENTION_HOURS: int = 24
    PROCESS_LIMIT: int = 50

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

