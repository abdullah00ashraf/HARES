# 01_Project_Hares_SRS.md

# Project Hares: Public Fraud Triage & Threat Intelligence System
**System Requirements Specification & Architecture Definition**  
*Document Version: 2.0-revised*  
*Classification: Dubai Public Sector Architecture Proposal*  

---

## 1. Problem Statement

As the Dubai government accelerates digital transformation through initiatives such as the Agentic AI for Government Services Accelerator (launched 5 October 2026 by Dubai Future Foundation across 33 Dubai entities covering 300+ public-facing use cases)[cite: 42], municipal and enterprise perimeters have hardened significantly. Consequently, threat actors increasingly bypass technical perimeters by targeting the human layer[cite: 40]. Official telemetry from the UAE Cyber Security Council confirms that **75% of cyber breaches within the UAE originate from phishing emails and fraudulent messages** (reported 16 July 2026)[cite: 40, 42]. While broader public awareness campaigns cite that human error figures in nearly 98% of cyber incidents (UAE Cyber Security Council Cyber Pulse campaign, 21 September 2025)[cite: 42], the attack surface has expanded into mobile instant messaging. Threat actors routinely deploy smishing (SMS phishing) and social engineering lures via WhatsApp, impersonating official entities such as Dubai Police, DEWA, or Emirates Post[cite: 41].

### 1.1 The Specific Operational Gap
Dubai residents currently have access to established formal reporting and emergency channels, including:
* Dubai Police non-emergency line (901) and the Dubai Police e-Crime portal (`ecrime.ae`)[cite: 42].
* Abu Dhabi Police Aman Service (800-2626 / SMS 2828)[cite: 42].
* Sharjah Police Najeed Service (800151 / SMS 7999)[cite: 42].
* The Dubai Police Anti-Fraud Centre[cite: 42].

However, empirical research indicates a pronounced operational gap in **pre-loss triage and low-friction intelligence harvesting**:
1. **Reporting Friction and Awareness:** In a 2024 national study (*State of Scams in the UAE*, GASA / BioCatch / Cyber Security Council / TRENDS; $n = 1,964$ UAE residents), **56% of respondents reported encountering scam attempts at least monthly**, yet **only 30% reported scam encounters to law enforcement**, and **18% stated they did not know where to report scams**[cite: 42].
2. **The Zero-Loss Telemetry Blackout:** The 2026 GASA / Trend Micro study ($n = 1,000$ UAE residents) revealed that while 79% of individuals who experienced a scam reported at least one incident to some entity (most frequently banks or platform providers), **no financial loss was the single most common reason for not reporting scams, cited by 52% of non-reporting respondents**[cite: 42]. Furthermore, **50% of respondents who submitted a report stated that no action was taken or they remained unsure of the outcome**[cite: 42].
3. **The Unharvested Reconnaissance Window:** When a citizen receives a fraudulent link or synthetic voice note, identifies it as suspicious, and simply deletes it without financial loss, existing formal police channels (which require structured complainant data and evidence of an offense within Dubai jurisdiction) are rarely engaged[cite: 42]. Consequently, active malicious infrastructure remains fully operational against other residents[cite: 40].

### 1.2 Proposed Solution
Project Hares resolves this gap by providing an open-source, purpose-built, automated fraud triage tool deployed on WhatsApp[cite: 41, 42]. The service functions not as a general-purpose conversational agent, but as a deterministic and statistical classification pipeline[cite: 42]. Citizens forward suspicious text lures, URLs, or recorded voice notes to receive immediate, non-definitive risk indicators and official verification routing[cite: 41, 42]. Concurrently, the platform extracts and aggregates sanitized threat indicators (scammer URLs, phone numbers, and crypto addresses) into an internal municipal threat intelligence repository, providing security operations teams with an early-warning feedback loop before financial loss occurs[cite: 40, 41].

---

## 2. Software Requirements Specification (SRS)

### 2.1 Introduction

#### 2.1.1 Purpose
This specification defines the functional, non-functional, security, and architectural requirements for Project Hares[cite: 41]. It details the citizen-facing triage interface and the municipal Threat Intelligence Dashboard, establishing engineering constraints that comply with UAE sovereign cloud and data-protection mandates[cite: 41, 42].

#### 2.1.2 Scope
Project Hares encompasses:
1. **Citizen Triage Interface:** A single-purpose WhatsApp Business messaging endpoint that receives forwarded text, links, and voice notes, parses them via deterministic rules and local open-weight AI models, and returns an automated triage verdict[cite: 41, 42].
2. **Threat Intelligence Aggregator:** An asynchronous backend pipeline that strips citizen identifiers, extracts malicious indicators of compromise (IoCs), and exposes aggregated campaign telemetry to authorized municipal analysts via a secured Next.js web portal[cite: 41, 42].

