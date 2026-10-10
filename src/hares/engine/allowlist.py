import tldextract


class AllowlistEngine:
    """
    Deterministic Registrable Domain Allowlist Matcher (FR-2.2).
    Extracts registrable domains via public suffix parsing and verifies exact matches
    against curated UAE public-sector and verified utility registries.
    """

    def __init__(self, active_domains: set[str] | None = None) -> None:
        # Enforce air-gapped operation with bundled suffix list (AUDIT-OBS-09)
        self._extractor = tldextract.TLDExtract(cache_dir=None, suffix_list_urls=None)
        self._active_domains: set[str] = {
            domain.strip().lower().rstrip(".")
            for domain in (active_domains or set())
            if domain and domain.strip()
        }

    def update_domains(self, domains: set[str]) -> None:
        """Atomically updates the active allowlist cache."""
        self._active_domains = {
            domain.strip().lower().rstrip(".")
            for domain in domains
            if domain and domain.strip()
        }

    def extract_registrable_domain(self, url_or_domain: str) -> str:
        """
        Extracts and normalizes the registrable domain (e.g., 'sub.ecrime.ae:8080/path' -> 'ecrime.ae').
        Returns empty string if domain is absent or unparseable.
        """
        if not url_or_domain or not url_or_domain.strip():
            return ""

        extracted = self._extractor(url_or_domain.strip())
        if not extracted.domain or not extracted.suffix:
            return ""

        return f"{extracted.domain}.{extracted.suffix}".lower().rstrip(".")

    def is_allowlisted(self, url_or_domain: str) -> bool:
        """
        Returns True if the candidate's exact registrable domain is in the active allowlist.
        Does not allow wildcard subdomains of unauthorized entities.
        """
        registrable = self.extract_registrable_domain(url_or_domain)
        if not registrable:
            return False
        return registrable in self._active_domains
