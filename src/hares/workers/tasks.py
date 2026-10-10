import logging
import time
import uuid
from decimal import Decimal
from typing import Any
from hares.ai.asr_client import LocalASRClient
from hares.ai.audio_classifier import AudioDeepfakeClassifier
from hares.ai.audio_pipeline import UnifiedAudioTriage
from hares.ai.audio_preprocessor import AudioDurationExceededError
from hares.ai.slm_client import LocalSLMClient
from hares.core.config import get_settings
from hares.core.security import derive_citizen_user_hash
from hares.db.repositories.allowlist_repo import AllowlistRepository
from hares.db.repositories.audit_repo import AuditRepository
from hares.db.repositories.threat_repo import ThreatRepository
from hares.db.session import sync_session_scope
from hares.engine.allowlist import AllowlistEngine
from hares.engine.homograph import HomographDetector
from hares.engine.sanitizer import EntityExtractor, PIIScrubber
from hares.engine.verdict import TriageVerdict, VerdictResult, VerdictSynthesizer
from hares.services.media_downloader import MediaDownloader
from hares.services.rate_limiter import RedisTokenBucketRateLimiter
from hares.services.whatsapp_client import WhatsAppClient
from hares.workers.celery_app import celery_app

logger = logging.getLogger("hares.workers")

# Engine & AI singletons for worker execution
allowlist_engine = AllowlistEngine()
homograph_detector = HomographDetector()
entity_extractor = EntityExtractor()
pii_scrubber = PIIScrubber()
verdict_synthesizer = VerdictSynthesizer()
rate_limiter = RedisTokenBucketRateLimiter()
unified_audio_triage = UnifiedAudioTriage()
audio_classifier = AudioDeepfakeClassifier()
asr_client = LocalASRClient()
slm_client = LocalSLMClient()
media_downloader = MediaDownloader()
whatsapp_client = WhatsAppClient()


def _get_active_allowlist_domains() -> set[str]:
    """Retrieves active official domains from database, falling back to cached seed domains."""
    try:
        with sync_session_scope() as session:
            domains = AllowlistRepository.get_active_domain_names_sync(session)
            if domains:
                allowlist_engine.update_domains(domains)
                return domains
    except Exception as exc:
        logger.debug("Database allowlist query unavailable, using in-memory engine: %s", str(exc))

    from hares.db.seed_data import OFFICIAL_UAE_DOMAINS_SEED
    seed_domains = {s["domain"].lower().strip() for s in OFFICIAL_UAE_DOMAINS_SEED}
    allowlist_engine.update_domains(seed_domains)
    return seed_domains


