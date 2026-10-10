# SYSTEM_STATE.md — The Technical Blueprint of Project Hares

**Current Status:** Datasets Populated & Verified (100K Text Smishing Instruction-Response Corpus & 20K WhatsApp 16kHz Opus Audio Deepfake Evaluation Suite)  
**Last Updated:** 2026-10-10  
**Version:** 1.7.0-datasets-populated  

---

## 1. Active Ports & Services Architecture

| Service Name | Container / Process | Port | Binding | Protocol | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FastAPI Gateway** | `hares-api` | `8000` | `0.0.0.0:8000` | HTTP/REST | WhatsApp Webhook Ingress (`/webhook`), Health Probes, Metrics (`/metrics`), Municipal Threat Feed API (`/api/v1/threats/*`) |
| **Celery Text Worker**| `hares-worker-text`| N/A | Internal | AMQP/Redis | Rapid text & URL triage tasks (<1.5s SLA) (`high_priority_triage`) |
| **Celery Media Worker**| `hares-worker-media`| N/A| Internal | AMQP/Redis | Audio deepfake transcoding & ASR inference (<4.5s SLA) (`media_triage`) (NVIDIA GPU Passthrough) |
| **Redis Broker/Cache**| `hares-redis` | `6379` | `127.0.0.1:6379` | RESP | Celery task message broker and citizen token-bucket rate limiter (NFR-1.3)|
| **PostgreSQL DB** | `hares-db` | `5432` | `127.0.0.1:5432` | TCP/PostgreSQL| Class A threat intelligence repository and audit logging |
| **Local SLM Service** | `hares-slm` | `11434` / `8001` | Internal | HTTP (vLLM/Ollama)| Local sovereign language model text triage (NFR-1.1) (NVIDIA GPU Passthrough) |
| **Prometheus Telemetry**| `hares-prometheus`| `9090` | `0.0.0.0:9090` | HTTP/Prometheus| High-frequency metrics scraping (5s interval) and SLA alerting |
| **Mock Meta Sink** | `mock-meta-sink` | `8001` | `0.0.0.0:8001` | HTTP/FastAPI | E2E turnaround tracking (Delta t = t_outbound - t_inbound) and synthetic media streaming |
| **Next.js Dashboard** | `hares-dashboard` | `3000` | `0.0.0.0:3000` | HTTP | Air-gapped Municipal Threat Intelligence Portal (Analysts & SOC) |

### Network Topologies & Egress Isolation
* **`hares_ingress` (External Ingress Bridge):** Connects `hares-api` with published port 8000:8000 and standard default gateway routing for Meta webhook deliveries and public API ingress/egress.
* **`hares_internal` (Non-Routable Bridge):** Connects all containers (`hares-api`, `hares-worker`, `hares-db`, `hares-redis`, `hares-slm`). `hares-db` and `hares-redis` reside exclusively on this network with zero external gateway routing and zero external internet access.
* **`hares_egress` (Egress-Restricted Bridge):** Connects `hares-worker` (and `hares-api`) with outbound HTTPS routing strictly to Meta WhatsApp endpoints (`*.facebook.com`, `*.fbsbx.com`) for two-stage media downloads and reply dispatch.

---

## 2. Environment Variables Specification

The application enforces strict configuration management via `pydantic-settings`. All values must be defined in `.env`:

