# Project Hares: Backend Engineering Specification

**Document Version:** 1.0.0-production-spec  
**Classification:** Backend Architecture & Services Engineering  
**Technology Stack:** Python 3.12+, FastAPI 0.115+, Celery 5.4+, Redis 7, SQLAlchemy 2.0 (Async), HTTPX  
**Policy Compliance:** Separation of Concerns (`api/`, `workers/`, `core/`, `engine/`, `ai/`, `db/`)  
**Requirements Reference:** FR-3.3 (Webhook SLA <500ms), FR-4.1 (PII Sanitization), NFR-1.1 (Data Sovereignty)  

---

## 1. Modular Directory Layout

In strict adherence to the project policy guidelines, the backend repository enforces separation of concerns:

```
c:/HARES/src/hares/
├── __init__.py
├── main.py                     # FastAPI application factory, lifespan & middleware setup
├── core/                       # Core configuration, security, and logging
│   ├── __init__.py
│   ├── config.py               # Pydantic-settings configuration from .env
│   ├── security.py             # Webhook signature validation & citizen HMAC hashing
│   ├── logging.py              # Structured JSON logging (sanitized, zero-PII)
│   └── exceptions.py           # Custom exception hierarchy & global handlers
├── api/                        # HTTP transport layer
│   ├── __init__.py
│   ├── deps.py                 # Dependency injection (DB sessions, settings)
│   ├── middlewares.py          # Security headers & timing middleware
│   └── v1/
│       ├── __init__.py
│       ├── router.py           # Master v1 API router
│       ├── webhook.py          # WhatsApp Webhook GET (challenge) & POST (ingress)
│       ├── health.py           # Health, liveness & readiness probes
│       └── threat_feed.py      # Municipal threat intelligence read endpoints
├── engine/                     # Deterministic verification engine
│   ├── __init__.py
│   ├── allowlist.py            # Exact registrable domain allowlist matcher
│   ├── homograph.py            # IDN Punycode decoder & Levenshtein lookalike scorer
│   ├── sanitizer.py            # Class A extraction & Class B bilingual PII scrubber
│   └── verdict.py              # Tri-state verdict synthesizer & template builder
├── ai/                         # Local sovereign AI inference pipelines (NFR-1.1)
│   ├── __init__.py
│   ├── slm_client.py           # Local vLLM/Ollama client with guided JSON decoding
│   ├── audio_classifier.py     # Local PyTorch AASIST/WavLM deepfake detector
│   ├── conformal.py            # Conformal calibration & non-parametric p-value engine
│   └── asr_client.py           # Local faster-whisper ASR transcription client
├── db/                         # Persistence & repository patterns
│   ├── __init__.py
│   ├── session.py              # Async SQLAlchemy engine & sessionmaker
│   ├── models.py               # Declarative SQLAlchemy 2.0 ORM tables
│   └── repositories/
│       ├── __init__.py
│       ├── threat_repo.py      # Threat indicators & campaigns repository
│       └── audit_repo.py       # Sanitized audit logging repository
├── workers/                    # Asynchronous Celery task processing
│   ├── __init__.py
│   ├── celery_app.py           # Celery application instance & Redis broker settings
│   └── tasks.py                # Asynchronous webhook triage & media processing tasks
└── services/                   # External transport adapters
    ├── __init__.py
    ├── whatsapp_client.py      # Meta Graph API outbound dispatcher (UAE storage)
    └── rate_limiter.py         # Redis-backed token bucket rate limiter (NFR-1.3)
```

---

## 2. Ingress Tier: WhatsApp Webhook Implementation (`api/v1/webhook.py`)

To satisfy **FR-3.3**, the webhook handler decouples ingress acknowledgment from all downstream processing.

### 2.1 Webhook Handshake (GET `/webhook`)
Validates Meta Cloud API subscription requests using the shared secret verify token:

```python
from fastapi import APIRouter, Query, Response, status
from hares.core.config import get_settings

router = APIRouter()

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
) -> Response:
    settings = get_settings()
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return Response(content=hub_challenge, media_type="text/plain", status_code=status.HTTP_200_OK)
    return Response(content="Forbidden", status_code=status.HTTP_403_FORBIDDEN)
```

