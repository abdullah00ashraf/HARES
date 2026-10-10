import re
import idna
import tldextract
from Levenshtein import distance

# Whitelist legitimate UAE Arabic ccTLD (.امارات / xn--mgbaam7a8h)
ALLOWED_ARABIC_TLDS: set[str] = {"xn--mgbaam7a8h"}

# Arabic Unicode Block range check: \u0600-\u06FF, \u0750-\u077F, \u08A0-\u08FF, Arabic-Indic digits, hyphen
ARABIC_UNICODE_PATTERN = re.compile(r"^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9\-]+$")


class HomographDetector:
    """
    IDN Homograph, Punycode Spoof, and Lookalike Distance Detector (FR-2.3).
    Validates internationalized domain names, protects UAE Arabic ccTLD (.امارات),
    and scores normalized Levenshtein lookalikes against allowlisted targets.
    """

    def __init__(self) -> None:
        # Enforce air-gapped operation with bundled suffix list (AUDIT-OBS-09)
        self._extractor = tldextract.TLDExtract(cache_dir=None, suffix_list_urls=None)

    def check_spoof(self, candidate_domain: str, allowlist: set[str]) -> tuple[bool, str]:
        """
        Evaluates a candidate domain for IDN Punycode spoofing, mixed scripts,
        and length-normalized Levenshtein lookalike spoofing against allowlisted entities.

        Returns:
            (is_spoof: bool, reason: str)
            - is_spoof is True if malicious/spoofed, False if clean.
            - reason provides diagnostic or rule identifier.
        """
        if not candidate_domain or not candidate_domain.strip():
            return False, "empty_domain"

        clean_candidate = candidate_domain.strip().lower().rstrip(".")

        # Extract domain components
        extracted = self._extractor(clean_candidate)
        if not extracted.domain or not extracted.suffix:
            # If tldextract cannot find standard domain + suffix, attempt direct label inspection
            raw_labels = clean_candidate.split(".")
            if len(raw_labels) < 2:
                return False, "unparseable_domain"
            tld = raw_labels[-1]
            non_tld_labels = raw_labels[:-1]
        else:
            tld = extracted.suffix.split(".")[-1]
            non_tld_labels = [extracted.subdomain, extracted.domain] if extracted.subdomain else [extracted.domain]

        try:
            # 1. TLD Punycode Verification
            # Convert TLD to ASCII Punycode representation if in unicode
            tld_ascii = idna.encode(tld).decode("ascii").lower()
            if tld_ascii.startswith("xn--") and tld_ascii not in ALLOWED_ARABIC_TLDS:
                return True, f"unauthorized_punycode_tld_{tld_ascii}"

            is_arabic_cctld = (tld_ascii in ALLOWED_ARABIC_TLDS)

            # 2. Non-TLD Label Verification
            for raw_label in non_tld_labels:
                if not raw_label:
                    continue

                for label_part in raw_label.split("."):
                    if not label_part:
                        continue

                    # Check if label is punycode or contains non-ASCII
                    label_ascii = idna.encode(label_part).decode("ascii").lower()
                    if label_ascii.startswith("xn--"):
                        decoded_label = idna.decode(label_ascii)
                        # Under .امارات, labels must consist strictly of authentic Arabic characters
                        if is_arabic_cctld:
                            if not ARABIC_UNICODE_PATTERN.match(decoded_label):
                                return True, f"mixed_script_spoof_in_arabic_domain_{label_part}"
                        else:
                            # Non-Arabic TLDs with punycode subdomains targeting UAE are high-risk attacks
                            return True, f"punycode_homograph_in_label_{label_part}"

        except (idna.IDNAError, UnicodeError):
            return True, "malformed_idn_encoding"

        # 3. Length-Normalized Lookalike Distance against allowlist (FR-2.3)
        candidate_domain_part = extracted.domain.lower() if extracted.domain else ""
        if candidate_domain_part:
            for official in allowlist:
                official_extracted = self._extractor(official.strip().lower())
                official_domain_part = official_extracted.domain.lower()
                if not official_domain_part:
                    continue

                # Exact match against allowlist is clean
                if candidate_domain_part == official_domain_part:
                    continue

                d = distance(candidate_domain_part, official_domain_part)
                max_len = max(len(candidate_domain_part), len(official_domain_part))

                # Length-normalized edit distance rule:
                # Requires max_len >= 5 to prevent short domain false positives (e.g. dew.ae vs dewa)
                # and d/max_len <= 0.25 (e.g., 1 edit on length 5 = 0.20 <= 0.25)
                if max_len >= 5 and 0 < d <= 2 and (d / max_len) <= 0.25:
                    return True, f"lookalike_spoof_of_{official}"

        return False, "clean"