```env
# ==========================================
# Application & Environment Settings
# ==========================================
PROJECT_NAME="Project Hares"
ENVIRONMENT="development"  # development | staging | production
DEBUG=false
LOG_LEVEL="INFO"
SECRET_KEY="<cryptographically-secure-random-string-min-32-chars>"

# ==========================================
# Meta WhatsApp Business Cloud API Settings
# ==========================================
WHATSAPP_API_VERSION="v21.0"
WHATSAPP_PHONE_NUMBER_ID="<meta-assigned-phone-number-id>"
WHATSAPP_BUSINESS_ACCOUNT_ID="<meta-business-account-id>"
WHATSAPP_ACCESS_TOKEN="<system-user-access-token-with-whatsapp-business-messaging-permission>"
WHATSAPP_VERIFY_TOKEN="<custom-secret-string-for-get-webhook-challenge>"
WHATSAPP_APP_SECRET="<meta-app-secret-for-payload-hmac-sha256-verification>"
WHATSAPP_API_BASE_URL="https://graph.facebook.com"
WHATSAPP_LOCAL_STORAGE_REGION="UAE"

# ==========================================
# Security & Privacy (FR-4.1 & NFR-1.3)
# ==========================================
CITIZEN_HASH_SALT="<cryptographically-random-salt-minimum-32-bytes-hex>"
RATE_LIMIT_QUERIES_PER_HOUR=5
RATE_LIMIT_WINDOW_SECONDS=3600

# ==========================================
# Database & Persistence (PostgreSQL)
# ==========================================
POSTGRES_USER="hares_admin"
POSTGRES_PASSWORD="<strong-database-password>"
POSTGRES_DB="hares_threat_db"
POSTGRES_HOST="db"
POSTGRES_PORT=5432
DATABASE_URL="postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"
DATABASE_URL_SYNC="postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"

# ==========================================
# Queue & Caching (Redis)
# ==========================================
REDIS_HOST="redis"
REDIS_PORT=6379
REDIS_PASSWORD="<strong-redis-password>"
REDIS_DB=0
REDIS_URL="redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}"
CELERY_BROKER_URL="redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/1"
CELERY_RESULT_BACKEND="redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/2"
REDIS_EPHEMERAL_PAYLOAD_TTL_SECONDS=60  # Ephemeral transit queue TTL for outbound reply routing (FR-4.1)

# ==========================================
# Local AI Sovereign Inference (NFR-1.1)
# ==========================================
SLM_INFERENCE_ENDPOINT="http://slm:11434/api/generate"
SLM_MODEL_NAME="llama3.2:3b-instruct-q4_K_M"
AUDIO_MODEL_CHECKPOINT_PATH="/models/audio/aasist_opus_calibrated.pt"
AUDIO_CONFORMAL_THRESHOLD=0.85
MAX_AUDIO_DURATION_SECONDS=120
```

---

## 3. Database Schema Map

```
+--------------------------------------------------------------------------+
|                            TABLE: official_domains                       |
|   (Curated Registrable Domain Exact Allowlist - FR-2.2)                  |
+--------------------------------------------------------------------------+
| id                  : UUID (PK)                                          |
| domain              : VARCHAR(255) (UNIQUE, INDEX)                       |
| entity_name         : VARCHAR(255)                                       |
| entity_type         : VARCHAR(50) (government, utility, banking, telecom)|
| verified_owner      : VARCHAR(255)                                       |
| quarterly_review_at : TIMESTAMP WITH TIME ZONE                           |
| is_active           : BOOLEAN (DEFAULT TRUE)                             |
| created_at          : TIMESTAMP WITH TIME ZONE                           |
+--------------------------------------------------------------------------+

+--------------------------------------------------------------------------+
|                            TABLE: threat_indicators                     |
|   (Class A Indicators of Compromise - Persisted Indefinitely - FR-4.1)   |
+--------------------------------------------------------------------------+
| id                  : UUID (PK)                                          |
| indicator_type      : VARCHAR(50) (url, domain, phone, crypto_wallet)    |
| raw_indicator       : TEXT                                               |
| normalized_value    : VARCHAR(512) (INDEX)                               |
| verdict             : VARCHAR(20) (red, amber, green)                    |
| risk_score          : NUMERIC(5, 4)                                      |
| occurrence_count    : INTEGER (DEFAULT 1)                                |
| campaign_id         : UUID (FK -> threat_campaigns.id, NULLABLE)         |
| first_seen_at       : TIMESTAMP WITH TIME ZONE                           |
| last_seen_at        : TIMESTAMP WITH TIME ZONE                           |
+--------------------------------------------------------------------------+

+--------------------------------------------------------------------------+
|                            TABLE: threat_campaigns                      |
|   (Aggregated Campaign Telemetry for Municipal Analysts - FR-4.3)        |
+--------------------------------------------------------------------------+
| id                  : UUID (PK)                                          |
| name                : VARCHAR(255)                                       |
| lure_type           : VARCHAR(50) (traffic_fine, parcel, utility, voice) |
| target_entity_spoofed: VARCHAR(255)                                      |
| status              : VARCHAR(50) (active, disrupted, monitoring)        |
| total_submissions   : INTEGER (DEFAULT 0)                                |
| created_at          : TIMESTAMP WITH TIME ZONE                           |
| updated_at          : TIMESTAMP WITH TIME ZONE                           |
+--------------------------------------------------------------------------+

+--------------------------------------------------------------------------+
|                            TABLE: triage_audit_log                       |
|   (Sanitized Performance & Audit Log - ZERO Citizen PII - FR-4.1)        |
+--------------------------------------------------------------------------+
| id                  : UUID (PK)                                          |
| request_id          : UUID (UNIQUE)                                      |
| citizen_user_hash   : VARCHAR(64) (INDEX) [HMAC-SHA256 with rotatable salt|
| payload_type        : VARCHAR(20) (text, url, audio_voice_note)          |
| triage_verdict      : VARCHAR(20) (RED, AMBER, GREEN)                    |
| rule_triggered      : VARCHAR(100) (allowlist_match, idn_homograph, etc.)|
| processing_time_ms  : INTEGER                                            |
| created_at          : TIMESTAMP WITH TIME ZONE                           |
+--------------------------------------------------------------------------+
```

