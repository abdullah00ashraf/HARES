import uuid
from decimal import Decimal
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from hares.db.models import Base
from hares.db.repositories.allowlist_repo import AllowlistRepository
from hares.db.repositories.audit_repo import AuditRepository
from hares.db.repositories.threat_repo import ThreatRepository


@pytest_asyncio.fixture
async def async_test_session():
    """Provides an isolated in-memory SQLite async session via aiosqlite."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sync_test_session():
    """Provides an isolated in-memory SQLite synchronous session."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    session_factory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
    with session_factory() as session:
        yield session

    engine.dispose()


@pytest.mark.asyncio
async def test_allowlist_repo_async(async_test_session: AsyncSession):
    """Verifies seeding and querying official domains asynchronously."""
    seeded_count = await AllowlistRepository.seed_default_domains_async(async_test_session)
    assert seeded_count > 0

    domains = await AllowlistRepository.get_active_domain_names_async(async_test_session)
    assert "ecrime.ae" in domains
    assert "dubaipolice.gov.ae" in domains
    assert "salik.ae" in domains

    record = await AllowlistRepository.get_domain_by_name_async(async_test_session, "salik.ae")
    assert record is not None
    assert record.entity_name == "Salik Toll System"


def test_allowlist_repo_sync(sync_test_session: Session):
    """Verifies seeding and querying official domains synchronously."""
    seeded_count = AllowlistRepository.seed_default_domains_sync(sync_test_session)
    assert seeded_count > 0

    domains = AllowlistRepository.get_active_domain_names_sync(sync_test_session)
    assert "ecrime.ae" in domains

    record = AllowlistRepository.get_domain_by_name_sync(sync_test_session, "ecrime.ae")
    assert record is not None
    assert record.entity_name == "Dubai Police e-Crime Portal"


@pytest.mark.asyncio
async def test_threat_repo_async(async_test_session: AsyncSession):
    """Verifies recording threat indicators and campaigns asynchronously."""
    campaign = await ThreatRepository.get_or_create_campaign_async(
        session=async_test_session,
        name="Dubai Police Traffic Phish Wave 1",
        lure_type="traffic_fine",
        target_entity_spoofed="Dubai Police",
    )
    assert campaign.id is not None
    assert campaign.total_submissions == 1

    indicator = await ThreatRepository.record_indicator_async(
        session=async_test_session,
        indicator_type="domain",
        raw_indicator="https://dubai-police.scam",
        normalized_value="dubai-police.scam",
        verdict="RED",
        risk_score=Decimal("0.9800"),
        campaign_id=campaign.id,
    )
    assert indicator.id is not None
    assert indicator.occurrence_count == 1

    # Record duplicate indicator to verify occurrence counter increment
    updated_indicator = await ThreatRepository.record_indicator_async(
        session=async_test_session,
        indicator_type="domain",
        raw_indicator="https://dubai-police.scam/pay",
        normalized_value="dubai-police.scam",
        verdict="RED",
        risk_score=Decimal("0.9800"),
    )
    assert updated_indicator.id == indicator.id
    assert updated_indicator.occurrence_count == 2


@pytest.mark.asyncio
async def test_audit_repo_async(async_test_session: AsyncSession):
    """Verifies persisting sanitized operational audit logs."""
    req_id = uuid.uuid4()
    audit_log = await AuditRepository.record_triage_audit_async(
        session=async_test_session,
        request_id=req_id,
        citizen_user_hash="a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
        payload_type="text",
        triage_verdict="RED",
        rule_triggered="punycode_homograph",
        latency_ms=25,
    )

    assert audit_log.id is not None
    assert audit_log.request_id == req_id
    assert audit_log.triage_verdict == "RED"
    assert audit_log.latency_ms == 25
