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
Initialized local Git repository on branch `main` and executed a semantic, 8-commit conventional progression pushed to **`https://github.com/abdullah00ashraf/HARES`**:

1. `cdac05a`: `docs: initialize foundational specifications and architectural blueprints`
2. `4adff43`: `feat(agent): configure governance rules, skills, and security audit frameworks`
3. `6de700e`: `feat(core): implement packaging, configuration, and cryptographic security layer`
4. `5850068`: `feat(infra): add multi-stage Dockerfile and tri-network docker-compose topology`
5. `629fcf4`: `feat(webhook): implement sub-50ms FastAPI ingress and Celery worker triage pipeline`
6. `ebb36fd`: `test(unit): add hermetic unit and integration test suite`
7. `0224667`: `docs(ledger): record system blueprint and development history ledger`
8. `316eb4f`: `docs(ledger): record repository publication to GitHub in development history`
9. `5eacc55`: `docs(blueprint): record source control state in SYSTEM_STATE.md`

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
│       │       └── webhook.py               # WhatsApp GET/POST webhook endpoint
│       └── workers/
│           ├── __init__.py
│           ├── celery_app.py                # Celery app & queue routing
│           └── tasks.py                     # process_incoming_webhook background task
├── tests/
│   ├── __init__.py
│   ├── conftest.py                          # Session-scoped hermetic test fixtures
│   ├── test_security.py                     # Signature & hashing unit tests
│   ├── test_webhook.py                      # Webhook challenge & post tests
│   └── test_tasks.py                        # Celery worker task tests
├── .env                                     # Local developer environment variables (git-ignored)
├── .env.example                             # Public environment template
├── .gitignore                               # Git exclusion rules
├── Dockerfile                               # Multi-stage hardened Python 3.12 container
├── docker-compose.yml                       # Tri-network container topology
├── pyproject.toml                           # Python package definition & test settings
├── README.md                                # Project overview & quickstart guide
├── SYSTEM_STATE.md                          # Living technical blueprint
├── DEVELOPMENT_LEDGER.md                    # Chronological execution & error history
├── history.md                               # Complete Session 1 markdown context ledger
└── history.json                             # Complete Session 1 structured JSON ledger
```

---

## 5. Architectural Memory & State Ledger Summary

Both persistent ledgers in the root directory remain synchronized with this history:
- **[`SYSTEM_STATE.md`](file:///c:/HARES/SYSTEM_STATE.md):** Documents the living state of active ports (8000, 6379, 5432, 11434, 3000), tri-network topologies (`hares_ingress`, `hares_internal`, `hares_egress`), environment variables, PostgreSQL DDL schemas, Phase 1 inventory, and GitHub remote tracking.
- **[`DEVELOPMENT_LEDGER.md`](file:///c:/HARES/DEVELOPMENT_LEDGER.md):** Chronologically records all 10 milestones from inception through Phase 1 code scaffolding, bug resolutions, security-audit ingestion, and Git publication.
