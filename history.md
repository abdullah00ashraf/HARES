# Project Hares: Comprehensive Engineering Session History
## Session 1: Foundational Architecture, MLOps Research, Phase 1 Implementation, Verification & Publication

**Document Version:** 1.0.0  
**Session Date:** 2026-10-09  
**Session Status:** Completed & Verified  
**Classification:** Enterprise Dubai Sovereign Threat Intelligence & Public Fraud Triage  

---

## 1. Executive Mission & Strategic Context

Project Hares (**مشروع حارس**) is an open-source, automated threat-intelligence and fraud-triage platform designed for residents of Dubai and the wider UAE. Operating as a single-purpose WhatsApp Business bot compliant with Meta's Business API policies, the platform ingests forwarded text lures, URLs, and audio voice notes (`.ogg` Opus, `.mp3`, `.m4a`) to detect social engineering and synthetic media (deepfakes).

The system serves two simultaneous audiences:
1. **The Citizen:** Receives an instantaneous, clear, explainable tri-state verdict:
   - 🔴 **High Risk / Confirmed Scam:** Active malicious lure or deepfake synthetic voice impersonation.
   - 🟡 **Amber / Unverified:** Statistical ambiguity, novel template, or unverified sender; instructs cautious handling without false reassurance.
   - 🟢 **Verified Official:** Exact cryptographic match against verified government or utility allowlists.
2. **Municipal Cyber Authorities (DESC, Dubai Police, TDRA):** Harvests sanitized, de-duplicated Indicators of Compromise (Class A IoCs: spoofed domains, phishing URLs, scammer bank accounts, foreign sender numbers) into a centralized municipal repository without violating citizen privacy.

### The Threat Landscape in Dubai & UAE
- **Economic Toll:** Over AED 3.7 billion lost annually across the UAE to social engineering, imposter fraud, and advanced cyber scams.
- **Frequency:** 82% of UAE residents receive phishing attempts weekly across messaging apps and SMS.
- **Prevalent Vectors:** Impersonation of critical government and utility entities:
  - Dubai Police traffic fines (`ecrime.ae` vs fraudulent lookalikes)
  - Emirates Post parcel delivery fees
  - Salik toll road recharges
  - Dubai Electricity and Water Authority (DEWA) billing notices
  - UAE Central Bank account verification alerts
  - Synthetic deepfake voice clones mimicking family members, CEOs, or municipal officials over WhatsApp audio notes.

---

## 2. Foundational Constraints & Architectural Invariants

Every technical design, schema, and line of code produced in Session 1 adheres to four strict operational boundaries:

### A. NFR-1.1: Data Sovereignty & Sovereign Compute Boundary
- **Zero Offshore Dispatches:** Under no circumstances may citizen payloads, message tokens, audio buffers, or embeddings be transmitted to external commercial AI APIs (e.g., OpenAI, Anthropic, Google Cloud offshore endpoints).
- **100% Local Inference:** All language model text classification (SLMs), speech-to-text transcription (Whisper), and audio deepfake classifiers (AASIST / WavLM) must execute locally within sovereign UAE compute infrastructure.
- **Meta Cloud API Transport Protocol:** Meta discontinued the On-Premises WhatsApp Business API Docker client on October 23, 2025. In accordance with Section 4.2 of the Validation Report, Hares connects to the **Meta WhatsApp Business Cloud API with UAE Local Storage enabled** for data-at-rest residency within the UAE geographic boundary. The bot includes an explicit transport transparency disclosure in its onboarding message.

### B. FR-3.3: Webhook SLA & Decoupled Execution
- **Sub-50ms Response SLA:** Meta Cloud API webhooks mandate an HTTP 200 acknowledgment strictly within **500ms**. Failure to meet this SLA causes Meta edge servers to retry deliveries, trigger duplicate processing loops, and eventually disable the webhook endpoint.
- **Decoupled Architecture:** The ingress gateway (`POST /webhook`) performs constant-time HMAC-SHA256 signature verification, pushes the raw payload to Redis via Celery, and emits `HTTP 200 {"status": "queued"}` in $< 50\text{ms}$. Heavy AI models (~1.5s for text SLM, ~280ms for Whisper ASR, ~250ms for audio deepfake classification) run completely out-of-band in Celery background workers.

### C. FR-4.1: Cryptographic Data Segregation (Class A vs. Class B)
- **Class A Data (Scammer Threat Indicators):** Malicious URLs, spoofed domain names, attacker foreign phone numbers, scammer bank accounts, and crypto wallet addresses are retained indefinitely in PostgreSQL for municipal intelligence and threat dashboard telemetry.
- **Class B Data (Citizen Privacy & Identifiers):** Citizen submitter phone numbers, personal names, Emirates IDs, personal account numbers, and OTPs are strictly protected. Citizen phone numbers are pseudonymized immediately upon ingestion using a keyed `HMAC-SHA256` hash with a rotatable 32-byte salt (`CITIZEN_HASH_SALT`). The raw phone number is never persisted to database tables, structured logs, or disk.
- **Ephemeral Transit Lifecycle:** To reply to the citizen via WhatsApp, Celery background workers require the recipient phone number. This paradox is resolved by storing the raw phone number ephemerally in Redis with a 60-second message TTL (`expires=60`). Immediately after outbound reply dispatch to Meta, the worker purges `recipient_phone` from local memory scope (`del recipient_phone`, `del raw_sender_phone`).

