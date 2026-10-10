from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Project Hares central configuration schema using Pydantic v2 Settings.
    Enforces required security keys, network URLs, and cryptographic parameters.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Core Application Settings
    PROJECT_NAME: str = "Project Hares"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = Field(..., min_length=32)

    # Meta WhatsApp Business Cloud API Settings
    WHATSAPP_API_VERSION: str = "v21.0"
    WHATSAPP_PHONE_NUMBER_ID: str = Field(..., min_length=1)
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = Field(default="")
    WHATSAPP_ACCESS_TOKEN: str = Field(..., min_length=10)
    WHATSAPP_VERIFY_TOKEN: str = Field(..., min_length=8)
    WHATSAPP_APP_SECRET: str = Field(..., min_length=16)
    WHATSAPP_API_BASE_URL: str = "https://graph.facebook.com"
    WHATSAPP_LOCAL_STORAGE_REGION: str = "UAE"

    # Cryptographic Privacy (FR-4.1 & NFR-1.3)
    CITIZEN_HASH_SALT: str = Field(..., min_length=32)
    RATE_LIMIT_QUERIES_PER_HOUR: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 3600
    REDIS_EPHEMERAL_PAYLOAD_TTL_SECONDS: int = 60

    # Persistence & Caching
    DATABASE_URL: str = Field(..., min_length=10)
    DATABASE_URL_SYNC: str = Field(..., min_length=10)
    REDIS_URL: str = Field(..., min_length=10)
    CELERY_BROKER_URL: str = Field(..., min_length=10)
    CELERY_RESULT_BACKEND: str = Field(..., min_length=10)

    # Sovereign Local AI Cluster & Inference Settings (NFR-1.1, FR-1.x, FR-2.4)
    SLM_API_BASE_URL: str = "http://localhost:8000/v1"
    SLM_MODEL_NAME: str = "llama-3.2-3b-instruct-awq"
    SLM_TIMEOUT_SECONDS: float = 3.0
    ASR_MODEL_SIZE: str = "small"
    ASR_DEVICE: str = "cpu"
    AUDIO_MAX_DURATION_SECONDS: float = 120.0
    CONFORMAL_ALPHA: float = 0.001
    CONFORMAL_THRESHOLD: float = 0.85

    # Municipal Threat Intelligence Portal Settings (FR-4.3)
    ANALYST_API_KEY: str = Field(default="hares_analyst_secret_key_2026", min_length=16)
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @field_validator("CITIZEN_HASH_SALT")
    @classmethod
    def validate_salt_entropy(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError(
                "CITIZEN_HASH_SALT must be at least 32 characters in length for cryptographic entropy."
            )
        return value

    @field_validator("ANALYST_API_KEY")
    @classmethod
    def validate_analyst_api_key(cls, value: str, info) -> str:
        # If in production, prevent default key and enforce high entropy
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            if value == "hares_analyst_secret_key_2026" or len(value) < 32:
                raise ValueError(
                    "In production, ANALYST_API_KEY must be overridden via .env with a secure key >= 32 characters."
                )
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns singleton instance of validated application settings."""
    return Settings()
