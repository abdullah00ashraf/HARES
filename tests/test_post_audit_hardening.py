import pytest
from unittest.mock import MagicMock
from httpx import ASGITransport, AsyncClient
from hares.core.config import Settings
from hares.core.security import get_stix_signing_key, sign_stix_bundle, verify_stix_bundle_signature
from hares.main import app, create_app
from hares.services.rate_limiter import RateLimitResult, RedisTokenBucketRateLimiter


@pytest.mark.asyncio
async def test_auth_verify_endpoint_header_and_body():
    """Verify AUDIT-OBS-30: /api/v1/threats/auth/verify authenticates via header or body."""
    from hares.core.config import get_settings

    settings = get_settings()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Test via X-API-Key header
        resp = await client.post(
            "/api/v1/threats/auth/verify",
            headers={"X-API-Key": settings.ANALYST_API_KEY},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["authenticated"] is True
        assert data["role"] == "soc_analyst"

        # 2. Test via JSON payload passkey
        resp2 = await client.post(
            "/api/v1/threats/auth/verify",
            json={"passkey": settings.ANALYST_API_KEY},
        )
        assert resp2.status_code == 200
        assert resp2.json()["authenticated"] is True

        # 3. Test invalid passkey
        resp_invalid = await client.post(
            "/api/v1/threats/auth/verify",
            json={"passkey": "incorrect_clearance_token"},
        )
        assert resp_invalid.status_code == 403

        # 4. Test missing credentials
        resp_empty = await client.post("/api/v1/threats/auth/verify")
        assert resp_empty.status_code == 401


@pytest.mark.asyncio
async def test_triage_web_rate_limiter(monkeypatch):
    """Verify AUDIT-OBS-34: Web triage endpoint enforces IP rate limiting and emits HTTP 429."""
    # Mock rate limiter to simulate exhausted bucket
    def mock_check_rate_limit(self, client_id, max_requests=None, window_seconds=60):
        return RateLimitResult(
            is_allowed=False,
            current_count=16,
            max_allowed=15,
            reset_seconds=30,
        )

    monkeypatch.setattr(
        RedisTokenBucketRateLimiter, "check_web_triage_rate_limit", mock_check_rate_limit
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/triage/verify",
            data={"text": "Suspicious SMS check"},
        )
        assert resp.status_code == 429
        assert "Rate limit exceeded" in resp.json()["detail"]
        assert resp.headers.get("Retry-After") == "30"


def test_config_production_passkey_validation():
    """Verify AUDIT-OBS-30: In production, leaked passkey is rejected and minimum entropy enforced."""
    base_kwargs = {
        "SECRET_KEY": "a" * 32,
        "WHATSAPP_PHONE_NUMBER_ID": "12345",
        "WHATSAPP_VERIFY_TOKEN": "verify_token_123",
        "WHATSAPP_APP_SECRET": "secret_key_123456",
        "CITIZEN_HASH_SALT": "b" * 32,
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "DATABASE_URL_SYNC": "postgresql+psycopg2://user:pass@localhost:5432/db",
        "REDIS_URL": "redis://localhost:6379/0",
        "CELERY_BROKER_URL": "redis://localhost:6379/1",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
        "CORS_ORIGINS": ["https://hares.dubai.gov.ae"],
        "ENVIRONMENT": "production",
        "ANALYST_API_KEY": "c" * 32,
    }

    # Leaked passkey must be rejected in production
    with pytest.raises(ValueError, match="leaked default passkey"):
        Settings(
            **base_kwargs,
            SOC_ADMIN_PASSWORD="APPledbx@33#hinxtolnimda",
        )

    # Short passkey must be rejected in production
    with pytest.raises(ValueError, match="at least 32 characters"):
        Settings(
            **base_kwargs,
            SOC_ADMIN_PASSWORD="short_passkey",
        )

    # Valid high-entropy passkey succeeds
    valid_settings = Settings(
        **base_kwargs,
        SOC_ADMIN_PASSWORD="d" * 32,
    )
    assert valid_settings.SOC_ADMIN_PASSWORD == "d" * 32


def test_whatsapp_token_permanent_fallback():
    """Verify AUDIT-OBS-31: Falls back to permanent token if temporary token is empty or staging."""
    kwargs = {
        "SECRET_KEY": "a" * 32,
        "WHATSAPP_PHONE_NUMBER_ID": "12345",
        "WHATSAPP_VERIFY_TOKEN": "verify_token_123",
        "WHATSAPP_APP_SECRET": "secret_key_123456",
        "CITIZEN_HASH_SALT": "b" * 32,
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "DATABASE_URL_SYNC": "postgresql+psycopg2://user:pass@localhost:5432/db",
        "REDIS_URL": "redis://localhost:6379/0",
        "CELERY_BROKER_URL": "redis://localhost:6379/1",
        "CELERY_RESULT_BACKEND": "redis://localhost:6379/2",
        "WHATSAPP_ACCESS_TOKEN": "",
        "WHATSAPP_ACCESS_TOKEN_PERMAMENT": "EAAG_permanent_token_xyz_123",
    }
    s = Settings(**kwargs)
    assert s.WHATSAPP_ACCESS_TOKEN == "EAAG_permanent_token_xyz_123"


def test_stix_signing_key_deterministic_derivation(monkeypatch):
    """Verify AUDIT-OBS-36: STIX_SIGNING_KEY_HEX derives persistent ECDSA SECP256R1 key."""
    hex_key = "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90"
    from hares.core import security
    monkeypatch.setattr(security, "_STIX_SIGNING_KEY", None)

    mock_settings = MagicMock()
    mock_settings.STIX_SIGNING_KEY_HEX = hex_key
    monkeypatch.setattr("hares.core.config.get_settings", lambda: mock_settings)

    key1 = get_stix_signing_key()
    assert key1 is not None

    test_bundle = '{"type": "bundle", "id": "bundle--123"}'
    sig = sign_stix_bundle(test_bundle, key1)
    assert verify_stix_bundle_signature(test_bundle, sig, key1.public_key()) is True


def test_production_openapi_docs_disabled(monkeypatch):
    """Verify AUDIT-OBS-39: Docs and OpenAPI schemas are disabled in production."""
    mock_settings = MagicMock()
    mock_settings.ENVIRONMENT = "production"
    mock_settings.PROJECT_NAME = "Project Hares"
    mock_settings.LOG_LEVEL = "INFO"
    mock_settings.CORS_ORIGINS = ["https://hares.ae"]
    mock_settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"

    monkeypatch.setattr("hares.main.get_settings", lambda: mock_settings)
    prod_app = create_app()

    assert prod_app.docs_url is None
    assert prod_app.redoc_url is None
    assert prod_app.openapi_url is None
