from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, Response
from hares.core.config import get_settings
from hares.api.v1.webhook import router as webhook_router
from hares.api.v1.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for resource initialization and teardown."""
    # Startup sequence
    yield
    # Teardown sequence


def create_app() -> FastAPI:
    """Application factory configuring routers, security headers, and middleware."""
    settings = get_settings()
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        lifespan=lifespan,
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

    return application


app = create_app()