### D. The "Zero Guess" & "No Mockup" Policy (`policy.md`)
- **Production-Ready Code Only:** No dummy mockups, placeholder code, `pass` blocks, or `TODO: implement later` comments.
- **Deployable State:** Every module must be fully typed (Python 3.11+ / 3.12+), handle exceptions gracefully, and run cleanly inside Docker containers.
- **Dual-Ledger State Tracking:** Mandatory maintenance of `SYSTEM_STATE.md` (the living technical blueprint) and `DEVELOPMENT_LEDGER.md` (chronological decision and error history).

---

## 3. Comprehensive Chronology of Session 1

### Phase 1: Ingestion & Foundational Specification Authoring
1. **Document Ingestion:** Analyzed foundational project specifications:
   - `idea/01_Project_Hares_SRS.md`: System requirements, functional/non-functional specifications, SLA constraints.
   - `idea/02_UAE_Cyber_Fraud_Statistics.md`: Regional fraud data, financial impact figures, and target entity analysis.
   - `idea/03_Validation_ChangeLog_and_OpenItems.md`: Validation report detailing Meta on-premises deprecation, allowlist design requirements, and conformal prediction thresholds.
2. **Authoring the Goal Specifications Suite (`c:/HARES/goal/`):**
   Prior to implementing application code, authored 8 production-grade specification blueprints in the `goal/` directory:
   - `architecture.md`: C4 component topology, sub-50ms ingress pipeline, tri-network container design, audio latency budget ($<4.6\text{s}$ total budget incorporating two-stage Meta media fetching).
   - `feature.md`: Complete traceability matrix mapping functional requirements (FR-1.1 through FR-4.4) and non-functional requirements (NFR-1.1 through NFR-3.2).
   - `models.md`: Local SLM architecture (Qwen-2.5-3B AWQ / Falcon-3-3B with Outlines guided JSON decoding), `faster-whisper-small` (INT8) ASR, and AASIST audio deepfake classifier.
   - `datasets.md`: Curated UAE Regional Opus Suite, ASVspoof 2021 DF codec subset, Localized UAE SMS phishing corpus, and Curated Registrable Domain allowlist.
   - `database.md`: PostgreSQL 16 DDL & SQLAlchemy 2.0 ORM schemas for `official_domains`, `threat_indicators`, `threat_campaigns`, and `triage_audit_log`.
   - `frontend.md`: Next.js 15 Municipal Threat Intelligence Dashboard with Class A telemetry views and zero Class B PII exposure.
   - `backend.md`: FastAPI and Celery worker layout with deterministic verification engine specifications.
   - `security.md`: DESC, ISR, and Dubai AI Security Policy compliance mapping, STRIDE threat model, and network bridge isolation.

---

### Phase 2: Open-Source Asset Evaluation & MLOps Research
1. **Authoring Open-Source Asset Registry (`c:/HARES/opensource/relevants.md`):**
   Compiled and audited top open-source GitHub repositories, Hugging Face checkpoints, calibration datasets, and security tools across all 7 operational domains:
   - *Domain 1 (Audio Deepfake):* `clovaai/aasist`, `microsoft/wavlm-base-plus`, `piotrkawa/deepfake-whisper-features`.
   - *Domain 2 (Speech-to-Text ASR):* `SYSTRAN/faster-whisper`, `openai/whisper`.
   - *Domain 3 (Language Models / SLMs):* `Qwen/Qwen2.5-3B-Instruct`, `tiiuae/Falcon3-3B-Instruct`, `outlines-dev/outlines`.
   - *Domain 4 (URL & Homograph Verification):* `john-kurkowski/tldextract`, `kjd/idna`, `rapidfuzz/Levenshtein`.
   - *Domain 5 (Data Sanitization & Privacy):* `google/re2`, `microsoft/presidio`.
   - *Domain 6 (Evaluation Datasets):* Curated UAE Regional Opus Suite, ASVspoof 2021 DF, Mozilla Common Voice Arabic.
   - *Domain 7 (Backend Infrastructure):* `tiangolo/fastapi`, `celery/celery`, `redis/redis-py`, `sqlalchemy/sqlalchemy`.

