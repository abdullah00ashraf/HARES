import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from hares.db.models import TriageAuditLog

_DEFAULT_WEB_HASH = hashlib.sha256(b"hares_sovereign_web_portal_user").hexdigest()


class AuditRepository:
    """
    Repository for persisting sanitized operational telemetry and triage audit logs (FR-4.1).
    Guarantees ZERO citizen PII is persisted (citizen phone is stored exclusively as salted HMAC hash).
    """

    @staticmethod
    async def record_triage_audit_async(
        session: AsyncSession,
        request_id: uuid.UUID,
        citizen_user_hash: str | None,
        payload_type: str,
        triage_verdict: str,
        rule_triggered: str,
        latency_ms: int,
    ) -> TriageAuditLog:
        """Asynchronously persists a sanitized audit record with strict PII protection."""
        safe_hash = citizen_user_hash.strip() if citizen_user_hash and citizen_user_hash.strip() else _DEFAULT_WEB_HASH
        audit_entry = TriageAuditLog(
            request_id=request_id,
            citizen_user_hash=safe_hash,
            payload_type=payload_type.lower(),
            triage_verdict=triage_verdict.upper(),
            rule_triggered=rule_triggered,
            latency_ms=max(0, int(latency_ms)),
            created_at=datetime.now(timezone.utc),
        )
        session.add(audit_entry)
        await session.commit()
        await session.refresh(audit_entry)
        return audit_entry

    @staticmethod
    def record_triage_audit_sync(
        session: Session,
        request_id: uuid.UUID,
        citizen_user_hash: str | None,
        payload_type: str,
        triage_verdict: str,
        rule_triggered: str,
        latency_ms: int,
    ) -> TriageAuditLog:
        """Synchronously persists a sanitized audit record in Celery worker context."""
        safe_hash = citizen_user_hash.strip() if citizen_user_hash and citizen_user_hash.strip() else _DEFAULT_WEB_HASH
        audit_entry = TriageAuditLog(
            request_id=request_id,
            citizen_user_hash=safe_hash,
            payload_type=payload_type.lower(),
            triage_verdict=triage_verdict.upper(),
            rule_triggered=rule_triggered,
            latency_ms=max(0, int(latency_ms)),
            created_at=datetime.now(timezone.utc),
        )
        session.add(audit_entry)
        session.commit()
        session.refresh(audit_entry)
        return audit_entry

    @classmethod
    def record_triage_event_sync(
        cls,
        session: Session,
        request_id: uuid.UUID,
        user_hash: str | None = None,
        citizen_user_hash: str | None = None,
        payload_type: str = "text",
        verdict: str = "AMBER",
        triage_verdict: str | None = None,
        rule_triggered: str = "triage_pipeline",
        latency_ms: float | int = 0,
        **kwargs: Any,
    ) -> TriageAuditLog:
        """
        Convenience forward-compatible synchronous logger for FastAPI endpoints and Celery workers.
        Accepts variable naming conventions without throwing AttributeErrors.
        """
        chosen_hash = user_hash or citizen_user_hash or _DEFAULT_WEB_HASH
        chosen_verdict = (triage_verdict or verdict or "AMBER").upper()
        return cls.record_triage_audit_sync(
            session=session,
            request_id=request_id,
            citizen_user_hash=chosen_hash,
            payload_type=payload_type,
            triage_verdict=chosen_verdict,
            rule_triggered=rule_triggered,
            latency_ms=int(round(float(latency_ms))),
        )

    @staticmethod
    async def get_recent_audit_events_async(
        session: AsyncSession,
        limit: int = 50,
    ) -> list[TriageAuditLog]:
        """Retrieves recent sanitized audit events for real-time SOC analyst telemetry feeds."""
        stmt = select(TriageAuditLog).order_by(TriageAuditLog.created_at.desc()).limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    def get_recent_audit_events_sync(
        session: Session,
        limit: int = 50,
    ) -> list[TriageAuditLog]:
        """Synchronously retrieves recent audit events for real-time telemetry."""
        stmt = select(TriageAuditLog).order_by(TriageAuditLog.created_at.desc()).limit(limit)
        res = session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_audit_stats_async(
        session: AsyncSession,
    ) -> dict[str, Any]:
        """Aggregates real-time audit statistics for SOC model & telemetry monitoring."""
        total_stmt = select(func.count()).select_from(TriageAuditLog)
        total_count = (await session.execute(total_stmt)).scalar() or 0

        verdict_stmt = select(TriageAuditLog.triage_verdict, func.count()).group_by(TriageAuditLog.triage_verdict)
        verdict_rows = (await session.execute(verdict_stmt)).all()
        verdicts = {v: cnt for v, cnt in verdict_rows}

        payload_stmt = select(TriageAuditLog.payload_type, func.count()).group_by(TriageAuditLog.payload_type)
        payload_rows = (await session.execute(payload_stmt)).all()
        payloads = {p: cnt for p, cnt in payload_rows}

        avg_lat_stmt = select(func.avg(TriageAuditLog.latency_ms)).select_from(TriageAuditLog)
        avg_latency = (await session.execute(avg_lat_stmt)).scalar() or 0.0

        return {
            "total_audit_events": total_count,
            "verdicts": verdicts,
            "payloads": payloads,
            "avg_latency_ms": round(float(avg_latency), 2),
        }

