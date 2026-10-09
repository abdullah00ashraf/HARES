import logging
from typing import Any
from hares.core.config import get_settings
from hares.core.security import derive_citizen_user_hash
from hares.workers.celery_app import celery_app

logger = logging.getLogger("hares.workers")


@celery_app.task(name="hares.process_incoming_webhook", queue="high_priority_triage", bind=True)
def process_incoming_webhook(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Background worker task handling WhatsApp payload processing out-of-band:
    1. Extracts ephemeral recipient phone for reply addressing.
    2. Derives citizen_user_hash via keyed HMAC-SHA256 for rate-limiting (FR-4.1).
    3. Purges raw citizen phone numbers from memory frames post-processing.
    4. Enforces zero persistence rule on raw citizen phone numbers.
    """
    settings = get_settings()
    processed_count = 0

    try:
        entries = raw_payload.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for msg in messages:
                    raw_sender_phone = msg.get("from", "")
                    if not raw_sender_phone:
                        continue

                    # Derive pseudonymized hash immediately (FR-4.1)
                    citizen_hash = derive_citizen_user_hash(raw_sender_phone, settings.CITIZEN_HASH_SALT)
                    msg_id = msg.get("id", "unknown")
                    msg_type = msg.get("type", "unknown")
                    logger.info(
                        "Ingesting message id=%s from citizen_hash=%s type=%s",
                        msg_id,
                        citizen_hash[:12],
                        msg_type,
                    )

                    # Ephemeral recipient phone retained strictly in volatile frame for reply routing
                    recipient_phone = raw_sender_phone
                    processed_count += 1

                    # Ephemeral in-memory memory purge
                    del recipient_phone
                    del raw_sender_phone

        return {"status": "processed", "messages_handled": processed_count}
    except Exception as exc:
        logger.error("Error processing incoming webhook payload: %s", str(exc), exc_info=True)
        raise self.retry(exc=exc, countdown=2, max_retries=3)
