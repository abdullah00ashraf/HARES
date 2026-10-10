from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from hares.core.config import get_settings
from hares.core.logging import configure_logging
from hares.api.v1.webhook import router as webhook_router
from hares.api.v1.health import router as health_router
from hares.api.v1.threat_feed import router as threat_feed_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for resource initialization and teardown."""
    settings = get_settings()
    configure_logging(level=settings.LOG_LEVEL)

    # Initialize in-memory SQLite schema in local/testing environment
    if "sqlite" in settings.DATABASE_URL:
        from hares.db.models import Base
        from hares.db.session import async_engine
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield


def create_app() -> FastAPI:
    """Application factory configuring routers, security headers, and middleware."""
    settings = get_settings()
    configure_logging(level=settings.LOG_LEVEL)

    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS Middleware for Internal Municipal Analyst Dashboard
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Enterprise Security Headers Middleware (NFR-1.3)
    @application.middleware("http")
    async def security_headers_middleware(request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none';"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    # Master Routers
    application.include_router(health_router, tags=["Health"])
    application.include_router(webhook_router, tags=["WhatsApp Webhook"])
    application.include_router(threat_feed_router, prefix="/api/v1", tags=["Municipal Threat Intelligence"])

    # Prometheus Metrics Endpoint (Phase 6 Observability)
    @application.get("/metrics", tags=["Observability"])
    async def prometheus_metrics() -> Response:
        """Exposes Prometheus/OpenMetrics formatted telemetry for scraper daemons."""
        from hares.core.metrics import export_prometheus_metrics

        content, content_type = export_prometheus_metrics()
        return Response(content=content, media_type=content_type)

    return application



app = create_app()
