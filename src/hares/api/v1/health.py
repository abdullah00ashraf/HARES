from fastapi import APIRouter, status

router = APIRouter(prefix="/health")


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_probe() -> dict[str, str]:
    """Liveness probe verifying that the application process is running."""
    return {"status": "alive"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_probe() -> dict[str, str]:
    """Readiness probe verifying that the application is ready to accept traffic."""
    return {"status": "ready"}
