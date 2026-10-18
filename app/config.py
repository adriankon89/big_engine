from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "FastAPI App"
    DEBUG: bool = False

    # Security
    SECRET_KEY: SecretStr = Field(
        default=SecretStr("local-development-secret-change-me"),
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET_KEY"),
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database & Redis Connection URIs
    DATABASE_URL: str = "sqlite:///./bid_engine.db"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    DEFAULT_RATE_LIMIT: str = "200/minute"

    # File storage
    UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent / "uploads"

    # Configure Pydantic to read from .env
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
