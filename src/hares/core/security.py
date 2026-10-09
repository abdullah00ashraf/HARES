import hashlib
import hmac
import re

E164_CLEAN_PATTERN = re.compile(r"[\s\-\(\)\+]")


def verify_meta_signature(payload_bytes: bytes, signature_header: str, app_secret: str) -> bool:
    """
    Validates Meta X-Hub-Signature-256 header using constant-time comparison.
    Signature format: 'sha256=<hex_digest>'
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False

    signature_hash = signature_header.removeprefix("sha256=").strip()
    expected_hash = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=payload_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_hash, signature_hash)


def derive_citizen_user_hash(raw_phone_number: str, salt: str) -> str:
    """
    Derives an anonymized, deterministic citizen user hash for rate limiting and deduplication (FR-4.1).
    Normalizes E.164 phone string and applies keyed HMAC-SHA256.
    """
    normalized_phone = E164_CLEAN_PATTERN.sub("", raw_phone_number).strip()
    return hmac.new(
        key=salt.encode("utf-8"),
        msg=normalized_phone.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
