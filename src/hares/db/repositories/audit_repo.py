import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from hares.db.models import TriageAuditLog


class AuditRepository:
    """
    Repository for persisting sanitized operational telemetry and triage audit logs (FR-4.1).
    Guarantees ZERO citizen PII is persisted (citizen phone is stored exclusively as salted HMAC hash).
    """

    @staticmethod
    async def record_triage_audit_async(
        session: AsyncSession,
        request_id: uuid.UUID,
        citizen_user_hash: str,
        payload_type: str,
        triage_verdict: str,
        rule_triggered: str,
        latency_ms: int,
    ) -> TriageAuditLog:
        """Asynchronously persists a sanitized audit record."""
        audit_entry = TriageAuditLog(
            request_id=request_id,
            citizen_user_hash=citizen_user_hash,
            payload_type=payload_type.lower(),
            triage_verdict=triage_verdict.upper(),
            rule_triggered=rule_triggered,
            latency_ms=max(0, latency_ms),
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
        citizen_user_hash: str,
        payload_type: str,
        triage_verdict: str,
        rule_triggered: str,
        latency_ms: int,
    ) -> TriageAuditLog:
        """Synchronously persists a sanitized audit record in Celery worker context."""
        audit_entry = TriageAuditLog(
            request_id=request_id,
            citizen_user_hash=citizen_user_hash,
            payload_type=payload_type.lower(),
            triage_verdict=triage_verdict.upper(),
            rule_triggered=rule_triggered,
            latency_ms=max(0, latency_ms),
            created_at=datetime.now(timezone.utc),
        )
        session.add(audit_entry)
        session.commit()
        session.refresh(audit_entry)
        return audit_entry