### 2.2 Inbound Payload Ingestion (POST `/webhook`)
Executes HMAC-SHA256 signature verification, pushes the task into Redis, and returns HTTP 200 within **< 50ms**:

```python
import hmac
import hashlib
from fastapi import APIRouter, Header, HTTPException, Request, status
from hares.core.config import get_settings
from hares.workers.tasks import process_incoming_webhook

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def ingest_webhook(
    request: Request,
    x_hub_signature_256: str = Header(..., alias="X-Hub-Signature-256"),
) -> dict[str, str]:
    settings = get_settings()
    body_bytes = await request.body()

    # 1. Cryptographic Signature Validation
    expected_hash = hmac.new(
        key=settings.WHATSAPP_APP_SECRET.encode("utf-8"),
        msg=body_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    expected_header = f"sha256={expected_hash}"

    if not hmac.compare_digest(expected_header, x_hub_signature_256):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid payload signature")

    # 2. Asynchronous Queue Dispatch (Decoupled FR-3.3)
    raw_payload = await request.json()
    process_incoming_webhook.delay(raw_payload)

    # 3. Sub-50ms Immediate Webhook Acknowledgment
    return {"status": "queued"}
```

---

## 3. Asynchronous Worker Tier: Celery Pipeline (`workers/tasks.py`)

The Celery worker pool processes queued payloads out-of-band:

* **Ephemeral Transit Lifecycle (FR-4.1):** The recipient's phone number is carried in the serialized Celery payload inside Redis (`TTL = 60s`) solely to populate the `"to"` field for the outbound WhatsApp Cloud API call. 
* **Zero Persistence Rule:** Immediately following the outbound API call (or terminal failure), `del recipient_phone` is explicitly executed. The raw phone number is never written to PostgreSQL, application logs, or metric counters.

```mermaid
graph TD
    Payload[Raw Webhook Payload from Redis] --> ExtractMetadata[Extract Message & Ephemeral Recipient Phone]
    ExtractMetadata --> DeriveHash[Derive Salted HMAC User Hash]
    DeriveHash --> RateLimitCheck{Check Redis Token Bucket<br/>5 req/hour (NFR-1.3)}
    
    RateLimitCheck -->|Exceeded| SendThrottleMsg[Dispatch Opaque Rate-Limit Template]
    RateLimitCheck -->|Allowed| InspectMedia{Message Type}
    
    InspectMedia -->|Text or URL| RunDeterministic[Run Registrable Allowlist & Homograph Checks]
    RunDeterministic --> SLMTriage[Run Local SLM Intent Classifier]
    
    InspectMedia -->|Audio Voice Note| DurationCheck{Duration <= 120s?}
    DurationCheck -->|No| SendTooLongMsg[Send Exceeded Duration Template]
    DurationCheck -->|Yes| FetchMediaURL[Hop 1: GET /v21.0/media_id to obtain URL]
    FetchMediaURL --> StreamMediaBinary[Hop 2: GET binary payload from Meta CDN]
    StreamMediaBinary --> TranscodeAudio[FFmpeg In-Memory to 16kHz PCM]
    TranscodeAudio --> RunDeepfake[AASIST Deepfake Classifier + Conformal p-values]
    TranscodeAudio --> RunASR[faster-whisper INT8 Transcription]
    RunASR --> SLMTriage
    
    SLMTriage & RunDeepfake --> SynthesizeVerdict[Formulate Tri-State Verdict: Red / Amber / Green]
    SynthesizeVerdict --> DispatchReply[Dispatch Outbound WhatsApp Template to Recipient Phone]
    DispatchReply --> PurgePhoneMemory[Explicit del recipient_phone from RAM]
    PurgePhoneMemory --> SaveThreats[Save Class A IoCs to PostgreSQL Threat DB]
```

---

## 4. Deterministic Verification Engine (`engine/`)

### 4.1 Registrable Domain Allowlist Matcher (`engine/allowlist.py`)
Extracts registrable domains using public suffix parsing (`tldextract`) and verifies exact matches:

```python
import tldextract
from hares.db.models import OfficialDomain

class AllowlistEngine:
    def __init__(self, active_domains: set[str]):
        self._active_domains = active_domains

    def is_allowlisted(self, url_or_domain: str) -> bool:
        extracted = tldextract.extract(url_or_domain)
        registrable = f"{extracted.domain}.{extracted.suffix}".lower()
        return registrable in self._active_domains
```

### 4.2 IDN Homograph & Lookalike Scorer (`engine/homograph.py`)
Detects punycode spoofing across subdomains, validates legitimate UAE Arabic TLDs (`.امارات`) and their authentic Arabic second-level domain labels, and applies length-normalized Levenshtein distance scoring against allowlisted entities:

```python
import idna
import re
import tldextract
from Levenshtein import distance

# Whitelist legitimate UAE Arabic ccTLD (.امارات)
ALLOWED_ARABIC_TLDS: set[str] = {"xn--mgbaam7a8h"}

# Arabic Unicode Block range check: \u0600-\u06FF, \u0750-\u077F, \u08A0-\u08FF
ARABIC_UNICODE_PATTERN = re.compile(r"^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF0-9\-]+$")

class HomographDetector:
    def check_spoof(self, candidate_domain: str, allowlist: set[str]) -> tuple[bool, str]:
        try:
            ascii_encoded = idna.encode(candidate_domain).decode("ascii").lower()
            labels = ascii_encoded.split(".")
            tld = labels[-1]
            
            # 1. TLD Punycode Verification
            if tld.startswith("xn--") and tld not in ALLOWED_ARABIC_TLDS:
                return True, f"unauthorized_punycode_tld_{tld}"
                
            # 2. Non-TLD Label Verification
            is_arabic_cctld = (tld in ALLOWED_ARABIC_TLDS)
            for label in labels[:-1]:
                if label.startswith("xn--"):
                    decoded_label = idna.decode(label)
                    # If under .امارات, label must consist purely of authentic Arabic characters
                    if is_arabic_cctld:
                        if not ARABIC_UNICODE_PATTERN.match(decoded_label):
                            return True, f"mixed_script_spoof_in_arabic_domain_{label}"
                    else:
                        # Non-Arabic TLDs (.ae, .com) with punycode subdomains targeting UAE are high-risk
                        return True, f"punycode_homograph_in_label_{label}"
        except idna.IDNAError:
            return True, "malformed_idn_encoding"

        # 3. Length-Normalized Lookalike Distance against allowlist
        extracted_cand = tldextract.extract(candidate_domain).domain.lower()
        for official in allowlist:
            official_domain_part = tldextract.extract(official).domain.lower()
            d = distance(extracted_cand, official_domain_part)
            max_len = max(len(extracted_cand), len(official_domain_part))
            
            # Match only if difference is within 25% of string length (prevents dew.ae -> dewa false alarms)
            if 0 < d <= 2 and (d / max_len) <= 0.25 and extracted_cand != official_domain_part:
                return True, f"lookalike_spoof_of_{official}"

        return False, "clean"
```

---

## 5. Security Middlewares & Hardened Headers

The FastAPI gateway applies production-grade HTTP security headers on all responses:

* `Content-Security-Policy: default-src 'none'; frame-ancestors 'none';`
* `X-Content-Type-Options: nosniff`
* `X-Frame-Options: DENY`
* `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload`
* `Referrer-Policy: no-referrer`
* `Permissions-Policy: geolocation=(), camera=(), microphone=()`

---

## 6. Observability & Health Probes

* **`GET /health/live`**: Returns 200 if the FastAPI event loop is responsive.
* **`GET /health/ready`**: Verifies connectivity to:
  * PostgreSQL (executes `SELECT 1`)
  * Redis (executes `PING`)
  * Local SLM Endpoint (checks HTTP status of `http://slm:11434`)
  * Celery Worker Heartbeat (queries Celery inspector ping)
* **Prometheus Metrics (`/metrics`)**:
  * `hares_incoming_webhooks_total` (counter by status code)
  * `hares_webhook_processing_latency_seconds` (histogram)
  * `hares_triage_verdict_total` (counter by red, amber, green)
  * `hares_rate_limit_exceeded_total` (counter)