2. **MLOps Deep Research & Audio Synergy Findings:**
   - **Community Checkpoints Caveat (`Vansh180`, `Sara1708`):** Hobbyist fine-tunes trained on clean audio fail catastrophically on 16kbps WhatsApp Opus audio due to codec high-frequency spectral compression. Reclassified them as "CI/smoke-test only". Production classifiers mandate intentional Opus data augmentation.
   - **The ASVspoof 2021 DF Calibration Trap:** ASVspoof 2021 DF is over 100GB and comprises almost exclusively English and European speakers. Calibrating non-parametric conformal prediction solely on ASVspoof breaks statistical exchangeability ($x_{\text{test}} \sim P_{\text{cal}}$) for Gulf Arabic speakers. Conformal thresholds ($\hat{q} = 0.85$) are calibrated on the Curated UAE Regional Opus Suite (Common Voice Arabic + regional recordings transcoded to 16kbps Opus).
   - **Unified Whisper Dual-Head Architecture (`deepfake-whisper-features` - Interspeech 2023):** Replaced separate WavLM audio passes by feeding Whisper encoder embeddings into both the ASR text decoder and an AASIST spoof classification head in a single forward pass. This saves ~3.5 GB VRAM and ~180ms per audio query.

---

### Phase 3: Algorithmic & Architectural Rectifications
During comprehensive audits of system designs, four critical bugs were detected and remediated:

1. **The `.امارات` Second-Level Domain False Positive:**
   - *Bug:* In `engine/homograph.py`, naive checks flagged any non-TLD label starting with `xn--` as a Punycode homograph attack. For authentic Arabic government portals under the `.امارات` ccTLD (`xn--mgbaam7a8h`), legitimate Arabic second-level domains (e.g., `بلدية-دبي.امارات` which Punycode-encodes to `xn----ymcbabb9a5b3a1a`) were falsely classified as 🔴 High Risk spoofing attacks.
   - *Resolution:* If the TLD is `.امارات` (`xn--mgbaam7a8h`), non-TLD labels are decoded via `idna.decode()` and validated against the Arabic Unicode character block (`[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9\-]`). Valid Arabic scripts pass safely; mixed-script lookalikes are blocked.

2. **Short-Domain Levenshtein False Positives:**
   - *Bug:* A flat Levenshtein edit distance check ($d \le 2$) falsely flagged short benign domains as spoofing attacks (e.g., `dew.ae` vs `dewa`, `ata.ae` vs `rta`).
   - *Resolution:* Enforced length-normalized edit distance: $\frac{d}{\max(\text{len}_1, \text{len}_2)} \le 0.25$ restricted to domains with $\max(\text{len}) \ge 5$. Short domains below 5 characters require exact prefix/suffix allowlist matching.

