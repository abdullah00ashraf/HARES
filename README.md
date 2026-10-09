# Project Hares (مشروع حارس)

**Automated Fraud Triage and Threat Intelligence System for Dubai and UAE Residents**

Project Hares is an open-source, sovereign, and privacy-preserving automated threat-intelligence and fraud-triage platform designed for residents of Dubai. Functioning as a single-purpose WhatsApp Business bot compliant with Meta's Business API policies, it analyzes forwarded text lures, URLs, and audio voice notes (`.ogg` Opus) to detect social engineering and synthetic media (deepfakes) while aggregating sanitized threat indicators into a municipal threat intelligence repository.

---

## Architecture & Operational Invariants

1. **Local Sovereign Inference (NFR-1.1):** 100% of AI inference (SLM text classification, Whisper ASR, AASIST audio deepfake classifier) runs locally within sovereign UAE infrastructure. Zero data is ever dispatched to offshore proprietary AI APIs.
2. **Sub-50ms Webhook Acknowledgment (FR-3.3):** Inbound WhatsApp webhooks (`POST /webhook`) are signature-validated via constant-time HMAC-SHA256, enqueued to Redis via Celery, and acknowledged with `HTTP 200 {"status": "queued"}` in $< 50\text{ms}$.
3. **Class A vs Class B Cryptographic Sanitization (FR-4.1):** Citizen phone numbers exist only ephemerally in Redis with a 60-second TTL strictly for outbound message routing. Phone numbers are pseudonymized via keyed `HMAC-SHA256` for rate limiting (5 queries/hour) and purged from memory immediately following response dispatch. Only scammer threat indicators (Class A) are persisted to PostgreSQL.
4. **Tri-Network Isolation:** Docker container network topology divides services across `hares_ingress` (API ingress), `hares_internal` (non-routable `internal: true` bridge isolating DB, Redis, and SLM), and `hares_egress` (outbound Meta API HTTPS routing).

---

## Quickstart

### 1. Environment Configuration
```bash
cp .env.example .env
# Edit .env with your WhatsApp Business Cloud API credentials and secrets
```

### 2. Local Container Deployment
```bash
docker compose up -d --build
```

### 3. Verify Health Probes
```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

### 4. Run Test Suite
```bash
pytest tests/ -v
```
