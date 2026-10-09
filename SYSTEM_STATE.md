# SYSTEM_STATE.md — The Technical Blueprint of Project Hares

**Current Status:** Phase 1 Completed & Verified (Foundation Infrastructure, Cryptographic Security & Asynchronous Webhook Pipeline)  
**Last Updated:** 2026-10-09  
**Version:** 1.1.0-phase1-complete  

---

## 1. Active Ports & Services Architecture

| Service Name | Container / Process | Port | Binding | Protocol | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **FastAPI Gateway** | `hares-api` | `8000` | `0.0.0.0:8000` | HTTP/REST | WhatsApp Webhook Ingress (`/webhook`), Health Probes, Threat API |
| **Celery Worker** | `hares-worker` | N/A | Internal | AMQP/Redis | Asynchronous audio deepfake & text triage tasks (FR-3.3) |
| **Redis Broker/Cache**| `hares-redis` | `6379` | `127.0.0.1:6379` | RESP | Celery task message broker and citizen token-bucket rate limiter (NFR-1.3)|
| **PostgreSQL DB** | `hares-db` | `5432` | `127.0.0.1:5432` | TCP/PostgreSQL| Class A threat intelligence repository and audit logging |
| **Local SLM Service** | `hares-slm` | `11434` / `8001` | Internal | HTTP (vLLM/Ollama)| Local sovereign language model text triage (NFR-1.1) |
| **Next.js Dashboard** | `hares-dashboard` | `3000` | `0.0.0.0:3000` | HTTP | Municipal Threat Intelligence Portal (Analysts & Operations) |

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

---

## 5. Source Control & Repository State

* **Remote Origin:** `https://github.com/abdullah00ashraf/HARES.git`
* **Default Branch:** `main` (tracked and synchronized with `origin/main`)
* **Working Tree:** Clean, zero untracked runtime artifacts
* **Secret Protection:** Local `.env` and credentials strictly excluded via `.gitignore`
* **Commit History:** 8 conventional, semantic commits mapping each architectural layer