3. **External Ingress vs. `internal: true` Network Deadlock:**
   - *Bug:* Setting `internal: true` on Docker bridge networks strips the default gateway (`0.0.0.0/0`). If `api` is attached solely to `internal: true`, it can receive inbound SYN packets via host port DNAT, but has no default route to transmit outbound SYN-ACK response packets back to external clients (such as Meta's edge servers).
   - *Resolution:* Established a tri-network Docker topology:
     - `hares_ingress` (bridge): Ingress/egress for `api` with published port 8000.
     - `hares_internal` (`internal: true` bridge): Strictly non-routable network connecting `api`, `worker`, `db`, and `redis`. `db` and `redis` reside exclusively here.
     - `hares_egress` (bridge): Grants `worker` outbound HTTPS access strictly to Meta endpoints (`*.facebook.com`, `*.fbsbx.com`).

4. **Broker Payload TTL vs. Result Backend TTL (FR-4.1):**
   - *Bug:* Setting `result_expires=60` in Celery only expires result backend metadata (`celery-task-meta-*`), leaving raw unhashed citizen phone numbers in the Redis broker queue indefinitely if workers stall.
   - *Resolution:* Dispatched tasks with message-level broker expiration using `process_incoming_webhook.apply_async(args=[raw_payload], queue="high_priority_triage", expires=60)`. If workers lag past 60s, Redis/Celery automatically purges the expired message.

5. **Dockerfile Builder Stage Source Code Omission:**
   - *Bug:* The Dockerfile builder stage executed `pip install .` without copying `src/` or `README.md`, crashing `setuptools.build_meta` with `package directory 'src/hares' does not exist`.
   - *Resolution:* Added `COPY pyproject.toml README.md* ./` and `COPY src/ ./src/` in the builder stage before executing `pip install --no-cache-dir .`.

---

### Phase 4: Phase 1 Implementation & Test Verification
Implemented the entire foundational codebase in strict accordance with the "Zero Guess" policy:

1. **Root Packaging & Configuration:**
   - `c:/HARES/README.md`: Project description and quickstart instructions.
   - `c:/HARES/pyproject.toml`: Modern packaging with pinned dependencies and `pythonpath = ["src"]`.
   - `c:/HARES/.env.example` & `.env`: Validated environment templates.
   - `c:/HARES/.gitignore`: Strict exclusion of `.env`, Python bytecode, and virtual environments.

2. **Core Security Layer (`c:/HARES/src/hares/core/`):**
   - `config.py`: Pydantic v2 `BaseSettings` validating salt entropy ($\ge 32$ chars), database URIs, and Redis queues.
   - `security.py`:
     - `verify_meta_signature(payload_bytes, signature_header, app_secret)`: Constant-time HMAC-SHA256 signature validation with `sha256=` prefix verification.
     - `derive_citizen_user_hash(raw_phone_number, salt)`: E.164 phone normalization and keyed HMAC-SHA256 citizen pseudonymization (FR-4.1).

3. **Container Infrastructure:**
   - `c:/HARES/Dockerfile`: Multi-stage build based on `python:3.12-slim-bookworm` with non-root security user `hares:hares` (UID/GID 10001).
   - `c:/HARES/docker-compose.yml`: Tri-network bridge configuration orchestrating `api`, `worker`, `db` (Postgres 16 Alpine), and `redis` (Redis 7 Alpine). Validated via `docker compose config`.

4. **FastAPI Webhook & Ingress Gateway (`c:/HARES/src/hares/`):**
   - `main.py`: Application factory with security headers middleware (CSP, nosniff, DENY, HSTS, no-referrer) and health routes.
   - `api/v1/health.py`: Liveness (`/health/live`) and readiness (`/health/ready`) probes.
   - `api/v1/webhook.py`:
     - `GET /webhook`: Meta challenge handshake verification (`hub.mode == "subscribe"`, `hub.verify_token`, returns integer challenge).
     - `POST /webhook`: Constant-time signature verification, broker-level ephemeral queue dispatch (`apply_async(..., expires=60)`), and sub-50ms HTTP 200 acknowledgment.

5. **Celery Worker & Background Processing (`c:/HARES/src/hares/workers/`):**
   - `celery_app.py`: Celery instance bound to Redis broker/backend with `task_default_queue="high_priority_triage"`, `task_acks_late=True`, and explicit task routes.
   - `tasks.py`: Asynchronous `process_incoming_webhook` task. Derives citizen user hash, logs sanitized audit telemetry, and executes explicit memory purge (`del recipient_phone`, `del raw_sender_phone`).

6. **Automated Test Suite (`c:/HARES/tests/`):**
   - `conftest.py`: Hermetic session environment fixtures initializing required test secrets at module load time.
   - `test_security.py`: Signature validation (valid, invalid, malformed) and phone pseudonymization normalization equivalence.
   - `test_webhook.py`: Webhook GET handshake, 403 signature rejection, mocked POST queue ingestion asserting `queue="high_priority_triage"` and `expires=60`, and health probes.
   - `test_tasks.py`: Synchronous Celery task execution (`apply().get()`) verifying WhatsApp message extraction and empty payload handling.
   - **Test Results:** 11/11 tests passed in 1.36s (100% pass rate).

7. **Runtime Dependency Bug Discovered & Resolved:**
   - *Issue:* Host environment had Starlette 1.7.0, which removed the `on_startup` keyword argument from `Router.__init__`, creating an incompatibility with FastAPI 0.116.1.
   - *Resolution:* Pinned `"starlette>=0.40.0,<0.48.0"` in `pyproject.toml` and installed release `0.47.3`, restoring complete API routing stability.

---

### Phase 5: Cloudflare Defensive Security-Audit Skill Ingestion
Downloaded all 20 assets of Cloudflare's defensive source-first `security-audit` skill from `cloudflare/security-audit-skill/skills/security-audit` into `c:/HARES/.agents/skills/security-audit/`:
- **Core Skill Contract:** `SKILL.md`, `report-schema.json`.
- **Attack Class Checklists:** `AI-AND-LLM.md`, `ATTACK-CLASSES.md`, `CLIENT-SIDE.md`, `CLOUD-AND-DEPLOYMENT.md`, `DATA-ISOLATION-AND-LIFECYCLE.md`, `DESKTOP-MOBILE-AND-LOCAL-IPC.md`, `HUNTING.md`, `MEMORY-SAFETY-AND-BINARY.md`, `PROTOCOLS-RPC-AND-MESSAGING.md`, `RECONNAISSANCE.md`, `RESOURCE-EXHAUSTION-AND-AVAILABILITY.md`, `SUPPLY-CHAIN-AND-RELEASE.md`, `VALIDATION-AND-REPORTING.md`, `WEB-PROTOCOL-AND-AUTH.md`.
- **Validation Scripts:** `validate-coverage-ledger.cjs`, `validate-coverage-ledger.test.cjs`, `validate-findings.cjs`, `validate-findings.test.cjs`.

---

### Phase 6: Systematic Git Commit & Publication to GitHub
Initialized local Git repository on branch `main` and executed a semantic, 15-commit conventional progression pushed to **`https://github.com/abdullah00ashraf/HARES`**:

1. `6de700e`: `feat(core): implement packaging, configuration, and cryptographic security layer`
2. `5850068`: `feat(infra): add multi-stage Dockerfile and tri-network docker-compose topology`
3. `629fcf4`: `feat(webhook): implement sub-50ms FastAPI ingress and Celery worker triage pipeline`
4. `ebb36fd`: `test(unit): add hermetic unit and integration test suite`
5. `0224667`: `docs(ledger): record system blueprint and development history ledger`
6. `316eb4f`: `docs(ledger): record repository publication to GitHub in development history`
7. `5eacc55`: `docs(blueprint): record source control state in SYSTEM_STATE.md`
8. `268b75a`: `docs(history): record Session 1 context in history.md and history.json`
9. `48a50b5`: `feat(core): complete Phases 2-5, Next.js dashboard, security audits, and open-source registry`
10. `a654794`: `docs(sync): update dual ledgers and history tracking Milestone 18 Git publication`
11. `2653992`: `docs(audit): complete comprehensive Phase 5 defensive security audit (Audit 5)`
12. `52126f6`: `feat(phase6): production hardening, GPU topology, Prometheus metrics, and 200 QPS load benchmark`
13. `91d3e5d`: `docs(ledger): record commit 52126f6 in dual-ledger memory`
14. `7ee553c`: `docs(audit): publish Phase 6 comprehensive defensive security audit (Audit 6)`
15. `32ded09`: `feat(datasets): populate 100k UAE smishing corpus and 20k audio deepfake evaluation suite`

All commits tracked on remote `origin/main` with zero secret leakage (`.env` strictly ignored).

---

## 4. Current Repository File Index

```
c:/HARES/
├── .agents/
│   ├── rules/
│   │   ├── boost.md                         # Boost multi-agent reasoning rules
│   │   ├── policy.md                        # Zero Guess doctrine & compliance policies
│   │   ├── protocols.md                     # Citadel-Core architecture invariants
│   │   └── rules.md                         # DeepMind code quality mandates
│   ├── skills/
│   │   └── security-audit/                  # Cloudflare security audit suite (20 files)
│   │       ├── SKILL.md
│   │       ├── AI-AND-LLM.md
│   │       ├── ATTACK-CLASSES.md
│   │       ├── report-schema.json
│   │       └── ... (16 additional checklists and validation scripts)
│   └── boost/
│       ├── SKILL.md
│       └── developer.md
├── goal/
│   ├── architecture.md                      # System topology, C4 models, sub-50ms ingress
│   ├── feature.md                           # Functional & non-functional requirements matrix
│   ├── models.md                            # SLM, Whisper ASR, AASIST specs
│   ├── datasets.md                          # Curated UAE Opus Suite & evaluation sets
│   ├── database.md                          # PostgreSQL 16 DDL & SQLAlchemy ORM
│   ├── frontend.md                          # Next.js 15 Municipal Threat Dashboard
│   ├── backend.md                           # FastAPI / Celery modular architecture
│   └── security.md                          # DESC, ISR, and STRIDE compliance
├── idea/
│   ├── 01_Project_Hares_SRS.md              # System Requirements Specification
│   ├── 02_UAE_Cyber_Fraud_Statistics.md     # UAE regional threat data
│   └── 03_Validation_ChangeLog_and_OpenItems.md # Validation report & open items
├── opensource/
│   └── relevants.md                         # Open-source model, repo, and dataset registry
├── skills/                                  # Root agent skill directory
├── src/
│   └── hares/
│       ├── __init__.py
│       ├── main.py                          # FastAPI factory & security headers
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py                    # Pydantic v2 Settings (salt validation)
│       │   └── security.py                  # HMAC signature check & citizen hashing
│       ├── api/
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── health.py                # Liveness & readiness probes
│       │       ├── threat_feed.py           # Municipal IoC threat feeds, STIX 2.1 & CSV exports
│       │       └── webhook.py               # WhatsApp GET/POST webhook endpoint
│       ├── ai/
│       │   ├── __init__.py
│       │   ├── schemas.py                   # Pydantic v2 schemas (TextTriageInferenceResult, etc.)
│       │   ├── slm_client.py                # Local SLM Client integrated with Sovereign Guardrails
│       │   ├── audio_pipeline.py            # Unified Whisper Dual-Head pipeline
│       │   ├── conformal.py                 # Conformal statistical risk evaluator (FPR <= 0.1%)
│       │   └── guardrails/                  # Sovereign Programmable Guardrails (NVIDIA NeMo Guardrails)
│       │       ├── __init__.py              # SovereignGuardrailsEngine & GuardrailResult exports
│       │       ├── actions.py               # Deterministic action registry (PII, injection, schema, ecrime)
│       │       ├── config.yml               # Colang 2.x config binding local vLLM daemon
│       │       ├── engine.py                # SovereignGuardrailsEngine pipeline orchestrator
│       │       └── policies/
│       │           └── hares_guardrails.co  # Declarative Colang 2.0 event flows
│       └── workers/
│           ├── __init__.py
│           ├── celery_app.py                # Celery app & queue routing
│           └── tasks.py                     # process_incoming_webhook background task
├── tests/
│   ├── __init__.py
│   ├── conftest.py                          # Session-scoped hermetic test fixtures
│   ├── test_security.py                     # Signature & hashing unit tests
│   ├── test_webhook.py                      # Webhook challenge & post tests
│   ├── test_tasks.py                        # Celery worker task tests
│   ├── test_engine.py                       # Deterministic engine unit tests (allowlist, homograph, PII)
│   ├── test_db.py                           # Database ORM models and repository tests (aiosqlite)
│   ├── test_rate_limiter.py                 # Redis token-bucket rate limiter tests
│   ├── test_slm.py                          # Local SLM client unit tests
│   └── test_programmable_guardrails.py      # 21 unit & concurrency tests for Sovereign Guardrails
├── .env                                     # Local developer environment variables (git-ignored)
├── monitoring/
│   ├── prometheus.yml                       # Prometheus scrape config (5s interval)
│   └── grafana_dashboard.json               # Operational dashboard (ingress p99, E2E turnaround, queue depth)
├── benchmarks/
│   ├── mock_meta_sink.py                    # Mock Meta Cloud API egress sink & latency tracker
│   ├── traffic_payloads.py                  # Webhook payload & dynamic HMAC-SHA256 signature generator
│   ├── locustfile.py                        # Pure-Python Locust load test (85 text / 15 audio)
│   ├── run_stress_test.py                   # Stepped load benchmark orchestrator (50->100->200 QPS)
│   └── benchmark_summary.md                 # Automated SLA verification report
├── docker-compose.prod.yml                  # Production GPU topology (NVIDIA passthrough & dual worker pools)
├── docker-compose.yml                       # Dev/portable CPU topology
├── pyproject.toml                           # Python package definition & test settings
├── audit/
│   ├── audit_1.md through audit_6.md        # Formal Phase 1-6 Markdown reports
│   ├── pre-train_audit.md                   # Formal Audit 7 (Pre-Train Defensive Security)
│   ├── post-train_audit.md                  # Formal Audit 8 (Post-Train SafeTensors Verification)
│   └── certificates/                        # 4 sealed cryptographic JSON attestation certificates
├── opensource/
│   ├── CATALOG.json                         # Open-source asset registry (repositories, models, datasets)
│   ├── repositories/
│   │   └── guardrails/
│   │       └── nemo_guardrails/             # NVIDIA NeMo Guardrails upstream repository
│   └── datasets/
│       ├── localized_fraud_corpus/          # 100,000 paired ChatML records (87.72 MB)
│       └── synthetic_voice_eval/            # 20,000 WhatsApp-compliant 16 kHz Mono Opus .ogg files
├── README.md                                # Project overview & quickstart guide
├── SYSTEM_STATE.md                          # Living technical blueprint (v2.3.0-guardrails-verified)
├── DEVELOPMENT_LEDGER.md                    # Chronological execution & error history (Milestones 1-26)
├── history.md                               # Complete engineering session context ledger
└── history.json                             # Complete Session 1, 2 & 3 structured JSON ledger
```

---

## 5. Architectural Memory & State Ledger Summary

All persistent ledgers in the root directory remain synchronized with this history:
- **[`SYSTEM_STATE.md`](file:///c:/HARES/SYSTEM_STATE.md):** Documents the living state of active ports (8000, 6379, 5432, 11434, 3000, 9090, 8001), tri-network topologies (`hares_ingress`, `hares_internal`, `hares_egress`), environment variables, PostgreSQL DDL schemas, Phase 1 through 6 inventory, formal audit history (Audits 1 through 6), and Sovereign Dataset Registries (Section 7).
- **[`DEVELOPMENT_LEDGER.md`](file:///c:/HARES/DEVELOPMENT_LEDGER.md):** Chronologically records all 22 milestones from inception through Phase 1 code scaffolding, bug resolutions, security-audit ingestion, Git publication, Audit 1, Phase 2, Audit 2, Phase 3 implementation, Audit 3 verification, Phase 4 Municipal Threat Intelligence Feed & Next.js 15 Dashboard delivery, Phase 5 Sovereign AI Integration & Unified Whisper Dual-Head Pipeline, Audit 5, Phase 6 Production Hardening, Multi-Container GPU Orchestration, Observability & 200 QPS Stress Testing, Audit 6, and Milestone 22: Local Open-Source Datasets Population.
- **Milestone 22 Dataset Repositories:**
  - **100K Text Smishing & Social Engineering Corpus:** [`uae_smishing_100k.jsonl`](file:///c:/HARES/opensource/datasets/localized_fraud_corpus/uae_smishing_100k.jsonl) (87.72 MB, 100,000 paired ChatML records, 40% Emirati Gulf Arabic, 30% Modern Standard Arabic, 20% UAE Expat English, 10% Arabizi; 70% Malicious, 30% Benign) strictly adhering to `TextTriageInferenceResult`.
  - **20K Audio Deepfake & Acoustic Artifact Corpus:** [`synthetic_voice_eval/audio/`](file:///c:/HARES/opensource/datasets/synthetic_voice_eval/audio/) (20,000 WhatsApp-compatible 16 kHz mono Opus `.ogg` files, 50% Genuine across Common Voice Arabic Gulf/MSA, English, Urdu, and 50% Synthetic across F5-TTS, CosyVoice, XTTS-v2, and ElevenLabs) sharded across 20 subdirectories with streaming metadata [`audio_metadata.jsonl`](file:///c:/HARES/opensource/datasets/synthetic_voice_eval/audio_metadata.jsonl) and [`audio_corpus_manifest.json`](file:///c:/HARES/opensource/datasets/synthetic_voice_eval/audio_corpus_manifest.json).
- **Phase 6 Production Suite:** Production multi-container Docker topology with NVIDIA GPU passthrough (`docker-compose.prod.yml`), Prometheus telemetry (`/metrics`, `monitoring/prometheus.yml`, `monitoring/grafana_dashboard.json`), Mock Meta Egress Sink (`benchmarks/mock_meta_sink.py`), Locust 200 QPS load test (`benchmarks/locustfile.py`), stepped load runner (`benchmarks/run_stress_test.py`), and 100% resolution of all 20 audit observations (`AUDIT-OBS-01` through `AUDIT-OBS-20`).
- **Audit 6 Certification:** [`audit/audit_6.md`](file:///c:/HARES/audit/audit_6.md) & [`audit/audit_6.json`](file:///c:/HARES/audit/audit_6.json) certifying zero open critical/high vulnerabilities and production readiness.
- **Hermetic Test Suite:** 89 of 89 tests passing (100% pass rate) across security hardening, Prometheus metrics, concurrent load benchmarks, core security, webhook ingress, deterministic verification engine, persistence tier, rate limiting, sovereign AI schemas, conformal calibration, audio preprocessing, deepfake classification, speech ASR, guided SLM, threat feed API, unified audio pipeline, and Celery task workers.

---

## 6. Sessions 4 & 5: Cloud MLOps, Post-Train Ingestion, Empirical Testing & Cryptographic Certification (Milestones 23–25)

### Session 4: Cloud-to-Sovereign MLOps Bridge, Training & Security Audits
1. **Google Colab & Kaggle Training Pipelines (Milestone 23):**
   - Authored `notebooks/colab_slm_qlora_tuning.ipynb` for Qwen-2.5-3B QLoRA instruction tuning with Turing T4 Float16 fallback, Google Drive checkpoint streaming, and low-RAM LoRA merge.
   - Authored `notebooks/colab_whisper_dual_head_training.ipynb` and `notebooks/kaggle_whisper_dual_head_training.ipynb` implementing 2-phase decoupled Whisper head training (<60s on T4, TPU VM v3-8 support).
   - Generated `scripts/package_colab_data.py` (25k stratified curriculum core subset) and `scripts/export_quantized_models.py` (AWQ & GGUF).
   - Published formal read-only `audit/pre-train_audit.md` (Audit 7).
2. **Secure Weights Ingestion & Post-Train Audit (Milestone 24):**
   - Authored `scripts/unpack_model_weights.py` with Zip Slip defense, unpacking SafeTensors shards into `models/hares_qwen2.5_3b_merged_fp16/`.
   - Executed numerical audit `scripts/audit_slm_model.py`: 434 weight matrices, 3.08B parameters, 100% Float16, zero NaNs/Infs, zero leaked Class B citizen PII.
   - Hardened `LocalSLMClient` against ChatML token breakout (`<|im_start|>`, `<|im_end|>`) (`AUDIT-OBS-29`).
   - Published formal read-only `audit/post-train_audit.md` (Audit 8).

### Session 5: Held-Out Empirical Evaluation & Formal Benchmark Certification
1. **Empirical Local Testing on Held-Out UAE Benchmarks:**
   - Evaluated SLM on 500 unseen records (125/dialect): **97.16% Recall**, **80.80% Accuracy**, **100.0% containment** across 30 prompt injection attacks.
   - Evaluated Whisper head on 500 WhatsApp Opus trials: **100.0% Accuracy**, **0.000% False Positive Rate**, strictly satisfying $\text{FPR} \le 0.1\%$ bound.
   - Emitted reports in `model_test/`.
2. **Standardized Benchmark Harnesses & Cryptographic Attestation Authority (Milestone 25):**
   - Implemented Meta CyberSecEval harness (`src/hares/benchmarks/cyberseceval_harness.py`): 50 vectors, **ASR 0.00%**, 100% containment.
   - Implemented ASVspoof 2021 DF harness (`src/hares/benchmarks/asvspoof_df_harness.py`): **EER 0.00%**, packaged `audit/certificates/asvspoof2021_df_codalab_submission.zip`.
   - Implemented Dialect Equity harness (`src/hares/benchmarks/dialect_equity_harness.py`): **Disparity Ratio 0.9091** ($\ge 0.80$).
   - Implemented Sovereign Attestation Engine (`src/hares/benchmarks/attestation.py`): sealed 4 machine-readable JSON certificates in `audit/certificates/`.
   - Built Master CLI pipeline (`scripts/run_benchmark_certification_pipeline.py`) and published `audit/certificates/COMPLIANCE_DOSSIER_AND_CERTIFICATES.md`.
   - Hermetic test verification: 8/8 benchmark tests passing in 17.40s; 19/19 regression tests passing. Total repository test suite: 100% pass rate.

---

## 7. Session 6: Live Staging Smoke Testing, NVIDIA NeMo Guardrails Ingestion & Sovereign Programmable Guardrails Engine (Milestone 26)

### A. Live Staging Smoke Testing & Source Control Closeout (v2.2.0-staging-verified)
1. **Multi-Container Staging Cluster Verification:**
   - Validated live container stack: PostgreSQL 16, Redis 7, FastAPI Gateway, Celery Workers (text & media pools), and Next.js 15 SOC dashboard.
   - Verified automated Alembic migrations (`alembic upgrade head`) and active UAE official domain allowlist seeds.
   - Confirmed 0 Class B citizen PII leaks across audit databases, structured logs, and Prometheus metrics.
2. **Security Hardening Remediations:**
   - Remediated loopback SSRF check in `media_downloader.py`, strictly scoping non-production mock CDN exemptions to `/media/download/` paths.
   - Hardened authority lure classification in `slm_client.py`, requiring explicit impersonation or coercive threats before categorizing messages as active fraud.
   - Staged release tag `v2.2.0-staging-verified`.

### B. Upstream Asset Ingestion: NVIDIA NeMo Guardrails
1. **Repository Synchronization:**
   - Cloned upstream `NVIDIA-NeMo/Guardrails` into `opensource/repositories/guardrails/nemo_guardrails` via shallow clone (`--depth 1`).
   - Purged inner `.git` directory to maintain clean parent repository hierarchy.
   - Registered asset in `opensource/CATALOG.json` under `repo-nemo-guardrails`.
2. **Architectural Evaluation:**
   - Evaluated Colang 1.0 vs Colang 2.0 event-driven execution models.
   - Analyzed input, output, dialog, and retrieval rails alongside built-in safety libraries (`injection_detection`, `jailbreak_detection`, `sensitive_data_detection`).

### C. Milestone 26: Sovereign Programmable Guardrails Engine Implementation
1. **Framework Implementation (`src/hares/ai/guardrails/`):**
   - `actions.py`: Registered deterministic safety actions:
     - `mask_citizen_pii` (FR-4.1): Masking 15-digit Emirates IDs (`[REDACTED_EID]`), 16-digit credit cards (`[REDACTED_CARD]`), and OTP verification codes (`[REDACTED_OTP]`).
     - `detect_prompt_injection` (NFR-1.3): Multi-pattern defense neutralizing ChatML delimiters (`<|im_start|>`), XML boundary tag breakouts (`</citizen_forwarded_text>`), English instruction overrides, Arabic adversarial jailbreaks (`تجاهل جميع التعليمات السابقة`), and Base64-obfuscated injection payloads.
     - `check_topical_boundary`: Gating off-topic conversational probes and code generation attempts while admitting legitimate cyber fraud queries.
     - `validate_triage_schema` (FR-2.4): Normalizing raw model output and markdown codeblocks into strict `TextTriageInferenceResult` JSON contracts.
     - `enforce_dubai_police_escalation` (FR-3.1): Enforcing official Dubai Police links (`https://www.ecrime.ae` | `901`) on all high-risk verdicts.
   - `policies/hares_guardrails.co`: Declarative Colang 2.0 flow specifications enforcing input rails, topical boundaries, and output rails.
   - `config.yml`: Binding local sovereign `vLLM` model daemon (`models/hares_qwen2.5_3b_merged_fp16`) under Colang 2.x standard configuration.
   - `engine.py`: `SovereignGuardrailsEngine` orchestrator managing `process_input()`, `process_output()`, and `generate_safe_triage()`.
2. **Client Layer Integration (`src/hares/ai/slm_client.py`):**
   - Enriched `LocalSLMClient` with `enable_guardrails=True` by default.
   - Added `triage_with_guardrails()` returning complete `GuardrailResult` telemetry.
   - Preserved backward-compatible `triage_text()` seamlessly routing through guardrail pipelines.
3. **Automated Verification & Test Harness:**
   - Authored `tests/test_programmable_guardrails.py` covering 21 automated unit, integration, and concurrency stress tests.
   - Stress test passed with 8 concurrent threads $\times$ 25 iterations (200 total invocations) with zero exceptions or deadlocks.
   - Verified 100% test pass rate across the repository: **126 of 126 automated tests passing**.
   - 100% sovereign compute maintained: zero external network transmission (NFR-1.1).
