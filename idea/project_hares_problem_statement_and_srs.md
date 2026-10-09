# Project Hares: Public Fraud Triage & Threat Intelligence System

## 1. Problem Statement

As the Dubai government accelerates digital transformation through initiatives like the Agentic AI for Government Services Accelerator, the cybersecurity threat landscape has shifted. While municipal and enterprise perimeters are increasingly fortified, the most vulnerable endpoint remains the everyday citizen.

**The Challenge:**
According to the UAE Cyber Security Council, social engineering drives nearly 98% of cyberattacks. With the commoditization of generative AI, threat actors are deploying hyper-realistic smishing (SMS phishing) and deepfake voice-cloning scams on a massive scale. These attacks predominantly occur on WhatsApp, impersonating official entities such as Dubai Police, DEWA, or Emirates Post. 

Currently, Dubai residents lack a frictionless, centralized tool to verify suspicious messages in real-time. A 2024 survey revealed that while 56% of UAE residents face monthly scam attempts, only 30% report them, and 18% do not know where to report. This hesitation leads to severe financial loss for citizens and deprives municipal authorities of real-time threat intelligence needed to combat campaigns before they scale.

**The Solution:**
Project Hares bridges this gap by providing an open-source, purpose-built fraud triage tool accessible directly via WhatsApp. It allows residents to forward suspicious texts, URLs, and voice notes for immediate automated verification. Concurrently, it aggregates sanitized threat data into an internal government dashboard, mapping active social engineering campaigns while strictly adhering to UAE data sovereignty and privacy laws.

---

## 2. Software Requirements Specification (SRS)

### 2.1 Introduction
**2.1.1 Purpose:** 
This document specifies the software requirements for Project Hares, detailing the functional and non-functional requirements for both the citizen-facing WhatsApp interface and the internal Threat Intelligence Dashboard.

**2.1.2 Scope:**
Project Hares consists of two primary modules:
1.  **Citizen Triage Interface:** A single-purpose WhatsApp bot that receives forwarded media/text, analyzes it for fraudulent intent or synthetic generation, and provides a binary risk assessment.
2.  **Threat Intel Dashboard:** A secure, web-based portal for government analysts to view aggregated, anonymized data on active scam vectors.

### 2.2 Overall Description
**2.2.1 Operating Environment:**
*   **Frontend (Public):** Meta WhatsApp Business API (configured as a single-purpose verification tool).
*   **Frontend (Admin):** Next.js (React) web application.
*   **Backend:** Asynchronous Python (FastAPI) deployed via Docker.
*   **Infrastructure:** UAE-region cloud infrastructure (e.g., Dubai AI Infrastructure Empowerment Platform) to ensure data sovereignty.
*   **AI Models:** Self-hosted, open-weight text and audio classification models (e.g., Llama 3 derivatives, wav2vec).

**2.2.2 User Classes:**
*   **Citizens (End Users):** Require low-friction, immediate, and clear verification of forwarded content.
*   **Threat Analysts (Admins):** Require real-time data visualization, high-level threat telemetry, and exportable reports.

### 2.3 System Features (Functional Requirements)

**2.3.1 Media Triage & Audio Classification**
*   **FR-1.1:** The system shall accept forwarded `.mp3`, `.m4a`, and `.ogg` audio files via the WhatsApp API.
*   **FR-1.2:** The system shall route audio files to a post-hoc, model-independent audio classifier to detect synthetic generation (deepfakes).
*   **FR-1.3:** The classifier must be robust to standard telecom compression and quantization introduced by WhatsApp.
*   **FR-1.4:** The system shall utilize conformal p-values calibrated against a held-out local dataset to establish detection thresholds, avoiding parametric distribution assumptions.

**2.3.2 Text & Link Verification**
*   **FR-2.1:** The system shall extract text and URLs from forwarded messages.
*   **FR-2.2:** The system shall cross-reference extracted URLs against a strictly maintained `.gov.ae` allowlist and a dynamic blocklist of known malicious domains.
*   **FR-2.3:** The system shall utilize a local LLM to parse the semantic intent of the text (e.g., detecting urgency-driven payment requests mimicking government entities).

**2.3.3 Automated Handoff & Response**
*   **FR-3.1:** The system shall return a clear, binary risk assessment (e.g., "🔴 HIGH RISK" or "🟢 NO KNOWN THREAT DETECTED") within 5 seconds of receiving a query.
*   **FR-3.2:** If high risk is detected, the system shall provide a direct handoff link to the official Dubai Police e-Crime portal or advise calling 901.

**2.3.4 Threat Intelligence Aggregation**
*   **FR-4.1:** The system shall sanitize all incoming queries, stripping Personally Identifiable Information (PII) before database storage.
*   **FR-4.2:** The system shall log the threat vector (e.g., "DEWA Impersonation", "Voice Clone") and timestamp to a PostgreSQL database.
*   **FR-4.3:** The admin dashboard shall display real-time heatmaps and frequency graphs of active scam templates.

### 2.4 Non-Functional Requirements

**2.4.1 Security & Data Sovereignty**
*   **NFR-1.1 (Sovereignty):** No citizen data or telemetry shall be routed through offshore APIs (e.g., OpenAI, Anthropic, or standard Hugging Face endpoints). All AI inference must occur on UAE-hosted infrastructure.
*   **NFR-1.2 (Compliance):** The system architecture must comply with the UAE Personal Data Protection Law (Federal Decree-Law No. 45 of 2021).
*   **NFR-1.3 (Threat Modeling):** The system shall implement robust input filtering to prevent prompt injection attacks (where an attacker attempts to use the bot to validate their own scam templates). Zero-entropy or out-of-domain generations shall be automatically rejected.

**2.4.2 Performance & Reliability**
*   **NFR-2.1 (Throughput):** The asynchronous backend must support a minimum of 1,000 concurrent WhatsApp API webhooks without dropping requests.
*   **NFR-2.2 (Uptime):** The system shall target a 99.9% uptime, utilizing Docker container orchestration for high availability and automatic restarts.

**2.4.3 Accuracy & Decision Making**
*   **NFR-3.1 (False Positives):** The audio classification and text triage systems must be calibrated to maintain a False Positive Rate (FPR) of less than 0.1% to prevent alert fatigue and maintain public trust.
*   **NFR-3.2 (Ambiguity Handling):** In cases where the conformal p-value indicates high uncertainty (e.g., heavily degraded audio), the system shall abstain from a definitive technical verdict and default to a behavioral warning ("Verify by calling the official source").