---

## 4. Phase 1 Implemented Components & Test Verification

| Module / Component | Path | Invariant / Requirement Satisfied | Status |
| :--- | :--- | :--- | :--- |
| **Packaging & Config** | `pyproject.toml`, `README.md` | Python 3.11+, setuptools, dependencies pinned | Verified & Active |
| **Pydantic Settings** | `src/hares/core/config.py` | Pydantic v2 BaseSettings, salt entropy validation | Verified & Active |
| **Cryptographic Security** | `src/hares/core/security.py` | Meta HMAC-SHA256 constant-time check, citizen hashing (FR-4.1) | Verified (100% tests passing) |
| **Container Topology** | `Dockerfile`, `docker-compose.yml` | Multi-stage build, tri-network bridge (`hares_ingress`, `hares_internal`, `hares_egress`) | Compose validated |
| **FastAPI Ingress Gateway**| `src/hares/main.py`, `src/hares/api/v1/health.py`, `src/hares/api/v1/webhook.py` | Sub-50ms SLA, security headers middleware, liveness/readiness | Verified (100% tests passing) |
| **Celery Worker Pipeline** | `src/hares/workers/celery_app.py`, `src/hares/workers/tasks.py` | `high_priority_triage` queue routing, ephemeral memory purge (`del recipient_phone`) | Verified (100% tests passing) |
| **Hermetic Test Suite** | `tests/conftest.py`, `tests/test_security.py`, `tests/test_webhook.py`, `tests/test_tasks.py` | 11 automated unit tests verifying signature, challenge, webhook post, and worker task | 11/11 tests PASSED (100%) |
| **Security Audit Skill** | `.agents/skills/security-audit/` | Cloudflare defensive source-first vulnerability audit skill suite (20 assets) | Integrated & Active |
| **Audit 1 Report & Ledger** | `audit/audit_1.md`, `audit/audit_1.json` | Formal read-only security & architectural reconnaissance audit (100% invariant compliance) | Verified & Active |
| **Deterministic Allowlist** | `src/hares/engine/allowlist.py` | Exact registrable domain extraction & allowlisting (`tldextract`) (FR-2.2) | Verified (100% tests passing) |
| **Homograph & Punycode** | `src/hares/engine/homograph.py` | `.امارات` ccTLD check, Arabic Unicode regex, normalized Levenshtein (FR-2.3) | Verified (100% tests passing) |
| **Sanitizer & PII Scrubber** | `src/hares/engine/sanitizer.py` | Entity extraction & Class B bilingual PII redaction (FR-4.1, FR-4.2) | Verified (100% tests passing) |
| **Verdict Synthesizer** | `src/hares/engine/verdict.py` | Tri-state classification (RED/AMBER/GREEN) & Dubai Police escalation (FR-3.1, FR-3.2) | Verified (100% tests passing) |
| **SQLAlchemy 2.0 ORM** | `src/hares/db/models.py` | `official_domains`, `threat_indicators`, `threat_campaigns`, `triage_audit_log` (Uuid) | Verified (100% tests passing) |
| **Database Sessions** | `src/hares/db/session.py` | Async (`asyncpg`) and sync (`psycopg2`/SQLite) session factories with connection pooling | Verified & Active |
| **Database Repositories** | `src/hares/db/repositories/` | `AllowlistRepository`, `ThreatRepository`, `AuditRepository`, UAE seeds | Verified (100% tests passing) |
| **Token-Bucket Rate Limiter**| `src/hares/services/rate_limiter.py` | Redis atomic token-bucket rate limiter (5 req/hr per citizen hash) (NFR-1.3) | Verified (100% tests passing) |
| **Worker Pipeline Integration**| `src/hares/workers/tasks.py` | End-to-end deterministic verification, PII scrubbing, audit logging & memory purge | Verified (100% tests passing) |
| **Sovereign AI Schemas** | `src/hares/ai/schemas.py` | Pydantic v2 schemas for SLM text triage, audio deepfakes, ASR, and UnifiedAudioTriageResult | Verified (100% tests passing) |
| **Conformal Calibration** | `src/hares/ai/conformal.py` | Non-parametric conformal p-values, FPR <= 0.1% bound, tri-band abstention (FR-1.4, NFR-3.1) | Verified (100% tests passing) |
| **Audio Preprocessor & Opus Normalizer** | `src/hares/ai/audio_preprocessor.py` | 16kHz mono PCM normalization via ffmpeg-python, WhatsApp Opus simulation, 120s duration cap (FR-1.3, FR-1.5) | Verified (100% tests passing) |
| **Unified Whisper Dual-Head Pipeline** | `src/hares/ai/audio_pipeline.py` | Single forward pass Whisper ASR + PyTorch WhisperDeepfakeMLPHead spoof detector, saving ~3.5GB VRAM and ~180ms latency (FR-1.1, FR-3.3) | Verified (100% tests passing) |
| **Whisper Deepfake MLP Head** | `src/hares/ai/audio_pipeline.py` | piotrkawa Interspeech 2023 architecture: LayerNorm, adaptive pooling, 3-layer MLP projection | Verified (100% tests passing) |
| **Audio Deepfake Classifier**| `src/hares/ai/audio_classifier.py` | AASIST acoustic anomaly detection with conformal risk evaluation (FR-1.2, FR-1.3) | Verified (100% tests passing) |
| **High-Throughput ASR** | `src/hares/ai/asr_client.py` | Sub-350ms speech-to-text engine with multilingual detection (FR-1.1, NFR-2.1) | Verified (100% tests passing) |
| **Guided SLM Client** | `src/hares/ai/slm_client.py` | Local SLM client with Outlines FSM guided decoding & anti-prompt-injection isolation (FR-2.4, NFR-1.3) | Verified (100% tests passing) |
| **Open-Source Asset Registry**| `opensource/` | 11 synchronized upstream git repos, 5 benchmark evaluation datasets, and 3 model profiles | Verified (100% synchronized) |
| **Two-Stage Media Fetcher** | `src/hares/services/media_downloader.py` | Two-stage WhatsApp Cloud API media retriever (GET /media_id + GET binary stream) | Verified (100% tests passing) |
| **WhatsApp Outbound Dispatch**| `src/hares/services/whatsapp_client.py` | Outbound WhatsApp client with official Dubai Police e-Crime escalation (FR-3.1, FR-3.2) | Verified (100% tests passing) |
| **Threat Feed API** | `src/hares/api/v1/threat_feed.py` | Municipal Class A IoC feeds, campaigns, homographs, STIX 2.1 & CSV exports with ECDSA SECP256R1 signatures (FR-4.3, AUDIT-OBS-16) | Verified (100% tests passing) |
| **Analyst Security Dep** | `src/hares/api/deps.py` | Municipal analyst API key validation with 120 req/min rate limiter (AUDIT-OBS-14) | Verified (100% tests passing) |
| **Active Health Readiness** | `src/hares/api/v1/health.py` | Active SELECT 1 on DB & PING on Redis (AUDIT-OBS-10) emitting 503 if down | Verified (100% tests passing) |
| **Media CDN SSRF Shield** | `src/hares/services/media_downloader.py` | Meta CDN hostname verification against malicious SSRF injection (AUDIT-OBS-11) | Verified (100% tests passing) |
| **Queue Worker Partitioning**| `src/hares/workers/celery_app.py` | Dedicated worker process pools for text vs media queues (AUDIT-OBS-12) | Verified (100% tests passing) |
| **Phone Sanitizing Filter** | `src/hares/core/logging.py` | Global logging filter scrubbing telephone numbers from logs and tracebacks (AUDIT-OBS-13) | Verified (100% tests passing) |
| **Next.js 15 Portal** | `frontend/` | 100% air-gapped zero-SaaS operations portal with decoupled 60 FPS HTML5 Canvas | Verified (Build succeeds) |
| **Prometheus Telemetry**| `src/hares/core/metrics.py` | OpenMetrics `/metrics` endpoint, custom histograms for ingress, E2E turnaround, and queue equilibrium | Verified (100% tests passing) |
| **Production GPU Topology**| `docker-compose.prod.yml` | Multi-container compose with NVIDIA GPU passthrough for Whisper/AASIST & vLLM, dual Celery pools | Verified (`docker compose config` valid) |
| **Mock Meta Egress Sink** | `benchmarks/mock_meta_sink.py` | Standalone FastAPI sink tracking E2E latency Delta t = t_outbound - t_inbound and serving synthetic Opus media | Verified (100% tests passing) |
| **Locust 200 QPS Harness** | `benchmarks/locustfile.py` | Pure Python load generator with 85/15 text/audio split, nanosecond timestamps, and dynamic HMAC signatures | Verified (100% tests passing) |
| **Benchmark Orchestrator**| `benchmarks/run_stress_test.py` | Stepped load runner (50 -> 100 -> 200 QPS) and automated SLA markdown report generator | Verified (CLI runs cleanly) |
| **Hermetic Test Suite (v6)** | `tests/` | 89 automated unit & integration tests across security hardening, Prometheus metrics, concurrent load benchmarks, AI, media, and threat feeds | 89/89 tests PASSED (100%) |
| **UAE Smishing Corpus (100K)**| `opensource/datasets/localized_fraud_corpus/` | 100,000 paired ChatML records (87.72 MB), 40% Emirati, 30% MSA, 20% Expat English, 10% Arabizi; 70% Malicious, 30% Benign | Verified (Schema validated) |
| **Audio Deepfake Suite (20K)**| `opensource/datasets/synthetic_voice_eval/` | 20,000 files (19.99 hrs), 16 kHz mono Opus (.ogg), 50% Genuine (CV Arabic, English, Urdu) / 50% Synthetic (F5-TTS, CosyVoice, XTTS-v2, ElevenLabs) | Verified (100% encoded) |

