import pytest
from httpx import ASGITransport, AsyncClient
from hares.main import app
from hares.core.metrics import (
    record_ingress_latency,
    record_e2e_latency,
    record_verdict,
    record_queue_depth,
    record_rate_limit_rejection,
    record_conformal_p_value,
    export_prometheus_metrics,
)


def test_metrics_collection_functions():
    """Validates that custom Prometheus metrics recording functions execute cleanly."""
    record_ingress_latency(0.015)
    record_e2e_latency("text", "RED", 0.75)
    record_e2e_latency("audio", "GREEN", 2.45)
    record_verdict("RED", "synthetic_voice_clone")
    record_queue_depth("high_priority_triage", 5)
    record_rate_limit_rejection("citizen")
    record_conformal_p_value(0.0015)

    data, content_type = export_prometheus_metrics()
    text = data.decode("utf-8")

    assert "hares_webhook_ingress_latency_seconds" in text
    assert "hares_triage_e2e_latency_seconds" in text
    assert "hares_triage_verdicts_total" in text
    assert "hares_queue_depth" in text
    assert "hares_rate_limit_rejections_total" in text
    assert "hares_conformal_p_values" in text


@pytest.mark.asyncio
async def test_get_metrics_http_endpoint():
    """Validates that GET /metrics exposes Prometheus telemetry."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers.get("content-type", "") or "openmetrics" in resp.headers.get("content-type", "")
        content = resp.text
        assert "hares_webhook_ingress_latency_seconds" in content
