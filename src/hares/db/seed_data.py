from datetime import datetime, timezone, timedelta
from typing import TypedDict


class OfficialDomainSeed(TypedDict):
    domain: str
    entity_name: str
    entity_type: str
    verified_owner: str


OFFICIAL_UAE_DOMAINS_SEED: list[OfficialDomainSeed] = [
    {
        "domain": "ecrime.ae",
        "entity_name": "Dubai Police e-Crime Portal",
        "entity_type": "government",
        "verified_owner": "Dubai Police General Headquarters",
    },
    {
        "domain": "dubaipolice.gov.ae",
        "entity_name": "Dubai Police Official Portal",
        "entity_type": "government",
        "verified_owner": "Dubai Police General Headquarters",
    },
    {
        "domain": "salik.ae",
        "entity_name": "Salik Toll System",
        "entity_type": "transport",
        "verified_owner": "Salik Company PJSC",
    },
    {
        "domain": "dewa.gov.ae",
        "entity_name": "Dubai Electricity & Water Authority",
        "entity_type": "utility",
        "verified_owner": "DEWA Government of Dubai",
    },
    {
        "domain": "dubai.ae",
        "entity_name": "Digital Dubai Official Portal",
        "entity_type": "government",
        "verified_owner": "Digital Dubai Authority",
    },
    {
        "domain": "rta.ae",
        "entity_name": "Roads & Transport Authority Dubai",
        "entity_type": "transport",
        "verified_owner": "Roads and Transport Authority",
    },
    {
        "domain": "gdrfad.gov.ae",
        "entity_name": "GDRFA Dubai (Immigration)",
        "entity_type": "government",
        "verified_owner": "General Directorate of Residency and Foreigners Affairs",
    },
    {
        "domain": "centralbank.ae",
        "entity_name": "Central Bank of the UAE",
        "entity_type": "banking",
        "verified_owner": "Central Bank of the UAE",
    },
    {
        "domain": "mofa.gov.ae",
        "entity_name": "Ministry of Foreign Affairs",
        "entity_type": "government",
        "verified_owner": "Ministry of Foreign Affairs UAE",
    },
    {
        "domain": "emiratespost.ae",
        "entity_name": "Emirates Post Official Portal",
        "entity_type": "logistics",
        "verified_owner": "Emirates Post Group",
    },
    {
        "domain": "tdra.gov.ae",
        "entity_name": "TDRA Telecom Regulatory Authority",
        "entity_type": "government",
        "verified_owner": "Telecommunications and Digital Government Regulatory Authority",
    },
    {
        "domain": "adpolice.gov.ae",
        "entity_name": "Abu Dhabi Police Official Portal",
        "entity_type": "government",
        "verified_owner": "Abu Dhabi Police General Headquarters",
    },
    {
        "domain": "xn--mgbaam7a8h",
        "entity_name": "UAE Arabic Country Code Top Level Domain (.امارات)",
        "entity_type": "government",
        "verified_owner": "Telecommunications and Digital Government Regulatory Authority",
    },
]


def get_default_quarterly_review() -> datetime:
    """Returns timestamp 90 days in the future for quarterly review compliance."""
    return datetime.now(timezone.utc) + timedelta(days=90)


def seed_official_domains_if_empty() -> int:
    """Seeds OFFICIAL_UAE_DOMAINS_SEED into official_domains table if it is currently empty.
    Returns the number of seeded domains."""
    from hares.db.models import OfficialDomain
    from hares.db.session import sync_session_scope
    from sqlalchemy import select

    with sync_session_scope() as session:
        existing = session.execute(select(OfficialDomain).limit(1)).scalar_one_or_none()
        if existing is not None:
            return 0

        inserted_count = 0
        review_date = get_default_quarterly_review()
        for seed in OFFICIAL_UAE_DOMAINS_SEED:
            domain_entry = OfficialDomain(
                domain=seed["domain"].lower().strip(),
                entity_name=seed["entity_name"],
                entity_type=seed["entity_type"],
                verified_owner=seed["verified_owner"],
                quarterly_review_at=review_date,
                is_active=True,
            )
            session.add(domain_entry)
            inserted_count += 1
        return inserted_count


def seed_security_credentials_if_empty() -> bool:
    """
    Seeds hashed and salted municipal SOC administrative credentials (NFR-1.3).
    Ensures zero plaintext passkeys or passwords persisted.
    """
    from hares.core.config import get_settings
    from hares.db.models import SecurityCredential
    from hares.db.session import sync_session_scope
    from sqlalchemy import select

    settings = get_settings()
    with sync_session_scope() as session:
        existing = session.execute(
            select(SecurityCredential).where(SecurityCredential.credential_name == "soc_admin_passkey")
        ).scalar_one_or_none()
        if existing is not None:
            return False

        cred = SecurityCredential(
            credential_name="soc_admin_passkey",
            salt_hex=settings.SOC_ADMIN_SALT_HEX,
            hash_hex=settings.SOC_ADMIN_PASSWORD_HASH,
            algorithm="pbkdf2_sha256",
        )
        session.add(cred)
        return True