---

### 2.2 Overall Description

#### 2.2.1 Operating Environment & Infrastructure Boundaries
* **Citizen Messaging Transport:** Meta WhatsApp Business Cloud API[cite: 41, 42]. The service is deployed strictly as a single-purpose verification utility to adhere to Meta’s Business API terms prohibiting general-purpose conversational AI assistants[cite: 42].
* **Data Sovereignty Architecture:** Message transport operates over Meta global network infrastructure[cite: 42]. To enforce data residency at rest, Project Hares mandates enabling **WhatsApp Business Cloud API Local Storage configured to the UAE region**[cite: 42].
* **Hares-Controlled Processing Boundary:** All application logic, database storage, message decryption, and AI inference must execute entirely within secure UAE sovereign cloud infrastructure (e.g., the Dubai Government AI Infrastructure Empowerment Platform[cite: 41, 42], subject to official public entity sponsorship[cite: 42]).
* **External API Prohibition:** No citizen message payload, metadata, or extracted token shall be transmitted to external, foreign, or third-party proprietary AI APIs[cite: 41, 42].
* **Application Framework:** Asynchronous Python (FastAPI) containerized via Docker and orchestrated within a local Kubernetes or container cluster[cite: 41].
* **AI Model Selection:** `[ASSUMPTION – Benchmark open-weight multilingual LLMs (e.g., Llama-3.2-3B-Instruct) against regional foundation models (e.g., Falcon-Mamba, Jais-13b) on an in-domain labelled UAE Arabic/English smishing evaluation set prior to production freeze]`[cite: 42].

#### 2.2.2 User Classes & Permissions
* **Dubai Residents (End Users):** Forward unverified digital communications anonymously via WhatsApp; receive immediate risk indicators and institutional handoff pathways[cite: 41].
* **Municipal Threat Intelligence Analysts:** Access role-based web dashboards to inspect sanitized campaign trends, export blocklists, and evaluate emerging attack templates[cite: 41].

---

### 2.3 System Features (Functional Requirements)

#### 2.3.1 Media Triage & Audio Classification
* **FR-1.1:** The system shall ingest forwarded voice notes and audio payloads in `.mp3`, `.m4a`, and `.ogg` (Opus) containers received via the WhatsApp Business API webhook[cite: 41, 42].
* **FR-1.2:** The system shall route audio files to an on-premise, post-hoc audio classification model to evaluate acoustic and spectral artifacts indicative of synthetic voice cloning[cite: 41, 42].
* **FR-1.3:** The audio classification feature extractor must be calibrated specifically against lossy, low-bitrate Opus speech encoding to account for WhatsApp transmission degradation[cite: 41, 42].
* **FR-1.4:** The audio classifier shall establish detection thresholds using non-parametric conformal p-values calibrated on a held-out reference dataset[cite: 41, 42]. The system shall explicitly document the underlying statistical exchangeability assumption, recognizing that distribution drift will alter empirical false alarm rates in production[cite: 42].
* **FR-1.5:** The system shall restrict audio inference strictly to forwarded audio files under 120 seconds in duration, rejecting larger payloads to preserve GPU compute capacity[cite: 42].

#### 2.3.2 Text & Link Verification
* **FR-2.1:** The system shall extract raw textual bodies, embedded hyperlinks, phone numbers, and potential financial identifiers from forwarded SMS and chat payloads[cite: 41, 42].
* **FR-2.2:** The system shall verify extracted web links against a curated, exact-match registrable domain allowlist containing verified official UAE public-sector and critical infrastructure portals (each entry requiring a verified entity owner and mandatory quarterly review date)[cite: 42]. The allowlist must explicitly include non-`.gov.ae` official public domains such as `ecrime.ae` and `salik.ae`[cite: 42].
* **FR-2.3:** The link verification engine shall execute deterministic string-matching routines, including Internationalized Domain Name (IDN) homograph detection, punycode resolution, and Levenshtein distance lookalike scoring against allowlisted targets, emitting an immediate deterministic high-risk flag upon identifying spoofing[cite: 42].
* **FR-2.4:** Payloads not resolved by deterministic allowlists or blocklists shall be evaluated by a locally hosted Small Language Model (SLM) executing prompt-bounded intent extraction[cite: 41, 42].

#### 2.3.3 Automated Handoff & Tri-State Verdict Semantics
* **FR-3.1:** The system shall classify incoming submissions into one of three explicit operational states and return the corresponding standardized response template via WhatsApp within 5 seconds[cite: 41, 42]:
  1. **🔴 HIGH RISK (Red):** Confirmed match against known malicious infrastructure, homograph spoof of official domains, or verified synthetic audio artifacts[cite: 41, 42].
  2. **🟡 UNVERIFIED / PROCEED WITH CAUTION (Amber - Default State):** The submission does not match known threat signatures, but cannot be verified as authentic official correspondence[cite: 42]. The response shall explicitly advise verifying directly through official directories[cite: 42].
  3. **🟢 VERIFIED OFFICIAL DESTINATION (Green):** Extracted links strictly resolve to an authenticated entry on the exact-domain allowlist[cite: 42].
