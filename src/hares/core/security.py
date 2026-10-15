import base64
import hashlib
import hmac
import re
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

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
# Municipal SOC Security Credentials Salting & PBKDF2 Hashing (NFR-1.3)
# =========================================================================
def hash_passkey_pbkdf2(passkey: str, salt_hex: str, iterations: int = 100_000) -> str:
    """
    Computes PBKDF2-HMAC-SHA256 hash of a municipal administrator passkey (NFR-1.3).
    Ensures zero plaintext passwords stored in database or source code.
    """
    salt_bytes = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac("sha256", passkey.encode("utf-8"), salt_bytes, iterations).hex()


def verify_passkey_pbkdf2(candidate_passkey: str, salt_hex: str, expected_hash_hex: str) -> bool:
    """Verifies candidate passkey in constant time against expected PBKDF2 hash."""
    candidate_hash = hash_passkey_pbkdf2(candidate_passkey, salt_hex)
    return hmac.compare_digest(candidate_hash, expected_hash_hex)


# =========================================================================
# Cryptographic STIX 2.1 CTI Signing & Non-Repudiation (AUDIT-OBS-16, AUDIT-OBS-36)
# =========================================================================
_STIX_SIGNING_KEY: ec.EllipticCurvePrivateKey | None = None


def get_stix_signing_key() -> ec.EllipticCurvePrivateKey:
    """
    Retrieves or deterministically derives the sovereign municipal ECDSA SECP256R1 signing key.
    Loads from STIX_SIGNING_KEY_HEX if configured, otherwise falls back to ephemeral key.
    """
    global _STIX_SIGNING_KEY
    if _STIX_SIGNING_KEY is None:
        try:
            from hares.core.config import get_settings

            settings = get_settings()
            if settings.STIX_SIGNING_KEY_HEX and len(settings.STIX_SIGNING_KEY_HEX.strip()) >= 64:
                scalar = int(settings.STIX_SIGNING_KEY_HEX.strip(), 16)
                _STIX_SIGNING_KEY = ec.derive_private_key(scalar, ec.SECP256R1())
            else:
                _STIX_SIGNING_KEY = ec.generate_private_key(ec.SECP256R1())
        except Exception:
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

