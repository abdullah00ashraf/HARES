from functools import lru_cache
from typing import Literal
from pydantic import Field, field_validator, model_validator
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
    WHATSAPP_ACCESS_TOKEN: str = Field(default="", min_length=0)
    WHATSAPP_ACCESS_TOKEN_PERMAMENT: str | None = Field(default=None)
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
    SLM_API_KEY: str = Field(default="hares_internal_slm_key", min_length=16)
    SLM_TIMEOUT_SECONDS: float = 3.0
    # Hugging Face ZeroGPU Neural Engine Settings
    HF_SPACE_URL: str = "https://abdullahashraf122-hares-neural-engine.hf.space"
    HF_SPACE_API_NAME: str = "/triage"
    HF_TOKEN: str | None = Field(default=None)
    HF_ZERO_GPU_ENABLED: bool = True
    HF_ZERO_GPU_TIMEOUT_SECONDS: float = 12.0
    ASR_MODEL_SIZE: str = "small"
    ASR_DEVICE: str = "cpu"
    AUDIO_MAX_DURATION_SECONDS: float = 120.0
    CONFORMAL_ALPHA: float = 0.001
    CONFORMAL_THRESHOLD: float = 0.85

    # Municipal Threat Intelligence Portal Settings (FR-4.3, NFR-1.3)
    ANALYST_API_KEY: str = Field(default="hares_analyst_secret_key_2026", min_length=16)
    SOC_ADMIN_SALT_HEX: str = Field(
        default="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
        min_length=32,
    )
    # Salted PBKDF2-HMAC-SHA256 hash of municipal passkey (100,000 iterations); zero plaintext in code
    SOC_ADMIN_PASSWORD_HASH: str = Field(
        default="742d493d2b34741a57abfde398e5fc86ebf8b4c74a629b516ef3d6be223b31c8",
        min_length=32,
    )
    # Optional runtime passkey override (will be hashed and cleared)
    SOC_ADMIN_PASSWORD: str | None = Field(default=None)
    ANALYST_RATE_LIMIT_PER_MINUTE: int = 120
    TRIAGE_WEB_RATE_LIMIT_PER_MINUTE: int = 15
    STIX_SIGNING_KEY_HEX: str = ""
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
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            if value == "hares_analyst_secret_key_2026" or len(value) < 32:
                raise ValueError(
                    "In production, ANALYST_API_KEY must be overridden via .env with a secure key >= 32 characters."
                )
        return value

    @field_validator("SOC_ADMIN_PASSWORD_HASH")
    @classmethod
    def validate_soc_password_hash(cls, value: str, info) -> str:
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            if len(value) < 32:
                raise ValueError("In production, SOC_ADMIN_PASSWORD_HASH must be a valid 64-char PBKDF2 hex hash.")
        return value

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, value: list[str], info) -> list[str]:
        # AUDIT-OBS-15: Prevent insecure localhost CORS in production
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            for origin in value:
                lower_origin = origin.lower()
                if "localhost" in lower_origin or "127.0.0.1" in lower_origin:
                    raise ValueError(
                        f"In production, CORS_ORIGINS cannot contain localhost or loopback addresses: {origin}"
                    )
        return value

    @model_validator(mode="after")
    def resolve_tokens_and_security(self) -> "Settings":
        # AUDIT-OBS-31: Automatic fallback to permanent WhatsApp token if temporary token is empty or placeholder
        if (not self.WHATSAPP_ACCESS_TOKEN or self.WHATSAPP_ACCESS_TOKEN.startswith("EAAG_staging")) and self.WHATSAPP_ACCESS_TOKEN_PERMAMENT:
            self.WHATSAPP_ACCESS_TOKEN = self.WHATSAPP_ACCESS_TOKEN_PERMAMENT

        # AUDIT-OBS-30: Enforce strict passkey hygiene in production
        if self.ENVIRONMENT == "production":
            if self.SOC_ADMIN_PASSWORD == "APPledbx@33#hinxtolnimda":
                raise ValueError(
                    "In production, SOC_ADMIN_PASSWORD cannot be the leaked default passkey ('APPledbx@33#hinxtolnimda')."
                )
            if self.SOC_ADMIN_PASSWORD is not None and len(self.SOC_ADMIN_PASSWORD) < 32:
                raise ValueError(
                    "In production, SOC_ADMIN_PASSWORD must be at least 32 characters in length."
                )
        return self



@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns singleton instance of validated application settings."""
    return Settings()
