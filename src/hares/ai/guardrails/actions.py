"""
Project Hares: Deterministic Guardrail Actions for NVIDIA NeMo Guardrails.

Implements input and output safety checks:
1. Class B Citizen PII Masking (Emirates ID, credit cards, phones, OTPs).
2. Adversarial Prompt Injection & ChatML Breakout Defense.
3. Topical Fraud Gating.
4. Pydantic v2 Schema Enforcement.
5. Official Dubai Police Escalation Verification.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import re
from typing import Any

try:
    from nemoguardrails.actions import action
except (ImportError, ModuleNotFoundError):
    def action(name: str | None = None) -> Any:
        def decorator(fn: Any) -> Any:
            return fn
        if callable(name):
            return name
        return decorator

from hares.ai.schemas import TextTriageInferenceResult
from hares.engine.sanitizer import PIIScrubber

logger = logging.getLogger("hares.ai.guardrails.actions")
_pii_scrubber = PIIScrubber()

# Known adversarial prompt injection patterns across English, Arabic, and ChatML
CHATML_DELIMITERS = [
    "<|im_start|>",
    "<|im_end|>",
    "<|endoftext|>",
    "<|im_sep|>",
    "<|extra_0|>",
    "<|extra_1|>",
]

XML_BREAKOUT_PATTERNS = [
    re.compile(r"</?citizen_forwarded_text>", re.IGNORECASE),
    re.compile(r"</?system_instruction>", re.IGNORECASE),
    re.compile(r"</?user_prompt>", re.IGNORECASE),
]

ENGLISH_JAILBREAK_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|system)\s+prompts", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?(developer\s+mode|dan|jailbroken)", re.IGNORECASE),
    re.compile(r"bypass\s+(all\s+)?safety\s+filters", re.IGNORECASE),
    re.compile(r"pretend\s+you\s+have\s+no\s+(rules|restrictions|guidelines)", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system\s+prompt|developer\s+instructions)", re.IGNORECASE),
]

ARABIC_JAILBREAK_PATTERNS = [
    re.compile(r"تجاهل\s+(جميع\s+)?التعليمات\s+السابقة"),
    re.compile(r"تجاوز\s+(نظام\s+)?الأمان"),
    re.compile(r"أنت\s+الآن\s+في\s+وضع\s+المطور"),
    re.compile(r"تصرف\s+دون\s+أي\s+قيود"),
    re.compile(r"اكشف\s+(عن\s+)?(تعليمات\s+النظام|الأوامر\s+السرية)"),
]

FRAUD_OR_SECURITY_INDICATORS = [
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"\b(www\.[a-z0-9\-]+\.[a-z]{2,})\b", re.IGNORECASE),
    re.compile(r"\b(police|شرطة|مرور|إقامة|تأشيرة|مخالفة|غرامة|حجز|قضائي|محكمة)\b", re.IGNORECASE),
    re.compile(r"\b(post|بريد|طرد|شحنة|parcel|delivery|courier|aramex|empost|dhl|fedex)\b", re.IGNORECASE),
    re.compile(r"\b(bank|مصرف|بنك|حساب|بطاقة|card|otp|رمز|cvv|kyc|freeze|تجميد|سداد|pay|aed|درهم|fee|رسوم)\b", re.IGNORECASE),
    re.compile(r"\b(salik|سالك|dewa|ديوا|uae\s*pass|هوية|emirates\s*id|icp)\b", re.IGNORECASE),
    re.compile(r"\b(scam|fraud|phish|احتيال|نصب|مشبوه|رسالة|تنبيه|urgent|عاجل|immediately|فوراً)\b", re.IGNORECASE),
]

OFF_TOPIC_CONVERSATIONAL_PROBES = [
    re.compile(r"^(hi|hello|hey|how are you|good morning|who are you|tell me a joke|write a poem|مرحبا|أهلا|من أنت|كيف حالك)\s*[\.!\?]*$", re.IGNORECASE),
    re.compile(r"^(write|generate|create)\s+(a\s+)?(python|javascript|code|script|program|essay|story|poem)\b", re.IGNORECASE),
    re.compile(r"^(what\s+is\s+the\s+capital\s+of|calculate|solve\s+math)\b", re.IGNORECASE),
    re.compile(r"^(اكتب|أنشئ)\s+(كود|برنامج|نص|قصيدة|مقال|قصة)\b"),
    re.compile(r"^(ما\s+هي\s+عاصمة|احسب|حل\s+مسألة)\b"),
]


@action(name="mask_citizen_pii")
def mask_citizen_pii(text: str) -> dict[str, Any]:
    """
    Input Rail Action: Deterministically masks citizen Class B PII before model processing (FR-4.1).
    Redacts Emirates IDs, credit card numbers, OTP codes, and personal telephone numbers.
    """
    bounded_text = text[:4096] if text else ""
    scrubbed = _pii_scrubber.scrub(bounded_text)
    was_masked = scrubbed != bounded_text
    if was_masked:
        logger.info("🛡️ [Guardrail] Masked citizen Class B PII in incoming prompt.")
    return {
        "sanitized_text": scrubbed,
        "was_masked": was_masked,
    }


@action(name="detect_prompt_injection")
def detect_prompt_injection(text: str) -> dict[str, Any]:
    """
    Input Rail Action: Detects adversarial prompt injection, ChatML escapes, and jailbreaks (NFR-1.3).
    """
    if not text:
        return {"is_attack": False, "attack_type": "none", "sanitized_text": ""}

    # Normalize outer wrapper if caller passed pre-enclosed tags
    target_text = text.strip()
    if re.match(r"^<citizen_forwarded_text>.*</citizen_forwarded_text>$", target_text, re.DOTALL | re.IGNORECASE):
        target_text = re.sub(r"^<citizen_forwarded_text>\s*", "", target_text, flags=re.IGNORECASE)
        target_text = re.sub(r"\s*</citizen_forwarded_text>$", "", target_text, flags=re.IGNORECASE)

    # 1. ChatML token delimiter detection
    for token in CHATML_DELIMITERS:
        if token in target_text:
            logger.warning("🚨 [Guardrail] ChatML token breakout intercepted: %s", token)
            return {
                "is_attack": True,
                "attack_type": "chatml_delimiter_breakout",
                "sanitized_text": target_text.replace(token, "[REDACTED_TOKEN]"),
            }

    # 2. XML boundary breakout detection
    for pattern in XML_BREAKOUT_PATTERNS:
        if pattern.search(target_text):
            logger.warning("🚨 [Guardrail] XML boundary tag breakout intercepted.")
            return {
                "is_attack": True,
                "attack_type": "xml_boundary_escape",
                "sanitized_text": pattern.sub("[REDACTED_TAG]", target_text),
            }

    # 3. English adversarial jailbreak directives
    for pattern in ENGLISH_JAILBREAK_PATTERNS:
        if pattern.search(target_text):
            logger.warning("🚨 [Guardrail] English adversarial directive intercepted: %s", pattern.pattern)
            return {
                "is_attack": True,
                "attack_type": "direct_instruction_override",
                "sanitized_text": target_text,
            }

    # 4. Arabic adversarial jailbreak directives
    for pattern in ARABIC_JAILBREAK_PATTERNS:
        if pattern.search(target_text):
            logger.warning("🚨 [Guardrail] Arabic adversarial directive intercepted: %s", pattern.pattern)
            return {
                "is_attack": True,
                "attack_type": "arabic_jailbreak_directive",
                "sanitized_text": target_text,
            }

    # 5. Base64 encoded payload detection
    b64_matches = re.findall(r"\b[A-Za-z0-9+/]{24,}={0,2}\b", target_text)
    for match in b64_matches:
        try:
            decoded = base64.b64decode(match, validate=True).decode("utf-8", errors="ignore").lower()
            if any(term in decoded for term in ["ignore", "system", "override", "bypass", "instruction", "تجاهل"]):
                logger.warning("🚨 [Guardrail] Base64 obfuscated injection intercepted: %s", match)
                return {
                    "is_attack": True,
                    "attack_type": "base64_obfuscated_injection",
                    "sanitized_text": target_text,
                }
        except (binascii.Error, UnicodeDecodeError):
            pass

    return {
        "is_attack": False,
        "attack_type": "none",
        "sanitized_text": target_text,
    }


@action(name="check_topical_boundary")
def check_topical_boundary(text: str) -> dict[str, Any]:
    """
    Input Rail Action: Asserts that input contains fraud, phishing, link, authority, or financial cues.
    Deflects off-topic conversational probes.
    """
    if not text:
        return {"is_relevant": True, "reason": "empty_input"}

    trimmed = text.strip()

    # 1. Any cyber fraud, authority, or financial cue guarantees relevancy
    for indicator in FRAUD_OR_SECURITY_INDICATORS:
        if indicator.search(trimmed):
            return {
                "is_relevant": True,
                "reason": "on_topic_security_query",
            }

    # 2. Direct match against off-topic patterns
    for probe in OFF_TOPIC_CONVERSATIONAL_PROBES:
        if probe.search(trimmed):
            logger.info("🛡️ [Guardrail] Off-topic conversational probe deflected: '%s'", trimmed[:40])
            return {
                "is_relevant": False,
                "reason": "off_topic_conversational_probe",
            }

    return {
        "is_relevant": True,
        "reason": "on_topic_security_query",
    }


@action(name="validate_triage_schema")
def validate_triage_schema(raw_output: str) -> dict[str, Any]:
    """
    Output Rail Action: Enforces that model output parses cleanly into TextTriageInferenceResult (FR-2.4).
    Normalizes free-form text into strict JSON contract.
    """
    if not raw_output:
        fallback = TextTriageInferenceResult(
            is_impersonation=False,
            impersonated_entity=None,
            urgency_or_coercion=False,
            financial_or_credential_demand=False,
            confidence_score=0.10,
            detected_tactics=["none"],
            reasoning_summary="No discernible pattern detected.",
        )
        return {"is_valid": False, "validated_json": fallback.model_dump_json()}

    clean_str = raw_output.strip()
    # Strip markdown codeblocks if model wrapped output in ```json
    if clean_str.startswith("```"):
        clean_str = re.sub(r"^```(?:json)?\s*", "", clean_str)
        clean_str = re.sub(r"\s*```$", "", clean_str)

    try:
        parsed_dict = json.loads(clean_str)
        validated = TextTriageInferenceResult.model_validate(parsed_dict)
        return {"is_valid": True, "validated_json": validated.model_dump_json()}
    except Exception as exc:
        logger.warning("🛡️ [Guardrail] Model output failed Pydantic schema validation: %s. Normalizing...", exc)
        # Construct deterministic fallback
        is_fraud = "red" in clean_str.lower() or "high risk" in clean_str.lower() or "scam" in clean_str.lower()
        fallback = TextTriageInferenceResult(
            is_impersonation=is_fraud,
            impersonated_entity="Unverified Entity" if is_fraud else None,
            urgency_or_coercion=is_fraud,
            financial_or_credential_demand=is_fraud,
            confidence_score=0.85 if is_fraud else 0.20,
            detected_tactics=["account_suspension"] if is_fraud else ["none"],
            reasoning_summary="Normalized by sovereign guardrail schema engine.",
        )
        return {"is_valid": False, "validated_json": fallback.model_dump_json()}


@action(name="enforce_dubai_police_escalation")
def enforce_dubai_police_escalation(raw_output: str) -> str:
    """
    Output Rail Action: Ensures high-risk verdicts link exclusively to official Dubai Police portals (FR-3.1).
    """
    if "https://www.ecrime.ae" not in raw_output and ("RED" in raw_output or "HIGH RISK" in raw_output):
        logger.info("🛡️ [Guardrail] Enforcing official Dubai Police escalation link in high-risk output.")
        return (
            raw_output.rstrip()
            + "\n\n🚨 Official Dubai Police Escalation: https://www.ecrime.ae | Call: 901"
        )
    return raw_output