---

## 5. Source Control & Repository State

* **Remote Origin:** `https://github.com/abdullah00ashraf/HARES.git`
* **Default Branch:** `main` (tracked and synchronized with `origin/main`)
* **Working Tree:** Clean, zero untracked runtime artifacts
* **Secret Protection:** Local `.env` and credentials strictly excluded via `.gitignore`
* **Commit History:** 15 conventional, semantic commits mapping each architectural layer (Latest: `32ded09` covering Milestone 22 local dataset population: 100K ChatML smishing records and 20K WhatsApp 16 kHz mono Opus deepfake evaluation suite)
* **Remote Sync Status:** Fully synchronized with `origin/main` at `32ded09`

---

## 6. Formal Security & Architectural Audits

| Audit ID | Timestamp (UTC) | Scope / Focus | Framework | Verdict | Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AUDIT-001-PHASE1-RECON** | 2026-10-10 03:33:01 UTC | Phase 1 Foundation, Invariants, Ingress Gateway, Queue Pipeline & Tri-Network Docker | Cloudflare Security Audit Skill & Master Orchestrator | **PASSED WITH OBSERVATIONS** (11/11 tests pass) | [`audit/audit_1.md`](audit/audit_1.md), [`audit/audit_1.json`](audit/audit_1.json) |
| **AUDIT-002-PHASE2-DETERMINISTIC** | 2026-10-10 04:10:00 UTC | Phase 2 Deterministic Verification Engine, PostgreSQL Persistence Tier, Rate Limiting & Webhook Hardening | Cloudflare Security Audit Skill & Master Orchestrator | **PASSED WITH OBSERVATIONS** (32/32 tests pass) | [`audit/audit_2.md`](audit/audit_2.md), [`audit/audit_2.json`](audit/audit_2.json) |
| **AUDIT-003-PHASE3-SOVEREIGN-AI** | 2026-10-10 04:45:00 UTC | Phase 3 Local Sovereign AI Inference Cluster, Media Pipeline, AASIST Deepfake Detector, Conformal Engine & Hardening | Cloudflare Security Audit Skill & Master Orchestrator | **PASSED WITH OBSERVATIONS** (58/58 tests pass) | [`audit/audit_3.md`](audit/audit_3.md), [`audit/audit_3.json`](audit/audit_3.json) |
| **AUDIT-004-PHASE4-MUNICIPAL-DASHBOARD** | 2026-10-10 05:30:00 UTC | Phase 4 Municipal Threat Intelligence Feed, STIX 2.1 Export, Next.js 15 Analyst Dashboard, and Hardening Remediations | Cloudflare Security Audit Skill & Master Orchestrator | **PASSED WITH OBSERVATIONS** (69/69 tests pass) | [`audit/audit_4.md`](audit/audit_4.md), [`audit/audit_4.json`](audit/audit_4.json) |
| **AUDIT-005-PHASE5-SOVEREIGN-AI-AND-MEDIA** | 2026-10-10 07:15:00 UTC | Phase 5 Sovereign AI Integration, Unified Whisper Dual-Head Pipeline, Audio Opus Normalizer, Conformal Statistical Calibration, Local SLM Guided Decoding, and Open-Source Asset Registry | Cloudflare Security Audit Skill & Master Orchestrator | **PASSED WITH OBSERVATIONS** (77/77 tests pass) | [`audit/audit_5.md`](audit/audit_5.md), [`audit/audit_5.json`](audit/audit_5.json) |
| **AUDIT-006-PHASE6-PRODUCTION-HARDENING** | 2026-10-10 07:55:00 UTC | Phase 6 Production Hardening, Multi-Container GPU Orchestration, Observability, STIX Signing, and 200 QPS Load Benchmark | Cloudflare Security Audit Skill & Master Orchestrator | **PASSED WITH OBSERVATIONS** (89/89 tests pass) | [`audit/audit_6.md`](audit/audit_6.md), [`audit/audit_6.json`](audit/audit_6.json) |

