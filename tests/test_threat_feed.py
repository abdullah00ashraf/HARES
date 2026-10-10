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
    """Verifies rejection on missing or invalid API key."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Missing API Key -> 401
        resp_missing = await client.get("/api/v1/threats/overview")
        assert resp_missing.status_code == 401

        # 2. Invalid API Key -> 403
        resp_invalid = await client.get("/api/v1/threats/overview", headers={"X-API-Key": "invalid_analyst_key"})
        assert resp_invalid.status_code == 403

        # 3. Bearer Token Auth -> 200
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
