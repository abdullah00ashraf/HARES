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


# =========================================================================
# Cryptographic STIX 2.1 CTI Signing & Non-Repudiation (AUDIT-OBS-16)
# =========================================================================
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

_STIX_SIGNING_KEY: ec.EllipticCurvePrivateKey | None = None


def get_stix_signing_key() -> ec.EllipticCurvePrivateKey:
    """Retrieves or lazily generates the sovereign municipal ECDSA SECP256R1 signing key."""
    global _STIX_SIGNING_KEY
    if _STIX_SIGNING_KEY is None:
        _STIX_SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
    return _STIX_SIGNING_KEY


def sign_stix_bundle(bundle_json_str: str, private_key: ec.EllipticCurvePrivateKey | None = None) -> str:
    """
    Signs a serialized STIX 2.1 JSON bundle using ECDSA SECP256R1 + SHA256 (AUDIT-OBS-16).
    Returns Base64-encoded ASN.1 DER signature for the X-Hares-Bundle-Signature header.
    """
    key = private_key or get_stix_signing_key()
    signature_bytes = key.sign(bundle_json_str.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    return base64.b64encode(signature_bytes).decode("ascii")


def verify_stix_bundle_signature(
    bundle_json_str: str,
    signature_b64: str,
    public_key: ec.EllipticCurvePublicKey | None = None,
) -> bool:
    """
    Cryptographically verifies an ECDSA SECP256R1 signature over a STIX 2.1 bundle string.
    Guarantees feed integrity and inter-agency non-repudiation across municipal SOCs.
    """
    key = public_key or get_stix_signing_key().public_key()
    try:
        signature_bytes = base64.b64decode(signature_b64.strip().encode("ascii"))
        key.verify(signature_bytes, bundle_json_str.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
        return True
    except Exception:
        return False

