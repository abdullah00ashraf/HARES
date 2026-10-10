import pytest
from unittest.mock import MagicMock
from hares.engine.allowlist import AllowlistEngine
from hares.engine.homograph import HomographDetector
from hares.engine.sanitizer import EntityExtractor, PIIScrubber
from hares.services.rate_limiter import RedisTokenBucketRateLimiter


def test_audit_obs_06_text_slicing_bound():
    """Verify AUDIT-OBS-06: Sanitizer and extractor strictly bound oversized payloads to 4096 chars."""
    extractor = EntityExtractor()
    scrubber = PIIScrubber()

    # Create oversized 100,000 character payload
    oversized_text = "https://example.com/ " + ("A" * 100000)

    # Extraction must execute without CPU lockup and process bounded slice
    entities = extractor.extract(oversized_text)
    assert any("https://example.com" in u for u in entities["urls"])

    scrubbed = scrubber.scrub(oversized_text)
    assert len(scrubbed) <= 4096


def test_audit_obs_07_rate_limiter_lua_atomicity():
    """Verify AUDIT-OBS-07: Rate limiter invokes atomic Redis Lua script evaluation."""
    mock_redis = MagicMock()
    # Mock return from Lua script: [current_count, ttl]
    mock_redis.eval.return_value = [1, 3600]

    limiter = RedisTokenBucketRateLimiter(redis_client=mock_redis)
    res = limiter.check_and_increment("citizen_hash_test_123")

    assert res.is_allowed is True
    assert res.current_count == 1
    assert res.reset_seconds == 3600
    # Assert eval was called with the atomic Lua script
    mock_redis.eval.assert_called_once()
    assert "INCR" in mock_redis.eval.call_args[0][0]
    assert "EXPIRE" in mock_redis.eval.call_args[0][0]


def test_audit_obs_09_air_gapped_suffix_list_urls():
    """Verify AUDIT-OBS-09: AllowlistEngine and HomographDetector disable remote suffix list URL probes."""
    allowlist_engine = AllowlistEngine()
    homograph_detector = HomographDetector()

    # TLDExtract instance must have suffix_list_urls set to None / () to prevent outbound network queries
    assert allowlist_engine._extractor.suffix_list_urls in (None, ())
    assert homograph_detector._extractor.suffix_list_urls in (None, ())


@pytest.mark.asyncio
async def test_audit_obs_10_readiness_probe_active_pings(monkeypatch):
    """Verify AUDIT-OBS-10: /health/ready actively pings DB and Redis, returning 503 if any fails."""
    from httpx import ASGITransport, AsyncClient
    from hares.main import app
    import redis.asyncio as aioredis

    # 1. Nominal: Mock Redis ping to return True
    mock_redis = MagicMock()
    mock_redis.ping = AsyncMock(return_value=True) if hasattr(pytest, "AsyncMock") else None

    class FakeRedisClient:
        async def ping(self):
            return True
        async def aclose(self):
            pass

    monkeypatch.setattr(aioredis, "from_url", lambda *args, **kwargs: FakeRedisClient())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "ok"
        assert data["checks"]["redis"] == "ok"

    # 2. Redis Failure: Mock Redis ping to raise connection error
    class FailingRedisClient:
        async def ping(self):
            raise ConnectionError("Redis cluster connection refused")
        async def aclose(self):
            pass

    monkeypatch.setattr(aioredis, "from_url", lambda *args, **kwargs: FailingRedisClient())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        fail_resp = await client.get("/health/ready")
        assert fail_resp.status_code == 503
        fail_data = fail_resp.json()
        assert fail_data["status"] == "unhealthy"
        assert "error" in fail_data["checks"]["redis"]


def test_audit_obs_11_media_downloader_ssrf_validation():
    """Verify AUDIT-OBS-11: MediaDownloader strictly validates Meta CDN hostnames before downloading."""
    from hares.services.media_downloader import MediaDownloader

    # Valid Meta CDN URLs
    valid_urls = [
        "https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=123",
        "https://pps.whatsapp.net/v/t61.24694-24/sample.ogg",
        "https://cdn.fbcdn.net/v/sample.mp3",
        "https://media.facebook.com/download/audio.ogg",
    ]
    for url in valid_urls:
        # Must not raise
        MediaDownloader._validate_cdn_url(url)

    # Malicious or SSRF URLs
    invalid_urls = [
        "http://attacker-c2-server.com/malicious.ogg",
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost:8000/internal-admin",
        "ftp://fbsbx.com/evil.ogg",
        "https://fake-fbsbx.com.evil.com/audio.ogg",
    ]
    for url in invalid_urls:
        with pytest.raises(ValueError, match="SSRF Protection"):
            MediaDownloader._validate_cdn_url(url)


def test_audit_obs_13_phone_sanitizing_filter():
    """Verify AUDIT-OBS-13: PhoneSanitizingFilter globally scrubs telephone numbers from log output."""
    import io
    import logging
    from hares.core.logging import PhoneSanitizingFilter, redact_phone_numbers

    # 1. Direct text scrubber check
    text_with_phone = "Citizen +971501234567 submitted audio, alternative line 0551234567."
    scrubbed = redact_phone_numbers(text_with_phone)
    assert "+971501234567" not in scrubbed
    assert "0551234567" not in scrubbed
    assert "[REDACTED_PHONE]" in scrubbed

    # 2. Logging pipeline check
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.addFilter(PhoneSanitizingFilter())

    test_logger = logging.getLogger("test.phone.sanitizer")
    test_logger.setLevel(logging.INFO)
    test_logger.addHandler(handler)

    test_logger.info("Processing webhook for submitter phone: %s", "+971509988776")
    output = log_capture.getvalue()

    assert "+971509988776" not in output
    assert "[REDACTED_PHONE]" in output

