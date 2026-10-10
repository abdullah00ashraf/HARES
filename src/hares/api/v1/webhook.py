from fastapi import APIRouter, Header, HTTPException, Query, Request, Response, status
from hares.core.config import get_settings
from hares.core.security import verify_meta_signature
from hares.workers.tasks import process_incoming_webhook

router = APIRouter()


@router.get("/webhook")
async def verify_webhook_challenge(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
) -> Response:
    """
    Handles Meta WhatsApp webhook verification handshake.
    Returns integer hub.challenge on token match.
    """
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain", status_code=status.HTTP_200_OK)
    return Response(content="Forbidden", status_code=status.HTTP_403_FORBIDDEN)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def receive_webhook_payload(
    request: Request,
    x_hub_signature_256: str = Header(..., alias="X-Hub-Signature-256"),
) -> dict[str, str]:
    """
    WhatsApp Ingestion Webhook fulfilling sub-50ms SLA (FR-3.3):
    1. Validates HMAC-SHA256 signature in constant time.
    2. Enqueues payload into Celery with broker-level message TTL=60s (FR-4.1).
    3. Emits HTTP 200 acknowledgment in <50ms.
    """
    settings = get_settings()
    payload_bytes = await request.body()

    # 1. Cryptographic Signature Validation
    if not verify_meta_signature(payload_bytes, x_hub_signature_256, settings.WHATSAPP_APP_SECRET):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid payload signature")

    # 2. Broker-Level Ephemeral Queue Dispatch (FR-3.3 & FR-4.1)
    try:
        raw_payload = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed JSON payload",
        ) from exc

    process_incoming_webhook.apply_async(
        args=[raw_payload],
        queue="high_priority_triage",
        expires=settings.REDIS_EPHEMERAL_PAYLOAD_TTL_SECONDS,
    )

    # 3. Sub-50ms Response Acknowledgment
    return {"status": "queued"}
