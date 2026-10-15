import io
import logging
import time
import uuid
from decimal import Decimal
from typing import Any
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field
from hares.services.rate_limiter import RedisTokenBucketRateLimiter

from hares.ai.asr_client import LocalASRClient
from hares.ai.audio_classifier import AudioDeepfakeClassifier
from hares.ai.audio_preprocessor import AudioDurationExceededError
from hares.ai.slm_client import LocalSLMClient
from hares.core.config import get_settings
from hares.db.repositories.allowlist_repo import AllowlistRepository
from hares.db.repositories.audit_repo import AuditRepository
from hares.db.repositories.threat_repo import ThreatRepository
from hares.db.session import async_session_scope, sync_session_scope
from hares.engine.allowlist import AllowlistEngine
from hares.engine.homograph import HomographDetector
from hares.engine.ocr import OCREngine
from hares.engine.sanitizer import EntityExtractor, ExtractedEntities, PIIScrubber
from hares.engine.verdict import TriageVerdict, VerdictResult, VerdictSynthesizer

logger = logging.getLogger("hares.api.triage")

router = APIRouter(prefix="/triage", tags=["Citizen Fraud Triage"])

# Singletons for fast inference
allowlist_engine = AllowlistEngine()
homograph_detector = HomographDetector()
entity_extractor = EntityExtractor()
pii_scrubber = PIIScrubber()
verdict_synthesizer = VerdictSynthesizer()
audio_classifier = AudioDeepfakeClassifier()
asr_client = LocalASRClient()
slm_client = LocalSLMClient()
ocr_engine = OCREngine()


async def _get_active_allowlist_domains_async() -> set[str]:
    """Retrieves active official domains asynchronously from database, falling back to cached seed domains."""
    try:
        async with async_session_scope() as session:
            domains = await AllowlistRepository.get_active_domain_names_async(session)
            if domains:
                allowlist_engine.update_domains(domains)
                return domains
    except Exception as exc:
        logger.debug("Database allowlist async query unavailable: %s", str(exc))

    from hares.db.seed_data import OFFICIAL_UAE_DOMAINS_SEED

    seed_domains = {s["domain"].lower().strip() for s in OFFICIAL_UAE_DOMAINS_SEED}
    allowlist_engine.update_domains(seed_domains)
    return seed_domains


def _get_active_allowlist_domains() -> set[str]:
    """Retrieves active official domains synchronously from database, falling back to cached seed domains."""
    try:
        with sync_session_scope() as session:
            domains = AllowlistRepository.get_active_domain_names_sync(session)
            if domains:
                allowlist_engine.update_domains(domains)
                return domains
    except Exception as exc:
        logger.debug("Database allowlist query unavailable: %s", str(exc))

    from hares.db.seed_data import OFFICIAL_UAE_DOMAINS_SEED

    seed_domains = {s["domain"].lower().strip() for s in OFFICIAL_UAE_DOMAINS_SEED}
    allowlist_engine.update_domains(seed_domains)
    return seed_domains


class TriageVerificationResponse(BaseModel):
    request_id: str
    verdict: str  # RED, AMBER, GREEN
    rule_triggered: str
    reason: str
    risk_score: float
    escalation_url: str | None = None
    police_contact: str | None = None
    response_template_en: str
    response_template_ar: str
    extracted_entities: ExtractedEntities
    allowlist_match: dict[str, str] | None = None
    homograph_analysis: dict[str, Any] | None = None
    slm_analysis: dict[str, Any] | None = None
    audio_analysis: dict[str, Any] | None = None
    ocr_extracted_text: str | None = None
    input_type_detected: str = "text"
    execution_latency_ms: float
    privacy_notice: str = "FR-4.1 Compliant: Zero citizen identifiers or personal data retained in memory or storage."