@celery_app.task(name="hares.process_incoming_webhook", queue="high_priority_triage", bind=True)
def process_incoming_webhook(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Background worker task handling WhatsApp payload processing out-of-band:
    1. Extracts ephemeral recipient phone for reply addressing.
    2. Derives citizen_user_hash via keyed HMAC-SHA256 (FR-4.1).
    3. Enforces token-bucket rate limiting (5 queries/hr per user hash, NFR-1.3).
    4. Evaluates media: audio voice notes (AASIST + Conformal + ASR) or text lures (Allowlist + SLM).
    5. Emits standardized tri-state verdict (🔴 RED, 🟡 AMBER, 🟢 GREEN).
    6. Dispatches outbound WhatsApp reply via WhatsAppClient.
    7. Persists Class A threat indicators & sanitized audit logs (zero citizen PII).
    8. Guaranteed in-memory purge of raw phone via try...finally (AUDIT-OBS-08).
    """
    settings = get_settings()
    processed_count = 0
    verdict_summaries: list[dict[str, Any]] = []

    try:
        entries = raw_payload.get("entry", [])
        active_domains = _get_active_allowlist_domains()

        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for msg in messages:
                    start_time = time.perf_counter()
                    raw_sender_phone = msg.get("from", "")
                    if not raw_sender_phone:
                        continue

                    # Volatile variable scope guarded by try...finally (AUDIT-OBS-08)
                    recipient_phone = raw_sender_phone
                    try:
                        # 1. Derive pseudonymized hash immediately (FR-4.1)
                        citizen_hash = derive_citizen_user_hash(raw_sender_phone, settings.CITIZEN_HASH_SALT)
                        msg_id = msg.get("id", str(uuid.uuid4()))
                        msg_type = msg.get("type", "unknown")
                        logger.info(
                            "Ingesting message id=%s from citizen_hash=%s type=%s",
                            msg_id,
                            citizen_hash[:12],
                            msg_type,
                        )

                        # 2. Check Token-Bucket Rate Limiter (NFR-1.3, AUDIT-OBS-07)
                        rl_result = rate_limiter.check_and_increment(citizen_hash)
                        if not rl_result.is_allowed:
                            logger.warning(
                                "Rate limit exceeded for citizen_hash=%s (count=%d/%d)",
                                citizen_hash[:12],
                                rl_result.current_count,
                                rl_result.max_allowed,
                            )
                            rate_limit_verdict = verdict_synthesizer.build_amber_verdict(
                                reason=f"Hourly query rate limit exceeded ({rl_result.max_allowed}/hour). Please retry later."
                            )
                            whatsapp_client.send_verdict_reply(recipient_phone, rate_limit_verdict)
                            verdict_summaries.append({
                                "message_id": msg_id,
                                "verdict": rate_limit_verdict.verdict.value,
                                "rule_triggered": "rate_limit_exceeded",
                            })
                            processed_count += 1
                            continue

                        assigned_verdict: VerdictResult | None = None
                        triggered_indicator: str | None = None
                        extracted_text = ""

                        # 3. Handle Audio Voice Notes (FR-1.x)
                        if msg_type in ["audio", "voice"]:
                            media_info = msg.get(msg_type, {})
                            media_id = media_info.get("id", "")
                            try:
                                audio_bytes, _ = media_downloader.fetch_media(media_id)

                                # 3.1 Unified Whisper Dual-Head Pipeline (Single Forward Pass: ASR + Deepfake Detection)
                                triage_res = unified_audio_triage.process(audio_bytes, f"{media_id}.ogg")
                                if triage_res.is_synthetic:
                                    assigned_verdict = verdict_synthesizer.build_red_verdict(
                                        rule_triggered="synthetic_deepfake_voice_detected",
                                        reason=f"Detected synthetic AI voice clone / deepfake audio (non-conformity={triage_res.non_conformity_score:.3f}, p={triage_res.p_value:.4f})",
                                        indicators=[f"audio:{media_id}"],
                                    )
                                    triggered_indicator = f"audio:{media_id}"
                                else:
                                    # Transcript extracted from the same Whisper forward pass
                                    extracted_text = triage_res.transcript_text
                            except AudioDurationExceededError as dur_exc:
                                logger.warning("Audio duration cap exceeded: %s", str(dur_exc))
                                assigned_verdict = verdict_synthesizer.build_amber_verdict(
                                    reason=f"Audio duration exceeds maximum limit of 120 seconds (FR-1.5). Please submit a shorter voice note."
                                )
                            except Exception as audio_err:
                                logger.error("Audio processing failed: %s", str(audio_err))
                                assigned_verdict = verdict_synthesizer.build_amber_verdict(
                                    reason="Voice note could not be processed due to audio format corruption or retrieval timeout."
                                )

                        # 4. Handle Text Messages
                        elif msg_type == "text":
                            extracted_text = msg.get("text", {}).get("body", "")

                        # 5. Text Sanitization, Entity Extraction & Deterministic Matching
                        if not assigned_verdict and extracted_text:
                            # Bound text length and scrub Class B PII (AUDIT-OBS-06, FR-4.2)
                            bounded_text = extracted_text[:4096]
                            scrubbed_text = pii_scrubber.scrub(bounded_text)

                            # Extract Class A threat entities
                            entities = entity_extractor.extract(scrubbed_text)
                            all_targets = list(dict.fromkeys(entities["urls"] + entities["domains"]))

                            # 5.1 Check Homograph and Punycode Spoofs (Highest Precedence: RED)
                            for target in all_targets:
                                is_spoof, spoof_reason = homograph_detector.check_spoof(target, active_domains)
                                if is_spoof:
                                    assigned_verdict = verdict_synthesizer.build_red_verdict(
                                        rule_triggered=spoof_reason,
                                        reason=f"Detected deceptive domain spoof targeting UAE entities ({target})",
                                        indicators=[target],
                                    )
                                    triggered_indicator = target
                                    break

                            # 5.2 Check Exact Registrable Domain Allowlist (GREEN)
                            if not assigned_verdict and all_targets:
                                allowlisted_match: str | None = None
                                for target in all_targets:
                                    if allowlist_engine.is_allowlisted(target):
                                        allowlisted_match = allowlist_engine.extract_registrable_domain(target)
                                        break

                                if allowlisted_match:
                                    assigned_verdict = verdict_synthesizer.build_green_verdict(
                                        entity_name="Verified Official UAE Registry Entity",
                                        verified_domain=allowlisted_match,
                                        indicators=all_targets,
                                    )
                                else:
                                    # External or novel links -> Default AMBER
                                    assigned_verdict = verdict_synthesizer.build_amber_verdict(
                                        reason="Extracted destination is not on the official UAE verified allowlist",
                                        indicators=all_targets,
                                    )

                            # 5.3 Small Language Model (SLM) Social Engineering Intent Evaluation (FR-2.4)
                            if not assigned_verdict or assigned_verdict.verdict == TriageVerdict.AMBER:
                                slm_result = slm_client.triage_text(scrubbed_text)
                                if (
                                    slm_result.is_impersonation
                                    and (slm_result.urgency_or_coercion or slm_result.financial_or_credential_demand)
                                    and slm_result.confidence_score >= 0.70
                                ):
                                    assigned_verdict = verdict_synthesizer.build_red_verdict(
                                        rule_triggered="slm_social_engineering_detected",
                                        reason=f"{slm_result.reasoning_summary} ({', '.join(slm_result.detected_tactics)})",
                                        indicators=all_targets or [f"text_lure:{msg_id[:8]}"],
                                    )
                                    triggered_indicator = (
                                        all_targets[0] if all_targets else f"text_lure:{msg_id[:8]}"
                                    )
                                elif not assigned_verdict:
                                    assigned_verdict = verdict_synthesizer.build_amber_verdict(
                                        reason=slm_result.reasoning_summary,
                                        indicators=all_targets,
                                    )

                        # Default fallback for unclassified inputs
                        if not assigned_verdict:
                            assigned_verdict = verdict_synthesizer.build_amber_verdict(
                                reason="No deterministic official indicator identified; proceed with caution",
                                indicators=[],
                            )

                        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

                        # 6. Dispatch Outbound WhatsApp Reply to Recipient (FR-3.1, FR-3.2)
                        whatsapp_client.send_verdict_reply(recipient_phone, assigned_verdict)

                        # 7. Persist Class A Indicators & Sanitized Telemetry
                        try:
                            with sync_session_scope() as session:
                                if assigned_verdict.verdict == TriageVerdict.RED and triggered_indicator:
                                    ThreatRepository.record_indicator_sync(
                                        session=session,
                                        indicator_type="domain" if "." in triggered_indicator else "lure",
                                        raw_indicator=triggered_indicator,
                                        normalized_value=triggered_indicator.lower().strip(),
                                        verdict="RED",
                                        risk_score=Decimal("0.9500"),
                                    )

                                AuditRepository.record_triage_audit_sync(
                                    session=session,
                                    request_id=uuid.uuid4(),
                                    citizen_user_hash=citizen_hash,
                                    payload_type=msg_type,
                                    triage_verdict=assigned_verdict.verdict.value,
                                    rule_triggered=assigned_verdict.rule_triggered,
                                    latency_ms=elapsed_ms,
                                )
                        except Exception as db_exc:
                            logger.debug("Database write skipped in offline/test context: %s", str(db_exc))

                        verdict_summaries.append({
                            "message_id": msg_id,
                            "verdict": assigned_verdict.verdict.value,
                            "rule_triggered": assigned_verdict.rule_triggered,
                            "latency_ms": elapsed_ms,
                        })

                        processed_count += 1
                    finally:
                        # 8. Guaranteed Ephemeral in-memory memory purge (AUDIT-OBS-08, FR-4.1)
                        if "recipient_phone" in locals():
                            del recipient_phone
                        if "raw_sender_phone" in locals():
                            del raw_sender_phone

        return {
            "status": "processed",
            "messages_handled": processed_count,
            "verdicts": verdict_summaries,
        }
    except Exception as exc:
        logger.error("Error processing incoming webhook payload: %s", str(exc), exc_info=True)
        raise self.retry(exc=exc, countdown=2, max_retries=3)
