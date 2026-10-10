import logging
from typing import Any
from fastapi import APIRouter, Response, status
from sqlalchemy import text
from hares.core.config import get_settings
from hares.db.session import async_session_scope

logger = logging.getLogger("hares.api.health")
router = APIRouter(prefix="/health")


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_probe() -> dict[str, str]:
    """Liveness probe verifying that the application process is running."""
    return {"status": "alive"}


@router.get("/ready")
async def readiness_probe(response: Response) -> dict[str, Any]:
    """
    Active readiness probe verifying database and cache connectivity (AUDIT-OBS-10).
    Executes SELECT 1 on PostgreSQL and PING on Redis. Returns HTTP 503 if any dependency fails.
    """
    settings = get_settings()
    checks: dict[str, str] = {
        "database": "unknown",
        "redis": "unknown",
    }
    all_healthy = True

    # 1. Database Ping
    try:
        async with async_session_scope() as session:
            res = await session.execute(text("SELECT 1"))
            if res.scalar() == 1:
                checks["database"] = "ok"
            else:
                checks["database"] = "unexpected_response"
                all_healthy = False
    except Exception as exc:
        logger.warning("Database readiness check failed: %s", str(exc))
        checks["database"] = f"error: {str(exc)}"
        all_healthy = False

    # 2. Redis Ping
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=1.5,
        )
        pong = await client.ping()
        await client.aclose()
        if pong:
            checks["redis"] = "ok"
        else:
            checks["redis"] = "failed"
            all_healthy = False
    except Exception as exc:
        logger.warning("Redis readiness check failed: %s", str(exc))
        checks["redis"] = f"error: {str(exc)}"
        all_healthy = False

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", "checks": checks}

    response.status_code = status.HTTP_200_OK
    return {"status": "ready", "checks": checks}
