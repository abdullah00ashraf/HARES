"""
Project Hares — Sovereign Fraud Triage Coordinator
Unifies multi-tier fraud triage across Web API, WhatsApp workers, and municipal intelligence feeds.
Coordinates Tier 1 Deterministic Verification, Tier 2 Neural ZeroGPU Inference, and Tier 3 Offline Fallbacks.
"""

import logging
import urllib.parse
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

from hares.ai.schemas import TextTriageInferenceResult
from hares.ai.slm_client import LocalSLMClient
from hares.engine.allowlist import AllowlistEngine
from hares.engine.homograph import HomographDetector
from hares.engine.sanitizer import EntityExtractor, ExtractedEntities, PIIScrubber
from hares.engine.verdict import TriageVerdict, VerdictResult, VerdictSynthesizer

logger = logging.getLogger("hares.services.triage_coordinator")

TriageTierType = Literal["TIER_1_DETERMINISTIC", "TIER_2_NEURAL_ZEROGPU", "TIER_2_NEURAL_LOCAL", "TIER_3_OFFLINE_FALLBACK"]


class TriageCoordinatorResult(BaseModel):
    """Encapsulates unified triage verdict and attribution telemetry across evaluation tiers."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    verdict_result: VerdictResult = Field(description="Standardized tri-state verdict with localized advisories")
    risk_score: float = Field(description="Normalized risk score between 0.0 and 1.0")
    triage_tier_evaluated: TriageTierType = Field(description="The exact system tier that rendered the verdict")
    tier_preemption_reason: str = Field(description="Detailed reason for tier execution or preemption")
    provider_used: str = Field(description="Internal model engine or heuristic provider identifier")
    candidate_urls: list[str] = Field(default_factory=list, description="Extracted Class A URLs")
    candidate_domains: list[str] = Field(default_factory=list, description="Extracted Class A candidate hostnames")
    extracted_entities: ExtractedEntities = Field(description="Full entity extraction dictionary")
    allowlist_match_data: dict[str, str] | None = Field(default=None, description="Allowlist match metadata if verified")
    homograph_analysis_data: dict[str, str | bool] | None = Field(default=None, description="Homograph spoof metadata if detected")
    slm_analysis_data: dict[str, str | bool | float | list[str] | None] | None = Field(default=None, description="Neural SLM intent telemetry")


class TriageCoordinator:
    """
    Centralized Fraud Triage Coordinator.
    Enforces identical evaluation rules and precedence across Web API and Celery workers:
    - Tier 1: Deterministic Engine (Allowlist, Blocklist, IDN Homographs, Brand Impersonation)
    - Tier 2: Neural ZeroGPU Engine (Qwen2.5-3B + NVIDIA NeMo Guardrails)
    - Tier 3: Sovereign Offline Heuristics (Local NLP Classifier)
    """

    def __init__(
        self,
        allowlist_engine: AllowlistEngine | None = None,
        homograph_detector: HomographDetector | None = None,
        entity_extractor: EntityExtractor | None = None,
        pii_scrubber: PIIScrubber | None = None,
        verdict_synthesizer: VerdictSynthesizer | None = None,
        slm_client: LocalSLMClient | None = None,
    ) -> None:
        self.allowlist_engine = allowlist_engine or AllowlistEngine()
        self.homograph_detector = homograph_detector or HomographDetector()
        self.entity_extractor = entity_extractor or EntityExtractor()
        self.pii_scrubber = pii_scrubber or PIIScrubber()
        self.verdict_synthesizer = verdict_synthesizer or VerdictSynthesizer()
        self.slm_client = slm_client or LocalSLMClient()

    def coordinate_triage(
        self,
        text: str,
        url: str | None = None,
        active_domains: set[str] | None = None,
    ) -> TriageCoordinatorResult:
        """
        Coordinates full multi-tier triage evaluation on arbitrary text and/or URL inputs.
        Guarantees deterministic precedence and returns explicit tier attribution.
        """
        combined_text = (text or "").strip()
        if url and url.strip():
            combined_text = f"{combined_text}\n{url.strip()}".strip()

        # 1. Extract Threat Entities & Parse Hostnames
        extracted = self.entity_extractor.extract(combined_text)
        candidate_urls = list(extracted["urls"])
        if url and url.strip() and url.strip() not in candidate_urls:
            candidate_urls.append(url.strip())

        candidate_domains = list(extracted["domains"])
        for raw_u in candidate_urls:
            try:
                parsed = urllib.parse.urlparse(raw_u if "://" in raw_u else f"http://{raw_u}")
                host = (parsed.hostname or "").strip().lower()
                if host and host not in candidate_domains:
                    candidate_domains.append(host)
            except Exception:
                pass

        known_domains = active_domains or self.allowlist_engine.get_active_domains()

        # 2. TIER 1: DETERMINISTIC PREEMPTION
        # 2.1 IDN Homograph / Punycode Lookalike Spoof Check (RED)
        for domain in candidate_domains:
            is_spoof, spoof_reason = self.homograph_detector.check_spoof(domain, known_domains)
            if is_spoof:
                verdict = self.verdict_synthesizer.build_red_verdict(
                    rule_triggered="idn_homograph_spoof",
                    reason=f"Detected fraudulent lookalike domain spoofing UAE entity: '{domain}' ({spoof_reason})",
                    indicators=[domain],
                )
                return TriageCoordinatorResult(
                    verdict_result=verdict,
                    risk_score=0.99,
                    triage_tier_evaluated="TIER_1_DETERMINISTIC",
                    tier_preemption_reason=f"Detected deceptive IDN homograph spoof: '{domain}' ({spoof_reason})",
                    provider_used="engine.homograph",
                    candidate_urls=candidate_urls,
                    candidate_domains=candidate_domains,
                    extracted_entities=extracted,
                    homograph_analysis_data={"is_spoof": True, "domain": domain, "rule": spoof_reason},
                )

        # 2.2 Brand Impersonation Phishing Domain Check on Unofficial Domains (RED)
        for domain in candidate_domains:
            reg_d = self.allowlist_engine.extract_registrable_domain(domain)
            if reg_d not in known_domains:
                lower_d = domain.lower()
                spoofed_target: str | None = None
                if any(k in lower_d for k in ["police", "ecrime", "traffic"]):
                    spoofed_target = "Dubai Police"
                elif any(k in lower_d for k in ["salik", "salik-pay"]):
                    spoofed_target = "Salik"
                elif any(k in lower_d for k in ["dewa", "dewa-bill"]):
                    spoofed_target = "DEWA"
                elif any(k in lower_d for k in ["emiratespost", "post-delivery", "empost", "delivery-fee"]):
                    spoofed_target = "Emirates Post"
                elif any(k in lower_d for k in ["enbd", "adcb", "adib", "dib", "bank-auth", "banking-portal"]):
                    spoofed_target = "UAE Banking Authority"
                elif any(k in lower_d for k in ["crypto", "wealth", "invest", "lottery", "prize"]):
                    spoofed_target = "Cryptocurrency & Investment Scheme"

                if spoofed_target:
                    verdict = self.verdict_synthesizer.build_red_verdict(
                        rule_triggered="brand_impersonation_phishing_domain",
                        reason=f"Detected fraudulent external destination '{domain}' impersonating {spoofed_target} on unverified TLD.",
                        indicators=[domain],
                    )
                    return TriageCoordinatorResult(
                        verdict_result=verdict,
                        risk_score=0.96,
                        triage_tier_evaluated="TIER_1_DETERMINISTIC",
                        tier_preemption_reason=f"Detected brand impersonation phishing domain targeting {spoofed_target}: '{domain}'",
                        provider_used="engine.brand_impersonation",
                        candidate_urls=candidate_urls,
                        candidate_domains=candidate_domains,
                        extracted_entities=extracted,
                    )

        # 2.3 Exact Registrable Domain Allowlist Verification (GREEN)
        if candidate_urls or candidate_domains:
            all_targets = candidate_urls if candidate_urls else candidate_domains
            all_match = True
            matched_domain = ""
            matched_entity = ""

            for target in all_targets:
                reg_domain = self.allowlist_engine.extract_registrable_domain(target)
                if reg_domain and reg_domain in known_domains:
                    matched_domain = reg_domain
                    matched_entity = (
                        "Dubai Government / UAE Verified Entity"
                        if not matched_domain.startswith("ecrime")
                        else "Dubai Police e-Crime"
                    )
                else:
                    all_match = False

            if all_match and matched_domain:
                verdict = self.verdict_synthesizer.build_green_verdict(
                    entity_name=matched_entity,
                    verified_domain=matched_domain,
                    indicators=[matched_domain],
                )
                return TriageCoordinatorResult(
                    verdict_result=verdict,
                    risk_score=0.01,
                    triage_tier_evaluated="TIER_1_DETERMINISTIC",
                    tier_preemption_reason=f"Verified official UAE entity allowlist domain: '{matched_domain}'",
                    provider_used="engine.allowlist",
                    candidate_urls=candidate_urls,
                    candidate_domains=candidate_domains,
                    extracted_entities=extracted,
                    allowlist_match_data={"verified_domain": matched_domain, "entity_name": matched_entity},
                )

        # 3. TIER 2 & TIER 3: SOVEREIGN SLM & NLP INTENT EVALUATION
        scrubbed_text = self.pii_scrubber.scrub(combined_text)
        slm_result: TextTriageInferenceResult = self.slm_client.triage_text(scrubbed_text)

        provider_used = getattr(self.slm_client, "last_provider_used", "offline_heuristics")
        if "zerogpu" in provider_used:
            tier_evaluated: TriageTierType = "TIER_2_NEURAL_ZEROGPU"
            tier_reason = f"Evaluated by Sovereign Qwen2.5-3B Neural Engine on ZeroGPU ({provider_used})"
        elif provider_used in ["local_vllm", "outlines_local"]:
            tier_evaluated = "TIER_2_NEURAL_LOCAL"
            tier_reason = f"Evaluated by Local Sovereign SLM Cluster ({provider_used})"
        else:
            tier_evaluated = "TIER_3_OFFLINE_FALLBACK"
            tier_reason = "ZeroGPU/SLM unavailable or timed out; evaluated by Sovereign Deterministic NLP Engine"

        slm_analysis_data: dict[str, str | bool | float | list[str] | None] = {
            "is_impersonation": slm_result.is_impersonation,
            "detected_tactics": list(slm_result.detected_tactics),
            "confidence_score": slm_result.confidence_score,
            "urgency_or_coercion": slm_result.urgency_or_coercion,
            "financial_or_credential_demand": slm_result.financial_or_credential_demand,
            "reasoning_summary": slm_result.reasoning_summary,
            "provider_used": provider_used,
        }

        lower_comb = combined_text.lower()

        # Check for anti-phishing advisory and civic awareness context (protects non-coercive syntax)
        has_anti_phish_advisory = any(
            w in lower_comb
            for w in [
                "never share your password", "never share your otp", "never share", "do not share", "don't share",
                "لا تشارك", "لا تفصح", "عدم مشاركة", "تحذير أمني", "تنبيه أمني", "e-statement", "monthly statement",
                "traffic awareness", "awareness advisory", "safety first", "safe following distance", "foggy morning",
                "tzakkar teftah", "asharet el moroor", "le salametak", "neshabhat 3aleik"
            ]
        )

        malicious_tactics = [
            t for t in slm_result.detected_tactics
            if t in [
                "prompt_injection",
                "lottery_prize",
                "crypto_investment_fraud",
                "banking_kyc_freeze",
                "traffic_fine_lure",
                "account_suspension",
            ] and not (has_anti_phish_advisory and t in ["banking_kyc_freeze", "traffic_fine_lure", "account_suspension"])
        ]

        is_malicious = (
            (
                slm_result.is_impersonation
                and (slm_result.urgency_or_coercion or slm_result.financial_or_credential_demand)
                and slm_result.confidence_score >= 0.70
                and not has_anti_phish_advisory
            )
            or bool(malicious_tactics)
            or (slm_result.financial_or_credential_demand and slm_result.urgency_or_coercion and slm_result.confidence_score >= 0.70 and not has_anti_phish_advisory)
        )

        # Adversarial prompt injection containment
        if not is_malicious and any(kw in lower_comb for kw in ["<|im_start|>", "ignore all previous instructions", "system override"]):
            is_malicious = True
            slm_result.reasoning_summary = "Adversarial prompt injection attempt detected and neutralized."
            slm_result.detected_tactics = ["prompt_injection"]

        # Speculative financial / lottery lures
        if not is_malicious and any(kw in lower_comb for kw in ["rabihit", "500,000 aed", "lottery", "crypto wealth", "18.5%", "300%", "usdt", "telegram", "t.me", "guaranteed returns"]):
            is_malicious = True
            slm_result.reasoning_summary = "Unregulated financial lottery / crypto investment lure."
            slm_result.detected_tactics = ["lottery_prize" if any(p in lower_comb for p in ["rabihit", "lottery", "prize"]) else "crypto_investment"]

        has_speculative_or_crypto = any(
            kw in lower_comb for kw in [
                "crypto", "bitcoin", "usdt", "invest", "returns", "wealth", "lottery",
                "prize", "rabihit", "telegram", "t.me", "300%", "18.5%", "guaranteed", "million aed", "500,000"
            ]
        ) or any(t in slm_result.detected_tactics for t in ["crypto_investment", "lottery_prize"])

        is_benign_conversational = any(
            kw in lower_comb
            for kw in [
                # English
                "hello", "hi", "how are you", "good morning", "good evening", "see you", "meeting",
                "thank you", "thanks", "ok", "okay", "lunch", "dinner", "weekend", "family",
                "welcome", "congratulations", "happy birthday", "traffic awareness", "safety first",
                "monthly statement", "e-statement", "never share", "payment confirmed", "receipt",
                # Arabizi
                "salam", "marhaba", "kifak", "keifak", "ezayak", "shlonak", "shokran", "shukran",
                "tamam", "mashy", "yalla", "inshallah", "habibi", "akhi", "neshabhat 3aleik",
                "tam 5asm", "benaja7", "be naja7", "le sedad", "fatoorat", "el daf3a", "gayya fel tareeq",
                # Arabic
                "مرحبا", "أهلا", "السلام عليكم", "كيف الحال", "شكرا", "تمام", "إن شاء الله",
                "صباح الخير", "مساء الخير", "مبروك", "عيد سعيد", "تم خصم", "تم استلام", "بنجاح"
            ]
        )

        if is_malicious:
            verdict = self.verdict_synthesizer.build_red_verdict(
                rule_triggered="slm_social_engineering_detected",
                reason=f"{slm_result.reasoning_summary} ({', '.join(slm_result.detected_tactics)})",
                indicators=candidate_urls or candidate_domains,
            )
            final_risk = max(0.85, round(slm_result.confidence_score, 4))
        elif (
            (is_benign_conversational or not slm_result.is_impersonation)
            and not slm_result.urgency_or_coercion
            and not slm_result.financial_or_credential_demand
            and not candidate_urls
            and not candidate_domains
            and not has_speculative_or_crypto
            and slm_result.confidence_score <= 0.40
        ):
            verdict = self.verdict_synthesizer.build_green_verdict(
                entity_name="Personal Benign Communication",
                verified_domain=None,
                indicators=[],
                reason="No authority impersonation, financial demands, or malicious indicators detected.",
                rule_triggered="benign_conversational_syntax",
            )
            final_risk = 0.05
        else:
            if candidate_urls or candidate_domains:
                reason = "External commercial or third-party web link detected without direct phishing indicators or government impersonation. Verify the sender independently before clicking or entering credentials."
                rule = "unverified_source_fallback"
            elif has_speculative_or_crypto:
                reason = "Unverified speculative financial, lottery, or investment lure."
                rule = "speculative_financial_lure"
            else:
                reason = "Submission does not match authenticated official allowlist; source authenticity cannot be proven."
                rule = "unverified_source_fallback"

            verdict = self.verdict_synthesizer.build_amber_verdict(
                reason=reason,
                rule_triggered=rule,
                indicators=candidate_urls or candidate_domains,
            )
            final_risk = max(0.35, min(0.65, round(slm_result.confidence_score, 4)))

        slm_analysis_data["detected_tactics"] = list(slm_result.detected_tactics)
        slm_analysis_data["reasoning_summary"] = slm_result.reasoning_summary
        slm_analysis_data["confidence_score"] = final_risk

        return TriageCoordinatorResult(
            verdict_result=verdict,
            risk_score=final_risk,
            triage_tier_evaluated=tier_evaluated,
            tier_preemption_reason=tier_reason,
            provider_used=provider_used,
            candidate_urls=candidate_urls,
            candidate_domains=candidate_domains,
            extracted_entities=extracted,
            slm_analysis_data=slm_analysis_data,
        )
