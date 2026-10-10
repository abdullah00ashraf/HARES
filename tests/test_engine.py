import pytest
from hares.engine.allowlist import AllowlistEngine
from hares.engine.homograph import HomographDetector
from hares.engine.sanitizer import EntityExtractor, PIIScrubber
from hares.engine.verdict import TriageVerdict, VerdictSynthesizer


@pytest.fixture
def sample_allowlist() -> set[str]:
    return {
        "ecrime.ae",
        "dubaipolice.gov.ae",
        "salik.ae",
        "dewa.gov.ae",
        "dubai.ae",
        "rta.ae",
        "centralbank.ae",
        "xn--mgbaam7a8h",  # .امارات
    }


def test_allowlist_exact_match(sample_allowlist):
    """Verifies that exact registrable domains match correctly across various URL structures."""
    engine = AllowlistEngine(sample_allowlist)

    assert engine.is_allowlisted("ecrime.ae") is True
    assert engine.is_allowlisted("https://ecrime.ae") is True
    assert engine.is_allowlisted("https://subdomain.ecrime.ae:8443/report?id=123") is True
    assert engine.is_allowlisted("http://portal.dubaipolice.gov.ae/traffic") is True
    assert engine.is_allowlisted("https://salik.ae/recharge") is True


def test_allowlist_non_matching(sample_allowlist):
    """Verifies that unapproved domains do not match."""
    engine = AllowlistEngine(sample_allowlist)

    assert engine.is_allowlisted("ecrime-pay.com") is False
    assert engine.is_allowlisted("https://salik-toll-recharge.ae") is False
    assert engine.is_allowlisted("google.com") is False
    assert engine.is_allowlisted("") is False


def test_homograph_authentic_arabic_cctld(sample_allowlist):
    """Verifies that authentic Arabic domains under .امارات (xn--mgbaam7a8h) pass safely."""
    detector = HomographDetector()

    # Legitimate Arabic domain under .امارات: بلدية-دبي.امارات (Punycode: xn----ymcbabb9a5b3a1a.xn--mgbaam7a8h)
    arabic_domain = "xn----ymcbabb9a5b3a1a.xn--mgbaam7a8h"
    is_spoof, reason = detector.check_spoof(arabic_domain, sample_allowlist)
    assert is_spoof is False
    assert reason == "clean"


def test_homograph_punycode_in_latin_domain(sample_allowlist):
    """Verifies that Punycode labels under non-Arabic TLDs (.ae, .com) are flagged as attacks."""
    detector = HomographDetector()

    # Attacker spoofing dubaipolice with Cyrillic 'о' in Punycode under .ae
    spoofed_domain = "xn--dubaipolice-97a.ae"
    is_spoof, reason = detector.check_spoof(spoofed_domain, sample_allowlist)
    assert is_spoof is True
    assert "punycode_homograph" in reason


def test_homograph_lookalike_levenshtein(sample_allowlist):
    """Verifies length-normalized lookalike detection while preventing false alarms on short domains."""
    detector = HomographDetector()

    # 1. Lookalike targeting dewa (length 5 vs 4: max_len=5, d=1 -> d/max_len = 0.20 <= 0.25)
    is_spoof, reason = detector.check_spoof("dewaa.ae", sample_allowlist)
    assert is_spoof is True
    assert "lookalike_spoof" in reason

    # 2. Short domain: 'dew.ae' vs 'dewa' (length 3 vs 4: max_len=4 < 5) -> must not falsely trigger
    is_spoof, reason = detector.check_spoof("dew.ae", sample_allowlist)
    assert is_spoof is False
    assert reason == "clean"

    # 3. Short domain: 'ata.ae' vs 'rta' (length 3 vs 3: max_len=3 < 5) -> must not falsely trigger
    is_spoof, reason = detector.check_spoof("ata.ae", sample_allowlist)
    assert is_spoof is False
    assert reason == "clean"


def test_entity_extractor():
    """Verifies extraction of URLs, domains, phones, UAE IBANs, and crypto wallets."""
    extractor = EntityExtractor()
    sample_text = (
        "Pay your fine immediately at https://dubai-police.scam/pay or visit dubaipolice.gov.ae. "
        "Contact officer on +971-50-987-6543 or transfer AED 500 to IBAN AE12 0330 0001 2345 6789 012. "
        "BTC accepted: bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq"
    )

    entities = extractor.extract(sample_text)
    assert "https://dubai-police.scam/pay" in entities["urls"]
    assert any("dubaipolice.gov.ae" in d for d in entities["domains"])
    assert any("971" in p for p in entities["phone_numbers"])
    assert any("AE120330000123456789012" in i for i in entities["ibans"])
    assert "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq" in entities["crypto_wallets"]


def test_pii_scrubber():
    """Verifies that citizen Emirates IDs, credit cards, and OTPs are redacted."""
    scrubber = PIIScrubber()
    sample_text = (
        "My Emirates ID is 784-1990-1234567-1 and card number is 4111-2222-3333-4444. "
        "Your secret OTP is 837492. Do not share."
    )

    scrubbed = scrubber.scrub(sample_text)
    assert "784-1990-1234567-1" not in scrubbed
    assert "[REDACTED_EID]" in scrubbed
    assert "4111-2222-3333-4444" not in scrubbed
    assert "[REDACTED_CARD]" in scrubbed
    assert "[REDACTED_OTP]" in scrubbed


def test_verdict_synthesizer_red():
    """Verifies Red verdict generation with Dubai Police e-Crime escalation handoff."""
    synth = VerdictSynthesizer()
    res = synth.build_red_verdict(
        rule_triggered="punycode_homograph",
        reason="Deceptive domain impersonating police",
        indicators=["https://xn--police.ae"],
    )

    assert res.verdict == TriageVerdict.RED
    assert res.escalation_url == "https://www.ecrime.ae"
    assert res.police_contact == "901"
    assert "ecrime.ae" in res.response_template_en
    assert "901" in res.response_template_en
    assert "شرطة دبي" in res.response_template_ar


def test_verdict_synthesizer_green():
    """Verifies Green verdict generation for official entities."""
    synth = VerdictSynthesizer()
    res = synth.build_green_verdict(
        entity_name="Dubai Police General Headquarters",
        verified_domain="ecrime.ae",
        indicators=["ecrime.ae"],
    )

    assert res.verdict == TriageVerdict.GREEN
    assert res.rule_triggered == "allowlist_exact_match"
    assert "Verified Official" in res.explanation_en
    assert "رسمي موثق" in res.explanation_ar


def test_verdict_synthesizer_amber():
    """Verifies Amber default caution verdict."""
    synth = VerdictSynthesizer()
    res = synth.build_amber_verdict(reason="Unverified external link")

    assert res.verdict == TriageVerdict.AMBER
    assert "Unverified" in res.explanation_en
    assert "غير موثق" in res.explanation_ar
