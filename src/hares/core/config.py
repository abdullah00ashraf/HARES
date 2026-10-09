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

    @field_validator("CITIZEN_HASH_SALT")
    @classmethod
    def validate_salt_entropy(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError(
                "CITIZEN_HASH_SALT must be at least 32 characters in length for cryptographic entropy."
            )
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns singleton instance of validated application settings."""
    return Settings()