* **FR-3.2:** Whenever a Red (High Risk) verdict is returned, the system shall provide immediate, direct escalation links to the official Dubai Police e-Crime portal (`https://www.ecrime.ae`) and display the non-emergency telephone contact (901)[cite: 41, 42].
* **FR-3.3:** The WhatsApp triage handler shall issue an immediate HTTP 200 acknowledgment to the Meta webhook within 500 ms of receipt and deliver the subsequent triage assessment as an asynchronous outbound message, preventing gateway timeouts during model inference[cite: 42].

#### 2.3.4 Threat Telemetry Isolation & Sanitization
* **FR-4.1:** The backend ingestion engine shall strictly divide incoming message data into two segregated data classes prior to persistence[cite: 42]:
  * **Class A: Scammer-Controlled Indicators (Retained for Intelligence):** Malicious URLs, foreign sender phone numbers, destination cryptocurrency wallet addresses, spoofed domain names, and extracted bank accounts[cite: 42]. These are retained indefinitely[cite: 42].
  * **Class B: Citizen-Specific Identifiers (Sanitized / Discarded):** Submitter phone numbers, citizen names, national identification numbers (Emirates ID), One-Time Passwords (OTPs), and personal account numbers[cite: 42]. Submitter phone numbers must be converted via a keyed cryptographic salt to a pseudonymized identifier to enable rate limiting, with the raw number dropped from memory[cite: 42].
* **FR-4.2:** The redaction pipeline shall undergo automated recall benchmarking against bilingual (Arabic and English) and dialectal text to guarantee citizen PII is completely stripped before threat intelligence archiving[cite: 42].
* **FR-4.3:** The internal Threat Intelligence Dashboard shall display aggregate geospatial, temporal, and category heatmaps of active fraud campaigns without exposing Class B citizen identifiers[cite: 41, 42].

---

### 2.4 Non-Functional Requirements

#### 2.4.1 Security, Privacy & Legal Governance
* **NFR-1.1 (Data Sovereignty & Processing Boundaries):** All Hares-controlled infrastructure must physically reside within sovereign data centers located in the United Arab Emirates[cite: 41, 42]. WhatsApp Business Cloud API Local Storage must be enabled for UAE data-at-rest[cite: 42]. The public onboarding disclosure must transparently state that external message transport is operated by Meta Platforms Inc.[cite: 42] Transmission of raw or processed citizen telemetry to foreign third-party model APIs is strictly prohibited[cite: 41, 42].
* **NFR-1.2 (Regulatory Governance):** If operated directly by or on behalf of a Dubai government entity, system data governance is subject to the Dubai Electronic Security Center (DESC) regulations, the Dubai Information Security Regulation (ISR), and the Dubai AI Security Policy[cite: 42]. Federal Decree-Law No. 45 of 2021 on the Protection of Personal Data (PDPL) exempts government data and government entities from its material scope[cite: 42]. `[ASSUMPTION – Operational status of the PDPL Executive Regulations is unresolved; confirm specific compliance posture with qualified UAE legal counsel prior to enterprise deployment]`[cite: 42].
* **NFR-1.3 (Adversarial Anti-Reconnaissance Controls):** To prevent adversaries from using the triage bot as an automated oracle, the service shall enforce:
  1. Pseudonymized rate-limiting capping submissions to 5 queries per hour per unique user hash[cite: 42].
  2. Uniform, opaque triage verdicts that omit granular probability scores, confidence intervals, or specific feature-level explanations on Amber and Green responses[cite: 42].
  3. Active canary monitoring to alert administrators if near-identical text variants are submitted sequentially from clustered source numbers[cite: 42].

#### 2.4.2 Performance, Capacity & Reliability
* **NFR-2.1 (Throughput & Cloud API Tier):** The production deployment shall be provisioned for the WhatsApp Business Cloud API 1,000 messages/second throughput tier[cite: 42]. System compute capacity must be engineered to sustain a peak load of 1,000 concurrent queries within the 5-second end-to-end SLA[cite: 42].
  * *Capacity Planning Basis [engineering estimate]:*
    $$\text{Target Concurrency } C = 1{,}000 \text{ queries}, \quad \text{SLA Latency } L = 5.0 \text{ s}$$
    $$\text{Arrival Rate } \lambda = \frac{C}{L} = \frac{1{,}000}{5} = 200 \text{ queries/s}$$
    $$\text{Throughput Requirement } T = 2 \times \lambda = 400 \text{ messages/s (inbound + outbound)}$$
    A sustained arrival of 200 queries/s requires dedicated local GPU inference infrastructure sized to complete text classification within 1.5 seconds and audio feature extraction within 3.0 seconds[cite: 42].
