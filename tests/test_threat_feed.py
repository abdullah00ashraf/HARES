import json
import pytest
from httpx import ASGITransport, AsyncClient
from hares.core.config import get_settings
from hares.main import app

import pytest_asyncio
from hares.db.models import Base
from hares.db.session import async_engine

settings = get_settings()
AUTH_HEADERS = {"X-API-Key": settings.ANALYST_API_KEY}


@pytest_asyncio.fixture(autouse=True)
async def setup_threat_db():
    """Ensures database tables exist on async_engine before tests execute."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_threat_overview_endpoint():
    """Verifies that the /overview endpoint returns 24h KPIs, curves, and distributions."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/threats/overview", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "success"
        assert "kpis" in data
        assert "temporal_curve" in data
        assert "impersonation_distribution" in data

        kpis = data["kpis"]
        assert "total_scanned_24h" in kpis
        assert "high_risk_verdicts_24h" in kpis
        assert "amber_fallbacks_24h" in kpis
        assert "avg_latency_ms" in kpis
        assert kpis["total_scanned_24h"] > 0

        # Verify temporal curve structure (24 buckets)
        curve = data["temporal_curve"]
        assert len(curve) == 24
        assert "time" in curve[0]
        assert "text_volume" in curve[0]

        # Verify impersonation distribution
        dist = data["impersonation_distribution"]
        assert len(dist) >= 4
        entities = [d["entity"] for d in dist]
        assert "Dubai Police" in entities


