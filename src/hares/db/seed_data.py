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