* **NFR-2.2 (System Availability & SLO Scope):** The platform shall maintain a 99.9% availability Service Level Objective (SLO), equating to a maximum allowable unscheduled downtime of 8.76 hours per calendar year `[engineering estimate]`[cite: 42]. This SLO is explicitly scoped to components within Hares-controlled infrastructure and excludes downtime caused by Meta WhatsApp network transport or upstream carrier outages[cite: 42].

#### 2.4.3 Detection Accuracy & Statistical Confidence Bounds
* **NFR-3.1 (False Positive Rate Calibration):** The audio classification and text triage engines must be calibrated to maintain an empirical False Positive Rate (FPR) of $\le 0.1\%$[cite: 41, 42]. This threshold must be experimentally validated on a test dataset comprising at least 3,000 genuine audio samples per target language and codec variant, demonstrating zero false alarms at a 95% statistical confidence level[cite: 42].
  * *Sample Size Derivation [engineering estimate]:*
    $$n \ge \frac{\ln(1 - 0.95)}{\ln(1 - 0.001)} = \frac{\ln(0.05)}{\ln(0.999)} \approx 2{,}995 \text{ samples}$$
  Model performance must be reported as *Recall at 0.1% FPR*, rather than Equal Error Rate (EER)[cite: 42].
* **NFR-3.2 (Abstention Policy under Uncertainty):** When conformal confidence bounds indicate statistical ambiguity or when incoming media suffers from excessive background noise or bitrate truncation, the system must abstain from issuing an automated Red or Green verdict and default to the protective Amber (Unverified) operational state[cite: 41, 42].

---

### 2.5 Threat Modeling & Operational Boundaries

#### 2.5.1 In-Scope Capabilities
1. **Asynchronous Audio Triage:** Detection of synthetic speech, voice conversion, and neural cloning in pre-recorded, forwarded audio voice messages[cite: 42].
2. **Textual Social Engineering:** Identification of deceptive pretexting, artificial urgency, and impersonation of public agencies in digital chat messages[cite: 40, 41].
3. **Domain Spoofing:** Detection of lookalike URLs, unregistered top-level domains, and character-substitution attacks targeting UAE infrastructure[cite: 41, 42].

#### 2.5.2 Out-of-Scope Capabilities
1. **Live Synchronous Voice Calls:** Project Hares cannot intercept or inspect real-time GSM or VoIP telephony[cite: 42]. Scams executed via live interactive calls fall outside system inspection capabilities; users are directed to hang up and verify callers via official directories[cite: 42].
2. **Dynamic In-Session Phishing Proxies:** Real-time man-in-the-middle credential interception sessions (which bypass OTPs dynamically) cannot be actively blocked at the network level by a messaging bot[cite: 40, 42].
3. **Endpoint Device Forensics:** The system does not analyze mobile device malware, Spyware, or compromised operating system runtimes[cite: 42].

---

### 2.6 Evaluation Protocol & Benchmarking Standards

#### 2.6.1 Reference Evaluation Datasets
Prior to production deployment, all model pipelines must undergo structured benchmarking across four designated datasets[cite: 42]:
1. **In-Domain Genuine UAE Audio Dataset:** A minimum of 3,000 authentic voice samples recorded by consenting native speakers across Gulf Arabic, Modern Standard Arabic, English, Urdu, and Hindi, compressed using the WhatsApp Opus voice profile[cite: 42].
2. **Synthetic Voice Evaluation Set:** A minimum of 1,000 synthetic audio clips generated across varied text-to-speech (TTS) and voice conversion (VC) architectures, evaluated under identical Opus compression constraints[cite: 42].
3. **Localized Text Evaluation Corpus:** A minimum of 1,000 verified UAE-specific scam lures benchmarked against 1,000 authentic municipal notification templates[cite: 42].
4. **Adversarial Jailbreak & Injection Suite:** A battery of prompt injection strings, jailbreak attempts, and character-level obfuscations designed to test LLM containment[cite: 41, 42].

#### 2.6.2 Reporting Metrics & Disaggregation
* Model evaluations must disaggregate performance by target language and audio bitrate[cite: 42].
* Text classification models must demonstrate a minimum of 95% recall on high-urgency fraudulent payment extraction while maintaining zero false alarms on the allowlisted municipal template set[cite: 42].
* Automated PII sanitization pipelines must demonstrate $\ge 99.5\%$ recall in identifying and stripping UAE telephone numbers, national IDs, and bank account numbers in mixed Arabic/English text payloads[cite: 42].