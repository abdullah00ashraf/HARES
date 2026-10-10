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
    is_valid = secrets.compare_digest(candidate_key, settings.ANALYST_API_KEY)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Municipal Analyst API Key. Access denied.",
        )

    return candidate_key
