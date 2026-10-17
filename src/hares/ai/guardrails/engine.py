"""
Project Hares: Sovereign Programmable Guardrails Engine.

Orchestrates input, output, and conversational safety rails built on NVIDIA NeMo Guardrails
and deterministic Project Hares security shields:
- NFR-1.1: 100% Local Inference & Sovereign Data Residency
- NFR-1.3: Adversarial Prompt Injection & Jailbreak Immunity
- FR-4.1: Cryptographic Class B Citizen PII Masking
- FR-2.4: Closed Contract Pydantic v2 Schema Enforcement
- FR-3.1: Authentic Dubai Police Escalation Binding (ecrime.ae / 901)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from hares.ai.guardrails.actions import (
    check_topical_boundary,
    detect_prompt_injection,
    enforce_dubai_police_escalation,
    mask_citizen_pii,
    validate_triage_schema,
)
from hares.ai.schemas import TextTriageInferenceResult
from hares.engine.sanitizer import PIIScrubber

logger = logging.getLogger("hares.ai.guardrails.engine")
_pii_scrubber = PIIScrubber()


@dataclass
class GuardrailResult:
    """Outcome descriptor of a guardrail safety evaluation pass."""

    allowed: bool
    sanitized_input: str
    output_text: str | None = None
    blocked_reason: str | None = None
    pii_masked: bool = False
    attack_type: str | None = None
    triage_result: TextTriageInferenceResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SovereignGuardrailsEngine:
    """
    Sovereign Programmable Guardrails Engine wrapping NVIDIA NeMo Guardrails.
    Executes multi-phase deterministic and model-guided security boundaries.
    """

    def __init__(self, config_dir: Path | str | None = None) -> None:
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self._nemo_rails: Any = None
        self._init_nemo_rails()

    def _init_nemo_rails(self) -> None:
        """Initializes NeMo Guardrails LLMRails with local configuration if available."""
        try:
            from nemoguardrails import LLMRails, RailsConfig

            if self.config_dir.exists():
                config = RailsConfig.from_path(str(self.config_dir))
                self._nemo_rails = LLMRails(config)
                # Register deterministic actions
                self._nemo_rails.register_action(mask_citizen_pii, name="mask_citizen_pii")
                self._nemo_rails.register_action(detect_prompt_injection, name="detect_prompt_injection")
                self._nemo_rails.register_action(check_topical_boundary, name="check_topical_boundary")
                self._nemo_rails.register_action(validate_triage_schema, name="validate_triage_schema")
                self._nemo_rails.register_action(enforce_dubai_police_escalation, name="enforce_dubai_police_escalation")
                logger.info("🛡️ [GuardrailEngine] Successfully initialized NeMo Guardrails with Colang 2.0 policies.")
        except Exception as exc:
            logger.warning(
                "🛡️ [GuardrailEngine] NeMo Guardrails dynamic loader initialized in direct deterministic mode: %s",
                exc,
            )
            self._nemo_rails = None

    def process_input(self, text: str) -> GuardrailResult:
        """
        Executes Input Rails:
        1. Class B Citizen PII Masking (Emirates ID, credit cards, phones, OTPs).
        2. Prompt Injection & Jailbreak Defense (ChatML token breakouts, Base64 obfuscation, Arabic jailbreaks).
        3. Topical Fraud Gating (deflects off-topic chat).
        """
        if not text:
            return GuardrailResult(
                allowed=True,
                sanitized_input="",
                output_text=None,
            )

        # 1. Deterministic Class B PII Redaction Rail (FR-4.1)
        pii_res = mask_citizen_pii(text)
        sanitized_text = pii_res["sanitized_text"]
        was_masked = pii_res["was_masked"]

        # 2. Adversarial Prompt Injection Rail (NFR-1.3)
        injection_res = detect_prompt_injection(sanitized_text)
        if injection_res["is_attack"]:
            attack_type = injection_res["attack_type"]
            logger.warning("🚨 [GuardrailEngine] Intercepted adversarial prompt injection: %s", attack_type)
            return GuardrailResult(
                allowed=False,
                sanitized_input=injection_res.get("sanitized_text", sanitized_text),
                output_text="SECURITY_ALERT: Adversarial prompt injection detected. Triage aborted.",
                blocked_reason="prompt_injection_detected",
                pii_masked=was_masked,
                attack_type=attack_type,
            )

        # 3. Topical Gating Rail
        topical_res = check_topical_boundary(sanitized_text)
        if not topical_res["is_relevant"]:
            refusal_msg = "حارس دبي مخصص فقط لفحص الرسائل والاحتيال ومكافحة الجرائم الإلكترونية. يرجى إرسال الرسالة أو الرابط المشبوه."
            return GuardrailResult(
                allowed=False,
                sanitized_input=sanitized_text,
                output_text=refusal_msg,
                blocked_reason="off_topic_conversational_probe",
                pii_masked=was_masked,
            )

        return GuardrailResult(
            allowed=True,
            sanitized_input=sanitized_text,
            pii_masked=was_masked,
        )

    def process_output(self, raw_output: str) -> TextTriageInferenceResult:
        """
        Executes Output Rails:
        1. Pydantic v2 Schema Enforcement (FR-2.4).
        2. Dubai Police Escalation Verification (FR-3.1, FR-3.2).
        3. Secondary Class B PII Leakage Check.
        """
        # 1. Pydantic Schema Enforcement
        schema_res = validate_triage_schema(raw_output)
        clean_json_str = schema_res["validated_json"]

        # Parse verified dictionary
        data = json.loads(clean_json_str)

        # 2. Dubai Police Escalation Verification for High-Risk verdicts
        if data.get("is_impersonation") or data.get("confidence_score", 0.0) >= 0.70:
            summary = data.get("reasoning_summary", "")
            if "ecrime.ae" not in summary:
                data["reasoning_summary"] = (
                    summary.rstrip()
                    + " [Official Escalation: https://www.ecrime.ae | Call: 901]"
                )

        # 3. Secondary PII Masking on reasoning summary
        if "reasoning_summary" in data:
            data["reasoning_summary"] = _pii_scrubber.scrub(data["reasoning_summary"])

        return TextTriageInferenceResult.model_validate(data)

    def generate_safe_triage(
        self,
        text: str,
        generator_fn: Callable[[str], str | TextTriageInferenceResult],
    ) -> GuardrailResult:
        """
        End-to-End Programmable Guardrail Execution:
        1. Runs input safety rails.
        2. If allowed, invokes sovereign local generator function.
        3. Runs output safety rails and returns validated GuardrailResult.
        """
        # Step 1: Input Rails
        input_verdict = self.process_input(text)
        if not input_verdict.allowed:
            is_injection = input_verdict.blocked_reason == "prompt_injection_detected"
            fallback_triage = TextTriageInferenceResult(
                is_impersonation=False,
                impersonated_entity=None,
                urgency_or_coercion=False,
                financial_or_credential_demand=False,
                confidence_score=1.00 if is_injection else 0.00,
                detected_tactics=["prompt_injection"] if is_injection else ["none"],
                reasoning_summary=input_verdict.output_text or "Input blocked by programmable guardrail safety policy.",
            )
            input_verdict.triage_result = fallback_triage
            return input_verdict

        # Step 2: Invoke Local Model Generator
        try:
            raw_gen = generator_fn(input_verdict.sanitized_input)
            if isinstance(raw_gen, TextTriageInferenceResult):
                raw_output_str = raw_gen.model_dump_json()
            else:
                raw_output_str = str(raw_gen)
        except Exception as gen_err:
            logger.error("🚨 [GuardrailEngine] Model generation failure: %s", gen_err)
            raw_output_str = ""

        # Step 3: Output Rails
        verified_triage = self.process_output(raw_output_str)

        return GuardrailResult(
            allowed=True,
            sanitized_input=input_verdict.sanitized_input,
            output_text=verified_triage.model_dump_json(),
            pii_masked=input_verdict.pii_masked,
            triage_result=verified_triage,
        )