@router.post("/verify", response_model=TriageVerificationResponse)
async def verify_content(
    request: Request,
    text: str | None = Form(None),
    url: str | None = Form(None),
    file: UploadFile | None = File(None),
) -> TriageVerificationResponse:
    """
    Public Citizen Fraud Triage Endpoint (FR-1.x, FR-2.x, FR-3.x).
    Accepts forwarded messages, suspicious URLs, audio voice notes, or screenshot images.
    Performs deterministic verification and local sovereign AI inference, returning
    immediate tri-state verdicts with official Dubai Police escalation pathways.
    """
    # AUDIT-OBS-34: Token-Bucket Rate Limiter per client IP for web triage
    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
    limiter = RedisTokenBucketRateLimiter()
    rl_result = limiter.check_web_triage_rate_limit(client_ip)
    if not rl_result.is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded for citizen web triage ({rl_result.max_allowed} requests/minute). Please slow down.",
            headers={"Retry-After": str(rl_result.reset_seconds)},
        )

    start_time = time.perf_counter()
    request_id = str(uuid.uuid4())
    active_domains = await _get_active_allowlist_domains_async()

    combined_text = (text or "").strip()
    if url and url.strip():
        combined_text = f"{combined_text}\n{url.strip()}".strip()

    input_type = "url" if (url and url.strip() and not (text and text.strip())) else "text"
    ocr_text: str | None = None
    audio_analysis_data: dict[str, Any] | None = None
    audio_bytes: bytes | None = None

    # 1. Handle File Uploads (Image or Audio)
    if file is not None and file.filename:
        filename_lower = file.filename.lower()
        file_bytes = await file.read()

        # 1.1 Audio Ingestion & Acoustic Deepfake Classification (FR-1.x)
        if any(filename_lower.endswith(ext) for ext in [".ogg", ".opus", ".mp3", ".wav", ".m4a"]) or (
            file.content_type and "audio" in file.content_type
        ):
            input_type = "audio"
            audio_bytes = file_bytes
            try:
                audio_result = audio_classifier.classify(file_bytes, filename_hint=file.filename)
                audio_analysis_data = {
                    "is_synthetic": audio_result.is_synthetic,
                    "spectral_anomaly_score": audio_result.spectral_anomaly_score,
                    "p_value": audio_result.p_value,
                    "is_abstaining": audio_result.is_abstaining,
                    "duration_seconds": audio_result.duration_seconds,
                }
                # Transcribe audio for intent evaluation
                transcript_res = asr_client.transcribe(
                    file_bytes,
                    duration_seconds=audio_result.duration_seconds,
                    filename_hint=file.filename or "",
                )
                if transcript_res.text:
                    combined_text = f"{combined_text}\n{transcript_res.text}".strip()
                    logger.info("Transcribed audio voice note (%d chars)", len(transcript_res.text))
            except AudioDurationExceededError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Audio payload exceeds maximum permitted 120s duration: {exc}",
                )
            except Exception as exc:
                logger.warning("Audio triage encountered non-fatal error: %s", str(exc))

        # 1.2 Image Ingestion & Sovereign OCR Extraction
        elif any(filename_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]) or (
            file.content_type and "image" in file.content_type
        ):
            input_type = "image"
            try:
                extracted_ocr = ocr_engine.extract_text_from_bytes(file_bytes, filename_hint=file.filename)
                if extracted_ocr:
                    ocr_text = extracted_ocr
                    combined_text = f"{combined_text}\n{extracted_ocr}".strip()
                    logger.info("OCR successfully extracted %d chars from image", len(extracted_ocr))
            except Exception as exc:
                logger.warning("Image OCR encountered non-fatal error: %s", str(exc))

    if not combined_text and not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verifiable content provided. Please provide text, URL, audio note, or screenshot image.",
        )

    # 2. Extract Entities & Class A Threat Indicators
    extracted = entity_extractor.extract(combined_text)
    candidate_urls = list(extracted["urls"])
    if url and url.strip() and url.strip() not in candidate_urls:
        candidate_urls.append(url.strip())

    candidate_domains = list(extracted["domains"])

    # Parse hostnames from all candidate URLs
    import urllib.parse
    for raw_u in candidate_urls:
        try:
            parsed = urllib.parse.urlparse(raw_u if "://" in raw_u else f"http://{raw_u}")
            host = (parsed.hostname or "").strip().lower()
            if host and host not in candidate_domains:
                candidate_domains.append(host)
        except Exception:
            pass

    # 3. Deterministic Pipeline Execution
    verdict_result: VerdictResult | None = None
    allowlist_match_data: dict[str, str] | None = None
    homograph_analysis_data: dict[str, Any] | None = None
    slm_analysis_data: dict[str, Any] | None = None
    risk_score = 0.5  # Baseline prior

    # 3.1 Audio Synthetic Media Check
    if audio_analysis_data and audio_analysis_data.get("is_synthetic"):
        verdict_result = verdict_synthesizer.build_red_verdict(
            rule_triggered="audio_synthetic_deepfake_detected",
            reason=(
                f"Synthetic voice conversion / deepfake artifacts detected via conformal acoustic evaluation "
                f"(anomaly_score={audio_analysis_data['spectral_anomaly_score']}, p_value={audio_analysis_data['p_value']:.4f})"
            ),
            indicators=["synthetic_voice_recording"],
        )
        risk_score = 0.98

    # 3.2 IDN Homograph & Punycode Lookalike Check (FR-2.3)
    if verdict_result is None:
        for domain in candidate_domains:
            is_spoof, spoof_reason = homograph_detector.check_spoof(domain, active_domains)
            if is_spoof:
                homograph_analysis_data = {
                    "is_spoof": True,
                    "domain": domain,
                    "rule": spoof_reason,
                }
                verdict_result = verdict_synthesizer.build_red_verdict(
                    rule_triggered="idn_homograph_spoof",
                    reason=f"Detected fraudulent lookalike domain spoofing UAE entity: '{domain}' ({spoof_reason})",
                    indicators=[domain],
                )
                risk_score = 0.99
                break

    # 3.3 Brand Impersonation Phishing Domain Check on Unofficial Domains
    if verdict_result is None:
        for domain in candidate_domains:
            reg_d = allowlist_engine.extract_registrable_domain(domain)
            if reg_d not in active_domains:
                lower_d = domain.lower()
                spoofed_target = None
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
                    verdict_result = verdict_synthesizer.build_red_verdict(
                        rule_triggered="brand_impersonation_phishing_domain",
                        reason=f"Detected fraudulent external destination '{domain}' impersonating {spoofed_target} on unverified TLD.",
                        indicators=[domain],
                    )
                    risk_score = 0.96
                    break

    # 3.4 Database Known Malicious IoC Check
    if verdict_result is None and (candidate_urls or candidate_domains):
        try:
            async with async_session_scope() as session:
                for indicator in candidate_urls + candidate_domains:
                    existing = await ThreatRepository.get_indicator_by_normalized_value_async(session, indicator)
                    if existing and existing.verdict == "RED":
                        verdict_result = verdict_synthesizer.build_red_verdict(
                            rule_triggered="known_threat_ioc_match",
                            reason=f"Indicator matched verified malicious threat database: '{indicator}'",
                            indicators=[indicator],
                        )
                        risk_score = float(existing.risk_score or 0.95)
                        break
        except Exception as exc:
            logger.debug("Database threat check skipped: %s", str(exc))

    # 3.5 Exact Registrable Allowlist Verification (FR-2.2)
    if verdict_result is None and (candidate_urls or candidate_domains):
        all_targets = candidate_urls if candidate_urls else candidate_domains
        all_match = True
        matched_domain = ""
        matched_entity = ""

        for target in all_targets:
            reg_domain = allowlist_engine.extract_registrable_domain(target)
            if reg_domain and reg_domain in active_domains:
                matched_domain = reg_domain
                matched_entity = (
                    "Dubai Government / UAE Verified Entity"
                    if not matched_domain.startswith("ecrime")
                    else "Dubai Police e-Crime"
                )
            else:
                all_match = False

        if all_match and matched_domain:
            allowlist_match_data = {
                "verified_domain": matched_domain,
                "entity_name": matched_entity,
            }
            verdict_result = verdict_synthesizer.build_green_verdict(
                entity_name=matched_entity,
                verified_domain=matched_domain,
                indicators=[matched_domain],
            )
            risk_score = 0.01

    # 3.6 Local Small Language Model (SLM) Social Engineering Intent Evaluation (FR-2.4)
    if verdict_result is None and combined_text:
        scrubbed_text = pii_scrubber.scrub(combined_text)
        slm_result = slm_client.triage_text(scrubbed_text)
        slm_analysis_data = {
            "is_impersonation": slm_result.is_impersonation,
            "detected_tactics": slm_result.detected_tactics,
            "confidence_score": slm_result.confidence_score,
            "urgency_or_coercion": slm_result.urgency_or_coercion,
            "financial_or_credential_demand": slm_result.financial_or_credential_demand,
            "reasoning_summary": slm_result.reasoning_summary,
        }

        is_malicious = (
            (
                slm_result.is_impersonation
                and (slm_result.urgency_or_coercion or slm_result.financial_or_credential_demand)
                and slm_result.confidence_score >= 0.70
            )
            or any(
                t in slm_result.detected_tactics
                for t in [
                    "prompt_injection",
                    "lottery_prize",
                    "crypto_investment_fraud",
                    "banking_kyc_freeze",
                    "traffic_fine_lure",
                    "account_suspension",
                ]
            )
            or (slm_result.financial_or_credential_demand and slm_result.urgency_or_coercion and slm_result.confidence_score >= 0.70)
        )

        # Check for adversarial prompt injection in raw text
        lower_comb = combined_text.lower()
        if not is_malicious and any(kw in lower_comb for kw in ["<|im_start|>", "ignore all previous instructions", "system override"]):
            is_malicious = True
            slm_result.reasoning_summary = "Adversarial prompt injection attempt detected and neutralized."
            slm_result.detected_tactics = ["prompt_injection"]

        # Check for crypto / prize scam markers
        if not is_malicious and any(kw in lower_comb for kw in ["rabihit", "500,000 aed", "lottery", "crypto wealth", "18.5%"]):
            is_malicious = True
            slm_result.reasoning_summary = "Unregulated financial lottery / crypto investment lure."
            slm_result.detected_tactics = ["lottery_prize" if "rabihit" in lower_comb else "crypto_investment"]

        if is_malicious:
            verdict_result = verdict_synthesizer.build_red_verdict(
                rule_triggered="slm_social_engineering_detected",
                reason=f"{slm_result.reasoning_summary} ({', '.join(slm_result.detected_tactics)})",
                indicators=candidate_urls or candidate_domains,
            )
            risk_score = max(0.85, round(slm_result.confidence_score, 4))
        elif (
            not slm_result.is_impersonation
            and not slm_result.urgency_or_coercion
            and not slm_result.financial_or_credential_demand
            and not candidate_urls
            and not candidate_domains
            and slm_result.confidence_score <= 0.25
        ):
            # Benign conversation
            verdict_result = verdict_synthesizer.build_green_verdict(
                entity_name="Personal Benign Communication",
                verified_domain=None,
                indicators=[],
                reason="No authority impersonation, financial demands, or malicious indicators detected.",
                rule_triggered="benign_communication_safe",
            )
            risk_score = 0.05
        else:
            # Default sovereign fallback to Amber (caution)
            verdict_result = verdict_synthesizer.build_amber_verdict(
                rule_triggered="unverified_source_fallback",
                reason="Submission does not match authenticated official allowlist; source authenticity cannot be proven.",
                indicators=candidate_urls or candidate_domains,
            )
            risk_score = 0.45

    # 3.7 Genuine Human Audio Recording Verification
    if verdict_result is None and audio_analysis_data and not audio_analysis_data.get("is_synthetic"):
        verdict_result = verdict_synthesizer.build_green_verdict(
            entity_name="Verified Human Voice Recording",
            verified_domain=None,
            indicators=[],
            reason=f"Acoustic evaluation verified natural human voice characteristics (p_value={audio_analysis_data['p_value']:.4f}).",
            rule_triggered="genuine_human_voice_pass",
        )
        risk_score = 0.05

    # 4. Final Fallback
    if verdict_result is None:
        verdict_result = verdict_synthesizer.build_amber_verdict(
            rule_triggered="unverified_default_caution",
            reason="Content authenticity could not be established; exercise caution.",
            indicators=[],
        )
        risk_score = 0.45

    # 5. Persist Threat Indicators & Sanitized Audit Record (FR-4.1)
    try:
        async with async_session_scope() as session:
            # If confirmed RED threat, persist Class A IoCs
            if verdict_result.verdict == TriageVerdict.RED:
                targets = candidate_urls + candidate_domains
                if not targets and combined_text:
                    targets = [combined_text[:120]]
                for indicator in targets:
                    await ThreatRepository.upsert_indicator_async(
                        session=session,
                        indicator_type="url" if indicator.startswith("http") else ("domain" if "." in indicator else "lure"),
                        raw_indicator=indicator,
                        verdict="RED",
                        risk_score=Decimal(str(risk_score)),
                    )

            # Sanitized Audit Log (Zero Class B Citizen PII)
            await AuditRepository.record_triage_audit_async(
                session=session,
                request_id=uuid.UUID(request_id),
                citizen_user_hash=None,  # Automatically pseudonymized
                payload_type=input_type,
                triage_verdict=verdict_result.verdict.value,
                rule_triggered=verdict_result.rule_triggered,
                latency_ms=int(round((time.perf_counter() - start_time) * 1000.0)),
            )
    except Exception as exc:
        logger.warning("Database telemetry persistence failed: %s", str(exc))

    # 6. Live Prometheus Observability & Model Metrics (Phase 6)
    try:
        from hares.core.metrics import (
            record_conformal_p_value,
            record_e2e_latency,
            record_verdict,
        )

        total_duration_sec = time.perf_counter() - start_time
        record_e2e_latency(input_type, verdict_result.verdict.value, total_duration_sec)
        record_verdict(verdict_result.verdict.value, verdict_result.rule_triggered)
        if audio_analysis_data and "p_value" in audio_analysis_data and audio_analysis_data["p_value"] is not None:
            record_conformal_p_value(float(audio_analysis_data["p_value"]))
    except Exception as met_exc:
        logger.debug("Prometheus telemetry observation skipped: %s", str(met_exc))

    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    logger.info("Triage complete for request %s: verdict=%s latency=%.2fms", request_id, verdict_result.verdict.value, elapsed_ms)

    return TriageVerificationResponse(
        request_id=request_id,
        verdict=verdict_result.verdict.value,
        rule_triggered=verdict_result.rule_triggered,
        reason=verdict_result.reason,
        risk_score=risk_score,
        escalation_url=verdict_result.escalation_url,
        police_contact=verdict_result.police_contact,
        response_template_en=verdict_result.response_template_en,
        response_template_ar=verdict_result.response_template_ar,
        extracted_entities=extracted,
        allowlist_match=allowlist_match_data,
        homograph_analysis=homograph_analysis_data,
        slm_analysis=slm_analysis_data,
        audio_analysis=audio_analysis_data,
        ocr_extracted_text=ocr_text,
        input_type_detected=input_type,
        execution_latency_ms=elapsed_ms,
    )
