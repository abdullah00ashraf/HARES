import hashlib
import hmac
from unittest.mock import patch
import pytest
from httpx import ASGITransport, AsyncClient
from hares.main import app
from hares.core.config import get_settings


@pytest.mark.asyncio
async def test_webhook_challenge_success():
    """Tests Meta verification handshake when token matches."""
    settings = get_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            f"/webhook?hub.mode=subscribe&hub.verify_token={settings.WHATSAPP_VERIFY_TOKEN}&hub.challenge=115325704"
        )
        assert resp.status_code == 200
        assert resp.text == "115325704"


@pytest.mark.asyncio
async def test_webhook_challenge_forbidden():
    """Tests Meta verification handshake rejection on mismatched token."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/webhook?hub.mode=subscribe&hub.verify_token=wrong_token&hub.challenge=123")
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_webhook_post_rejected_bad_signature():
    """Tests POST payload rejection when signature does not match."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/webhook",
            json={"entry": []},
            headers={"X-Hub-Signature-256": "sha256=invalid0000000000000000000000000000000000000000000000000000000000"},
        )
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_webhook_post_success_mocked():
    """Tests cryptographically valid webhook POST ingestion into high_priority_triage queue."""
    settings = get_settings()
    payload = b'{"object": "whatsapp_business_account", "entry": []}'
    signature = hmac.new(
        settings.WHATSAPP_APP_SECRET.encode(), payload, hashlib.sha256
    ).hexdigest()

    transport = ASGITransport(app=app)
    with patch("hares.api.v1.webhook.process_incoming_webhook.apply_async") as mock_task:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/webhook",
                content=payload,
                headers={
                    "X-Hub-Signature-256": f"sha256={signature}",
                    "Content-Type": "application/json",
                },
            )
            assert resp.status_code == 200
            assert resp.json() == {"status": "queued"}
            mock_task.assert_called_once()
            call_kwargs = mock_task.call_args.kwargs
            assert call_kwargs.get("queue") == "high_priority_triage"
            assert call_kwargs.get("expires") == settings.REDIS_EPHEMERAL_PAYLOAD_TTL_SECONDS


@pytest.mark.asyncio
async def test_health_probes():
    """Tests liveness and readiness endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        live_resp = await client.get("/health/live")
        assert live_resp.status_code == 200
        assert live_resp.json() == {"status": "alive"}

        ready_resp = await client.get("/health/ready")
        assert ready_resp.status_code == 200
        assert ready_resp.json() == {"status": "ready"}
