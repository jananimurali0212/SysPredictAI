"""Configuration settings for the System Monitoring Platform."""
import os
from pathlib import Path
from typing import Optional
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

    # Machine Learning & Analytics Settings
    MODEL_DIR: str = str(Path(__file__).resolve().parent.parent / "saved_models")
    ML_MIN_TRAINING_SAMPLES: int = 30
    DEFAULT_FORECAST_HORIZON_SECONDS: int = 60
    
    # Anomaly Detection Thresholds (Configurable)
    ANOMALY_CPU_WARNING: float = 75.0
    ANOMALY_CPU_CRITICAL: float = 90.0
    ANOMALY_MEMORY_WARNING: float = 80.0
    ANOMALY_MEMORY_CRITICAL: float = 92.0
    ANOMALY_DISK_WARNING: float = 85.0
    ANOMALY_DISK_CRITICAL: float = 95.0
    ANOMALY_NET_SPEED_SPIKE_BPS: float = 50_000_000.0  # 50 MB/s
    ISOLATION_FOREST_CONTAMINATION: float = 0.05
    ISOLATION_FOREST_MIN_SAMPLES: int = 40

    # Gemini AI Insights
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

