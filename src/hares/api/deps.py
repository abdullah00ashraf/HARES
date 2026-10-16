import secrets
from typing import Annotated
from fastapi import Header, HTTPException, status
from hares.core.config import get_settings


async def verify_analyst_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> str:
    """
    Dependency verifying municipal cyber analyst authentication for Threat Feed APIs (FR-4.3).
    Accepts API key via 'X-API-Key' or 'Authorization: Bearer <token>'.
    Uses constant-time comparison against configured ANALYST_API_KEY.
    """
    settings = get_settings()
    candidate_key: str | None = None

    if x_api_key and x_api_key.strip():
        candidate_key = x_api_key.strip()
    elif authorization and authorization.strip():
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            candidate_key = parts[1]
        else:
            candidate_key = parts[0]

    if not candidate_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Municipal Analyst API Key required. Supply via 'X-API-Key' or 'Authorization: Bearer <key>'.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Constant-time comparison to prevent timing side-channel attacks
    # Authenticates against ANALYST_API_KEY or salted PBKDF2 master passkey hash (NFR-1.3)
    from hares.core.security import verify_passkey_pbkdf2

    is_analyst_key = secrets.compare_digest(candidate_key, settings.ANALYST_API_KEY)
    is_admin_passkey = verify_passkey_pbkdf2(
        candidate_key, settings.SOC_ADMIN_SALT_HEX, settings.SOC_ADMIN_PASSWORD_HASH
    )
    is_admin_override = (
        secrets.compare_digest(candidate_key, settings.SOC_ADMIN_PASSWORD)
        if settings.SOC_ADMIN_PASSWORD
        else False
    )
    if not (is_analyst_key or is_admin_passkey or is_admin_override):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Municipal Analyst API Key. Access denied.",
        )

    # AUDIT-OBS-14: Enforce token-bucket rate limiting per analyst key
    import hashlib
    from hares.services.rate_limiter import RedisTokenBucketRateLimiter

    limiter = RedisTokenBucketRateLimiter()
    key_hash = hashlib.sha256(candidate_key.encode("utf-8")).hexdigest()[:16]
    rl_result = limiter.check_analyst_rate_limit(key_hash, max_requests=settings.ANALYST_RATE_LIMIT_PER_MINUTE)
    if not rl_result.is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Municipal Analyst API rate limit exceeded ({rl_result.max_allowed} requests/minute). Please throttle requests.",
            headers={"Retry-After": str(rl_result.reset_seconds)},
        )

    return candidate_key


async def optional_analyst_key(
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> str | None:
    """
    Optional dependency for public-read threat feed telemetry endpoints (FR-4.3, Milestone 52).
    Permits unauthenticated read-only access (Class A indicators with zero citizen PII).
    If an API key or bearer token IS supplied, enforces strict constant-time validation
    and AUDIT-OBS-14 token-bucket rate limiting (rejecting invalid keys with HTTP 403).
    """
    candidate_key: str | None = None
    if x_api_key and x_api_key.strip():
        candidate_key = x_api_key.strip()
    elif authorization and authorization.strip():
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            candidate_key = parts[1]
        else:
            candidate_key = parts[0]

    if not candidate_key:
        return None

    settings = get_settings()
    from hares.core.security import verify_passkey_pbkdf2

    is_analyst_key = secrets.compare_digest(candidate_key, settings.ANALYST_API_KEY)
    is_admin_passkey = verify_passkey_pbkdf2(
        candidate_key, settings.SOC_ADMIN_SALT_HEX, settings.SOC_ADMIN_PASSWORD_HASH
    )
    is_admin_override = (
        secrets.compare_digest(candidate_key, settings.SOC_ADMIN_PASSWORD)
        if settings.SOC_ADMIN_PASSWORD
        else False
    )
    if not (is_analyst_key or is_admin_passkey or is_admin_override):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Municipal Analyst API Key. Access denied.",
        )

    # AUDIT-OBS-14: Enforce token-bucket rate limiting per analyst key
    import hashlib
    from hares.services.rate_limiter import RedisTokenBucketRateLimiter

    limiter = RedisTokenBucketRateLimiter()
    key_hash = hashlib.sha256(candidate_key.encode("utf-8")).hexdigest()[:16]
    rl_result = limiter.check_analyst_rate_limit(key_hash, max_requests=settings.ANALYST_RATE_LIMIT_PER_MINUTE)
    if not rl_result.is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Municipal Analyst API rate limit exceeded ({rl_result.max_allowed} requests/minute). Please throttle requests.",
            headers={"Retry-After": str(rl_result.reset_seconds)},
        )

    return candidate_key

