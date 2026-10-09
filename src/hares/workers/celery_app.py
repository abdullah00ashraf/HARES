from celery import Celery
from hares.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "hares_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=30,
    result_expires=settings.REDIS_EPHEMERAL_PAYLOAD_TTL_SECONDS,
    task_default_queue="high_priority_triage",
    task_routes={
        "hares.process_incoming_webhook": {"queue": "high_priority_triage"},
    },
)
