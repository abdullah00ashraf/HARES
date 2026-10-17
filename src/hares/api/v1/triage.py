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
from hares.services.triage_coordinator import TriageCoordinator, TriageCoordinatorResult

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
triage_coordinator = TriageCoordinator(
    allowlist_engine=allowlist_engine,
    homograph_detector=homograph_detector,
    entity_extractor=entity_extractor,
    pii_scrubber=pii_scrubber,
    verdict_synthesizer=verdict_synthesizer,
    slm_client=slm_client,
)


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
    model_engine: str = "Hugging Face ZeroGPU (Qwen2.5-3B + NVIDIA NeMo Guardrails)"
    triage_tier_evaluated: str = Field(
        default="TIER_1_DETERMINISTIC",
        description="The engine tier that rendered the verdict (TIER_1_DETERMINISTIC, TIER_2_NEURAL_ZEROGPU, TIER_2_NEURAL_LOCAL, TIER_3_OFFLINE_FALLBACK)",
    )
    tier_preemption_reason: str | None = Field(
        default=None,
        description="Detailed explanation of why deterministic preemption occurred or why fallback was engaged",
    )
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

    # 3. Multi-Tier Triage Pipeline Execution
    verdict_result: VerdictResult | None = None
    allowlist_match_data: dict[str, str] | None = None
    homograph_analysis_data: dict[str, Any] | None = None
    slm_analysis_data: dict[str, Any] | None = None
    risk_score = 0.5  # Baseline prior
    triage_tier_evaluated = "TIER_1_DETERMINISTIC"
    tier_preemption_reason = "Evaluated via Sovereign Deterministic Pipeline"

    # 3.1 Audio Synthetic Media Check (Conformal Acoustic Evaluation)
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
        triage_tier_evaluated = "TIER_1_DETERMINISTIC"
        tier_preemption_reason = "Synthetic voice conversion / deepfake artifacts detected via conformal acoustic evaluation"
    elif audio_analysis_data and not audio_analysis_data.get("is_synthetic") and not combined_text:
        # Genuine human audio recording without text
        verdict_result = verdict_synthesizer.build_green_verdict(
            entity_name="Verified Human Voice Recording",
            verified_domain=None,
            indicators=[],
            reason=f"Acoustic evaluation verified natural human voice characteristics (p_value={audio_analysis_data['p_value']:.4f}).",
            rule_triggered="genuine_human_voice_pass",
        )
        risk_score = 0.05
        triage_tier_evaluated = "TIER_1_DETERMINISTIC"
        tier_preemption_reason = "Acoustic evaluation verified natural human voice characteristics"
    else:
        # 3.2 Coordinate Unified Multi-Tier Triage
        coord_res = triage_coordinator.coordinate_triage(
            combined_text,
            url=url,
            active_domains=active_domains,
        )
        verdict_result = coord_res.verdict_result
        risk_score = coord_res.risk_score
        triage_tier_evaluated = coord_res.triage_tier_evaluated
        tier_preemption_reason = coord_res.tier_preemption_reason
        allowlist_match_data = coord_res.allowlist_match_data
        homograph_analysis_data = coord_res.homograph_analysis_data
        slm_analysis_data = coord_res.slm_analysis_data
        extracted = coord_res.extracted_entities
        candidate_urls = coord_res.candidate_urls
        candidate_domains = coord_res.candidate_domains

        # 3.3 Database Known Malicious IoC Check Override (if not already RED)
        if verdict_result.verdict != TriageVerdict.RED and (candidate_urls or candidate_domains):
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
                            triage_tier_evaluated = "TIER_1_DETERMINISTIC"
                            tier_preemption_reason = f"Indicator matched verified malicious threat database: '{indicator}'"
                            break
            except Exception as exc:
                logger.debug("Database threat check skipped: %s", str(exc))

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

    # Determine inference engine provider label
    if triage_tier_evaluated == "TIER_2_NEURAL_ZEROGPU":
        active_engine = "Hugging Face ZeroGPU (NVIDIA A10G • Qwen2.5-3B + NeMo Guardrails)"
    elif triage_tier_evaluated == "TIER_2_NEURAL_LOCAL":
        active_engine = "Local Sovereign SLM Cluster (Guided JSON Generation)"
    elif triage_tier_evaluated == "TIER_3_OFFLINE_FALLBACK":
        active_engine = "Sovereign Deterministic Engine (Offline NLP Heuristics Fallback)"
    elif audio_analysis_data:
        active_engine = "Sovereign Acoustic Engine (Conformal Spectral Anomaly + Whisper ASR)"
    elif homograph_analysis_data:
        active_engine = "Deterministic Homograph & Unicode Punycode Detector"
    elif allowlist_match_data:
        active_engine = "Deterministic UAE Government Exact Domain Allowlist"
    else:
        active_engine = "Project Hares Sovereign Deterministic Engine"

    # Render 512MB RAM Protection & Memory Hygiene (Milestone 52)
    if "file_bytes" in locals():
        del file_bytes
    if "audio_bytes" in locals():
        del audio_bytes
    import gc
    gc.collect()

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
        model_engine=active_engine,
        triage_tier_evaluated=triage_tier_evaluated,
        tier_preemption_reason=tier_preemption_reason,
    )
