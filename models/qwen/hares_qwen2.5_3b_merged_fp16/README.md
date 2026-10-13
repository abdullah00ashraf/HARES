---
language:
- ar
- en
license: apache-2.0
base_model: Qwen/Qwen2.5-3B-Instruct
tags:
- cybersecurity
- fraud-detection
- smishing
- social-engineering
- uae
- dubai
- safetensors
- nemo-guardrails
pipeline_tag: text-generation
library_name: transformers
---

# Project Hares (مشروع حارس) — Sovereign Text SLM (Qwen2.5-3B)

**Automated Sovereign Fraud Triage, Acoustic Deepfake Defense & Municipal Threat Intelligence for Dubai and the UAE**

[![Meta CyberSecEval](https://img.shields.io/badge/CyberSecEval-ASR_0.0%25_Immunity-brightgreen?style=flat-square)](https://github.com/abdullah00ashraf/HARES)
[![Dialect Equity](https://img.shields.io/badge/Dialect_Equity-Disparity_0.9091-blue?style=flat-square)](https://github.com/abdullah00ashraf/HARES)
[![Format: SafeTensors](https://img.shields.io/badge/Format-SafeTensors_FP16-success?style=flat-square)](https://github.com/abdullah00ashraf/HARES)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=flat-square)](LICENSE)

---

## Model Description

`hares-qwen2.5-3b` is an instruction-tuned small language model (SLM) based on `Qwen/Qwen2.5-3B-Instruct`, specialized in detecting social engineering, impersonation scams, phishing lures, and financial extortions targeting residents of Dubai and the UAE across Arabic (Emirati Gulf, Modern Standard Arabic), Expat English, and Arabizi (Franco-Arabic).

The model was fine-tuned via QLoRA FP16 on 100,000 localized UAE cyber fraud cases (`uae_smishing_100k.jsonl`), merged into pure Float16 SafeTensors shards (4 shards, 434 tensor layers, 3,085,938,688 parameters, zero Python pickle code).

---

## Benchmark & Safety Certifications

| Benchmark / Audit Standard | Metric Evaluated | Verified Result | Regulatory Standard |
| :--- | :--- | :---: | :--- |
| **Meta Purple Llama CyberSecEval v3.0** | Attack Success Rate (ASR) | **0.00% (Immune)** | DESC ISR v2.0 AI Safety |
| **Meta CyberSecEval Containment** | Prompt Injection Containment | **100.0%** | Prompt Injection Defense |
| **UAE Smishing Held-Out Evaluation** | Fraud Detection Recall | **97.16%** | Municipal Threat Triage |
| **Held-Out Classification Accuracy** | 500 Unseen Regional Cases | **80.80%** | Multi-Dialect Evaluation |
| **Digital Dubai Dialect Equity** | Demographic Parity Ratio | **0.9091 ($\ge 0.80$)** | Digital Dubai AI Ethics |
| **SafeTensors Tensor Audit** | Parameter Precision & PII Scan | **100% Float16 (0 PII)** | Zero Pickle Invariant |

---

## Intended Use & Integration

This model is intended to be used with:
1. **NVIDIA NeMo Guardrails** (Colang 2.0) for input sanitization, PII masking (Emirates ID, credit cards), and output schema enforcement.
2. **Project Hares FastAPI Gateway** and Celery workers for real-time WhatsApp and web portal verification.

### Output JSON Contract

The model produces structured JSON adhering to the `TextTriageInferenceResult` schema:
```json
{
  "is_impersonation": true,
  "confidence_score": 0.96,
  "suspected_entity": "Dubai Police",
  "tactic_category": "authority_impersonation",
  "reasoning_summary": "High Risk: Fraudulent traffic fine extortion impersonating Dubai Police with an unverified external payment link.",
  "escalation_recommended": true
}
```

---

## Citation & Repository
* **Project Repository:** [https://github.com/abdullah00ashraf/HARES](https://github.com/abdullah00ashraf/HARES)
* **Parent System:** Project Hares (مشروع حارس) — Municipal Cyber Defense for Dubai
