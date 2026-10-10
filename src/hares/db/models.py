import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base class for Project Hares persistence models."""
    pass


class OfficialDomain(Base):
    """
    Curated Registrable Domain Exact Allowlist (FR-2.2).
    Stores verified UAE public-sector, municipal, utility, and banking domains.
    """
    __tablename__ = "official_domains"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # government, utility, banking, telecom
    verified_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    quarterly_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ThreatCampaign(Base):
    """
    Aggregated Threat Clusters for Municipal Analysts (FR-4.3).
    Clusters related scam templates, targeted entities, and active campaigns.
    """
    __tablename__ = "threat_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lure_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # traffic_fine, courier, banking
    target_entity_spoofed: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)
    total_submissions: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    indicators: Mapped[list["ThreatIndicator"]] = relationship("ThreatIndicator", back_populates="campaign")


class ThreatIndicator(Base):
    """
    Class A Indicators of Compromise (FR-4.1).
    Persisted indefinitely in PostgreSQL for municipal SOC and threat intelligence harvesting.
    """
    __tablename__ = "threat_indicators"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("threat_campaigns.id", ondelete="SET NULL"), nullable=True
    )
    indicator_type: Mapped[str] = mapped_column(String(50), nullable=False)  # url, domain, phone, bank_account, crypto_wallet
    raw_indicator: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    verdict: Mapped[str] = mapped_column(String(20), nullable=False)  # RED, AMBER
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    campaign: Mapped[ThreatCampaign | None] = relationship("ThreatCampaign", back_populates="indicators")


class TriageAuditLog(Base):
    """
    Sanitized Operational Telemetry & Performance Audit Log (FR-4.1, NFR-1.3).
    Contains ZERO citizen PII. Submitter phone is pseudonymized via keyed HMAC-SHA256.
    """
    __tablename__ = "triage_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    citizen_user_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_type: Mapped[str] = mapped_column(String(20), nullable=False)  # text, url, audio_voice_note
    triage_verdict: Mapped[str] = mapped_column(String(20), nullable=False)  # RED, AMBER, GREEN
    rule_triggered: Mapped[str] = mapped_column(String(100), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
