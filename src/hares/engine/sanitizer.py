import re
from typing_extensions import TypedDict


class ExtractedEntities(TypedDict):
    urls: list[str]
    domains: list[str]
    phone_numbers: list[str]
    ibans: list[str]
    crypto_wallets: list[str]


# URL extraction regex supporting http/https and naked links with port/path
URL_PATTERN = re.compile(
    r"(?:https?://)?(?:[a-zA-Z0-9\u0600-\u06FF\-\._~%]+(?:\.[a-zA-Z0-9\u0600-\u06FF\-\._~%]+)+)(?::\d+)?(?:/[^\s]*)?",
    re.IGNORECASE,
)

# Strict HTTP/HTTPS URL pattern
EXPLICIT_URL_PATTERN = re.compile(
    r"https?://[^\s<>\"'{}|\\^`]+",
    re.IGNORECASE,
)

# Standalone domain pattern (at least one dot, valid TLD length >= 2 or punycode)
DOMAIN_PATTERN = re.compile(
    r"\b(?:[a-zA-Z0-9\u00A0-\uFFFF](?:[a-zA-Z0-9\u00A0-\uFFFF\-]{0,61}[a-zA-Z0-9\u00A0-\uFFFF])?\.)+(?:[a-zA-Z]{2,}|xn--[a-zA-Z0-9]+|[\u0600-\u06FF]{2,})\b",
    re.IGNORECASE,
)

# International & UAE Phone Number Regex (E.164, regional UAE 05X, and foreign numbers)
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,4}[\s\-]?)?(?:\(?\d{2,4}\)?[\s\-]?)?\d{3,4}[\s\-]?\d{3,4}\b"
)

# UAE IBAN Pattern: AE followed by 2 check digits and 19 alphanumeric/digits (total 23 chars)
UAE_IBAN_PATTERN = re.compile(
    r"\bAE\d{2}\s?(?:\d{4}\s?){4}\d{3}\b",
    re.IGNORECASE,
)

# Crypto Wallet Patterns: Bitcoin (Legacy, SegWit, Bech32) and Ethereum (0x...)
BTC_PATTERN = re.compile(r"\b(?:1[a-km-zA-HJ-NP-Z1-9]{25,34}|3[a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[a-z0-9]{39,59})\b")
ETH_PATTERN = re.compile(r"\b0x[a-fA-F0-9]{40}\b")

# PII Patterns for Class B Redaction (FR-4.1, FR-4.2)
# Emirates ID: 784-YYYY-XXXXXXX-Z or 784YYYYXXXXXXXZ
EMIRATES_ID_PATTERN = re.compile(r"\b784[\s\-]?[12]\d{3}[\s\-]?\d{7}[\s\-]?\d\b")

# Payment Card: 13 to 19 digits with optional spaces or dashes
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d{4}[\s\-]?){3}\d{4}\b")

# OTP Verification Code: 4-8 digit codes surrounded by OTP / verification keywords
OTP_PATTERN = re.compile(
    r"(?i)\b(?:otp|code|verification|passcode|رمز|الرمز|كود)(?:[\s\:\=\-]|is|هو){1,8}\b(\d{4,8})\b"
)


class EntityExtractor:
    """
    Extracts Class A threat indicators (URLs, domains, foreign numbers, financial accounts)
    from forwarded message strings across English and Arabic text bodies.
    """

    def extract(self, text: str) -> ExtractedEntities:
        if not text or not text.strip():
            return {
                "urls": [],
                "domains": [],
                "phone_numbers": [],
                "ibans": [],
                "crypto_wallets": [],
            }

        # Defense-in-depth: Bound input length to 4096 chars (AUDIT-OBS-06)
        text = text[:4096]

        # 1. Extract Explicit & Inferred URLs
        explicit_urls = EXPLICIT_URL_PATTERN.findall(text)
        all_urls = list(dict.fromkeys([u.strip().rstrip(".,;!?:") for u in explicit_urls if u.strip()]))

        # 2. Extract Domains
        raw_domains = DOMAIN_PATTERN.findall(text)
        domains: list[str] = []
        for d in raw_domains:
            clean_d = d.strip().lower().rstrip(".,;!?:")
            if clean_d and clean_d not in domains:
                domains.append(clean_d)

        # 3. Extract Phone Numbers (minimum 8 digits to filter short codes and numbers)
        raw_phones = PHONE_PATTERN.findall(text)
        phones: list[str] = []
        for p in raw_phones:
            digits_only = re.sub(r"\D", "", p)
            if 8 <= len(digits_only) <= 15:
                clean_p = p.strip().rstrip(".,;!?:")
                if clean_p not in phones:
                    phones.append(clean_p)

        # 4. Extract UAE IBANs
        raw_ibans = UAE_IBAN_PATTERN.findall(text)
        ibans = list(dict.fromkeys([re.sub(r"\s+", "", i).upper() for i in raw_ibans if i.strip()]))

        # 5. Extract Crypto Wallets
        btc_wallets = BTC_PATTERN.findall(text)
        eth_wallets = ETH_PATTERN.findall(text)
        wallets = list(dict.fromkeys(btc_wallets + eth_wallets))

        return {
            "urls": all_urls,
            "domains": domains,
            "phone_numbers": phones,
            "ibans": ibans,
            "crypto_wallets": wallets,
        }


class PIIScrubber:
    """
    Bilingual Citizen PII Redaction Pipeline (FR-4.2).
    Strips Class B citizen personal data (Emirates IDs, bank cards, OTPs) from text bodies
    prior to persistent intelligence storage or audit logging.
    """

    def scrub(self, text: str) -> str:
        if not text:
            return ""

        # Defense-in-depth: Bound input length to 4096 chars (AUDIT-OBS-06)
        scrubbed = text[:4096]

        # 1. Redact Emirates IDs
        scrubbed = EMIRATES_ID_PATTERN.sub("[REDACTED_EID]", scrubbed)

        # 2. Redact Payment Card Numbers
        scrubbed = CREDIT_CARD_PATTERN.sub("[REDACTED_CARD]", scrubbed)

        # 3. Redact OTPs
        scrubbed = OTP_PATTERN.sub(
            lambda m: m.group(0).replace(m.group(1), "[REDACTED_OTP]"),
            scrubbed,
        )

        return scrubbed