@pytest.mark.asyncio
async def test_threat_campaigns_endpoint():
    """Verifies campaigns list and campaign drill-down endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/threats/campaigns", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        campaigns = resp.json()

        assert len(campaigns) > 0
        first_c = campaigns[0]
        assert "id" in first_c
        assert "name" in first_c
        assert "lure_type" in first_c
        assert "target_entity_spoofed" in first_c
        assert first_c["status"] in ("active", "monitoring", "disrupted")

        # Test drill-down drawer endpoint
        c_id = first_c["id"]
        detail_resp = await client.get(f"/api/v1/threats/campaigns/{c_id}", headers=AUTH_HEADERS)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["id"] == c_id
        assert "indicators" in detail


@pytest.mark.asyncio
async def test_threat_indicators_endpoint_and_filters():
    """Verifies paginated Class A indicators with search and type filters."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Default listing
        resp = await client.get("/api/v1/threats/indicators", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "indicators" in data
        assert data["total"] > 0

        # Filter by indicator_type=url
        url_resp = await client.get("/api/v1/threats/indicators?indicator_type=url", headers=AUTH_HEADERS)
        assert url_resp.status_code == 200
        url_data = url_resp.json()
        for ind in url_data["indicators"]:
            assert ind["indicator_type"] == "url"

        # Filter by verdict=RED
        red_resp = await client.get("/api/v1/threats/indicators?verdict=RED", headers=AUTH_HEADERS)
        assert red_resp.status_code == 200
        red_data = red_resp.json()
        for ind in red_data["indicators"]:
            assert ind["verdict"] == "RED"


@pytest.mark.asyncio
async def test_homographs_and_isp_block():
    """Verifies homograph lookalike radar and ISP block trigger."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/threats/homographs", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        homographs = resp.json()
        assert isinstance(homographs, list)

        if homographs:
            target_id = homographs[0]["id"]
            block_resp = await client.post(
                f"/api/v1/threats/homographs/{target_id}/isp-block",
                headers=AUTH_HEADERS,
            )
            assert block_resp.status_code == 200
            block_data = block_resp.json()
            assert block_data["status"] == "submitted"
            assert "reference_id" in block_data
            assert block_data["reference_id"].startswith("TDRA-BLOCK-")


@pytest.mark.asyncio
async def test_export_stix_bundle():
    """Verifies STIX 2.1 JSON bundle serialization."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/threats/export/stix", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/json"
        assert "hares_stix21_feed.json" in resp.headers.get("content-disposition", "")

        bundle = resp.json()
        assert bundle["type"] == "bundle"
        assert bundle["spec_version"] == "2.1"
        assert "objects" in bundle
        assert len(bundle["objects"]) > 0

        first_obj = bundle["objects"][0]
        assert first_obj["type"] == "indicator"
        assert "pattern" in first_obj
        assert first_obj["pattern_type"] == "stix"
        assert "malicious-activity" in first_obj["indicator_types"]


@pytest.mark.asyncio
async def test_export_csv_feed():
    """Verifies CSV feed formatting and column headers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/threats/export/csv", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "hares_threat_indicators.csv" in resp.headers.get("content-disposition", "")

        csv_text = resp.text
        lines = csv_text.strip().split("\r\n") if "\r\n" in csv_text else csv_text.strip().split("\n")
        header = lines[0].split(",")
        assert "normalized_value" in header
        assert "indicator_type" in header
        assert "verdict" in header
        assert "risk_score" in header
        assert len(lines) > 1  # Has indicator rows


@pytest.mark.asyncio
async def test_threat_feed_authentication_enforcement():
    """Verifies public read telemetry access and strict authentication on mutating/sensitive endpoints (Milestone 52)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Missing API Key on protected mutating/sensitive endpoints -> 401
        resp_post_missing = await client.post("/api/v1/threats/indicators", json={"indicator_type": "url", "raw_indicator": "http://evil.com"})
        assert resp_post_missing.status_code == 401

        resp_stix_missing = await client.get("/api/v1/threats/export/stix")
        assert resp_stix_missing.status_code == 401

        # 2. Public Read Telemetry without API key -> 200 (Zero citizen PII, Class A only)
        resp_public_overview = await client.get("/api/v1/threats/overview")
        assert resp_public_overview.status_code == 200

        # 3. Invalid API Key on read endpoint -> 403 (optional_analyst_key validates when provided)
        resp_invalid = await client.get("/api/v1/threats/overview", headers={"X-API-Key": "invalid_analyst_key"})
        assert resp_invalid.status_code == 403

        # 4. Bearer Token Auth -> 200
        resp_bearer = await client.get(
            "/api/v1/threats/overview",
            headers={"Authorization": f"Bearer {settings.ANALYST_API_KEY}"},
        )
        assert resp_bearer.status_code == 200


@pytest.mark.asyncio
async def test_zero_class_b_pii_leakage():
    """
    CRITICAL COMPLIANCE TEST (FR-4.1, FR-4.3):
    Verifies that municipal threat feed endpoints contain ZERO citizen identifiers,
    zero raw phone numbers, and zero citizen HMAC hashes.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        endpoints = [
            "/api/v1/threats/overview",
            "/api/v1/threats/campaigns",
            "/api/v1/threats/indicators",
            "/api/v1/threats/homographs",
            "/api/v1/threats/export/stix",
            "/api/v1/threats/export/csv",
        ]

        for ep in endpoints:
            resp = await client.get(ep, headers=AUTH_HEADERS)
            assert resp.status_code == 200
            text = resp.text.lower()
            assert "citizen_user_hash" not in text
            assert "recipient_phone" not in text
            assert "raw_sender_phone" not in text
            assert "citizen_hash" not in text


@pytest.mark.asyncio
async def test_live_telemetry_feed_endpoint():
    """Verifies that /api/v1/threats/telemetry returns structured audit events with zero citizen PII."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/threats/telemetry?limit=20", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        events = resp.json()
        assert isinstance(events, list)
        assert len(events) >= 1
        first_evt = events[0]
        assert "id" in first_evt
        assert "timestamp" in first_evt
        assert "payload_type" in first_evt
        assert "verdict" in first_evt
        assert first_evt["verdict"] in ("RED", "AMBER", "GREEN")
        assert "latency_ms" in first_evt


@pytest.mark.asyncio
async def test_model_and_system_metrics_endpoint():
    """Verifies that /api/v1/threats/model-metrics exposes SLM, conformal, and database sync state."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/threats/model-metrics", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()

        assert "database_sync" in data
        assert data["database_sync"]["status"] == "synchronized_healthy"
        assert "total_triage_audit_records" in data["database_sync"]
        assert "slm_inference" in data
        assert data["slm_inference"]["parameters_count"] == 3085938688
        assert "acoustic_deepfake" in data
        assert data["acoustic_deepfake"]["conformal_calibration"]["conformal_threshold"] == 0.85
        assert "deterministic_radar" in data
        assert "audit_distribution" in data


@pytest.mark.asyncio
async def test_create_threat_indicator_post():
    """Verifies analysts can register indicators directly and correlate them with campaigns."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a new test indicator
        payload = {
            "indicator_type": "url",
            "raw_indicator": "https://fake-police-fine-dubai.xyz/pay",
            "verdict": "RED",
            "risk_score": 0.99,
        }
        resp = await client.post("/api/v1/threats/indicators", json=payload, headers=AUTH_HEADERS)
        assert resp.status_code == 201
        created = resp.json()
        assert created["normalized_value"] == "https://fake-police-fine-dubai.xyz/pay"
        assert created["verdict"] == "RED"
        assert created["risk_score"] == 0.99
        # Auto-correlated with Dubai Police campaign
        assert created["campaign_id"] is not None


@pytest.mark.asyncio
async def test_database_sync_with_triage_entry():
    """
    CRITICAL END-TO-END INVARIANT TEST:
    Verifies that when a citizen or analyst submits content to /api/v1/triage/verify,
    the database accurately syncs and updates both TriageAuditLog and ThreatIndicator tables!
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Check pre-triage audit count
        metrics_pre = (await client.get("/api/v1/threats/model-metrics", headers=AUTH_HEADERS)).json()
        pre_audits = metrics_pre["database_sync"]["total_triage_audit_records"]

        # 2. Perform a malicious URL triage
        triage_resp = await client.post(
            "/api/v1/triage/verify",
            data={"url": "http://salik-toll-recharge-steal.com/recharge"},
        )
        assert triage_resp.status_code == 200
        triage_data = triage_resp.json()
        assert triage_data["verdict"] == "RED"

        # 3. Check post-triage audit count and verify database sync
        metrics_post = (await client.get("/api/v1/threats/model-metrics", headers=AUTH_HEADERS)).json()
        post_audits = metrics_post["database_sync"]["total_triage_audit_records"]
        assert post_audits == pre_audits + 1

        # 4. Verify telemetry feed now includes the new entry
        telemetry_resp = await client.get("/api/v1/threats/telemetry?limit=5", headers=AUTH_HEADERS)
        assert telemetry_resp.status_code == 200
        events = telemetry_resp.json()
        assert len(events) >= 1
        # The latest event should match the triaged payload type and verdict
        first_event = events[0]
        assert first_event["payload_type"] == "url"
        assert first_event["verdict"] == "RED"

