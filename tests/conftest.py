import os
import pytest

# Configure hermetic test environment variables immediately upon conftest loading,
# ensuring settings are present before test module collection.
test_defaults = {
    "PROJECT_NAME": "Project Hares Test",
    "ENVIRONMENT": "development",
    "DEBUG": "true",
    "LOG_LEVEL": "DEBUG",
    "SECRET_KEY": "test-secret-key-must-be-at-least-32-chars-long",
    "WHATSAPP_API_VERSION": "v21.0",
    "WHATSAPP_PHONE_NUMBER_ID": "100000000000000",
    "WHATSAPP_BUSINESS_ACCOUNT_ID": "200000000000000",
    "WHATSAPP_ACCESS_TOKEN": "test-access-token-at-least-10-chars",
    "WHATSAPP_VERIFY_TOKEN": "test-verify-token",
    "WHATSAPP_APP_SECRET": "test-app-secret-16chars",
    "WHATSAPP_API_BASE_URL": "https://graph.facebook.com",
    "WHATSAPP_LOCAL_STORAGE_REGION": "UAE",
    "CITIZEN_HASH_SALT": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    "RATE_LIMIT_QUERIES_PER_HOUR": "5",
    "RATE_LIMIT_WINDOW_SECONDS": "3600",
    "REDIS_EPHEMERAL_PAYLOAD_TTL_SECONDS": "60",
    "POSTGRES_USER": "hares_admin",
    "POSTGRES_PASSWORD": "test_password",
    "POSTGRES_DB": "hares_threat_db",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
    "DATABASE_URL_SYNC": "sqlite:///:memory:",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_PASSWORD": "test_redis_password",
    "REDIS_DB": "0",
    "REDIS_URL": "redis://:test_redis_password@localhost:6379/0",
    "CELERY_BROKER_URL": "redis://:test_redis_password@localhost:6379/1",
    "CELERY_RESULT_BACKEND": "redis://:test_redis_password@localhost:6379/2",
}
for key, value in test_defaults.items():
    os.environ.setdefault(key, value)


@pytest.fixture(autouse=True, scope="session")
def set_test_environment() -> None:
    """Session fixture ensuring settings singleton cache is fresh."""
    from hares.core.config import get_settings
    get_settings.cache_clear()