---

## 7. Sovereign Dataset Registries & Evaluation Benchmarks

| Corpus / Benchmark Name | Local Filesystem Location | Volume | Format / Profile | Split & Class Distribution | Purpose / Invariants |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **UAE Smishing & Social Engineering Corpus** | `opensource/datasets/localized_fraud_corpus/` | 100,000 records (87.72 MB) | ChatML JSONL (`uae_smishing_100k.jsonl`) conforming to `TextTriageInferenceResult` | 40% Emirati Gulf, 30% MSA, 20% Expat English, 10% Arabizi; 70% Malicious, 30% Benign | Instruction-tuning and evaluating sovereign local SLMs for UAE fraud triage with zero offshore API dependencies |
| **Audio Deepfake & Acoustic Artifact Suite** | `opensource/datasets/synthetic_voice_eval/` | 20,000 files (100% 16 kHz Mono Opus .ogg) | WhatsApp Opus profile (16-24 kbps VBR), 10 shards/class (`audio/genuine/`, `audio/synthetic/`) | 50% Genuine (Common Voice Arabic Gulf/MSA, English, Urdu) / 50% Synthetic (F5-TTS, CosyVoice, XTTS-v2, ElevenLabs) | Rigorous training and conformal calibration of AASIST and Whisper dual-head spoof detection under real WhatsApp compression |
| **Audio Corpus Manifest & Streaming Index** | `opensource/datasets/synthetic_voice_eval/` | 20,000 entries | `audio_metadata.jsonl`, `audio_corpus_manifest.json` | Cataloged by file ID, duration, SNR, dialect, vocoder family, and specific acoustic artifacts | Continuous auditability, benchmark reproducibility, and automated evaluation pipeline ingestion |







