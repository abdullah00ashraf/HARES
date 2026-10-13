---
title: Project Hares Sovereign Neural Triage Engine
emoji: 🛡️
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 5.20.0
app_file: app.py
pinned: false
license: apache-2.0
short_description: UAE Sovereign Fraud Triage with NeMo Guardrails
---

# Project Hares (مشروع حارس) — Sovereign Neural Triage Engine

Autonomous cyber fraud triage, adversarial prompt injection containment, and municipal threat intelligence engine for Dubai & the United Arab Emirates.

## Architecture
- **Base Model:** [`abdullahashraf122/hares-qwen2.5-3b`](https://huggingface.co/abdullahashraf122/hares-qwen2.5-3b)
- **ZeroGPU Acceleration:** Dynamic NVIDIA A100 (80GB) execution via `@spaces.GPU`
- **Safety Rails:** NVIDIA NeMo Guardrails (Colang 2.0)
- **Compliance:** FR-4.1 (Zero Citizen PII Retention), NFR-1.3 (Prompt Injection Immunity), FR-3.1 (Official Dubai Police e-Crime Binding)
