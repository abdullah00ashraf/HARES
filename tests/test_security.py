import hashlib
import hmac
import pytest
from hares.core.security import derive_citizen_user_hash, verify_meta_signature


def test_verify_meta_signature_valid():
    """Verifies that a genuine HMAC-SHA256 signature returns True."""
    secret = "test_app_secret_12345"
    payload = b'{"object": "whatsapp_business_account"}'
    valid_hash = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    header = f"sha256={valid_hash}"

    assert verify_meta_signature(payload, header, secret) is True


def test_verify_meta_signature_invalid():
    """Verifies that an altered or incorrect hash returns False."""
    secret = "test_app_secret_12345"
    payload = b'{"object": "whatsapp_business_account"}'
    invalid_header = "sha256=badhash0000000000000000000000000000000000000000000000000000000000"

    assert verify_meta_signature(payload, invalid_header, secret) is False


def test_verify_meta_signature_malformed_header():
    """Verifies that headers missing the sha256= prefix or empty strings are rejected."""
    assert verify_meta_signature(b"data", "invalid_header", "secret") is False
    assert verify_meta_signature(b"data", "", "secret") is False


def test_derive_citizen_user_hash():
    """Verifies deterministic pseudonymization and E.164 normalization (FR-4.1)."""
    salt = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    phone_clean = "971501234567"
    phone_with_symbols = "+971-50-123-4567"

    hash_1 = derive_citizen_user_hash(phone_clean, salt)
    hash_2 = derive_citizen_user_hash(phone_with_symbols, salt)

    assert len(hash_1) == 64
    assert hash_1 == hash_2  # Normalized equivalence
