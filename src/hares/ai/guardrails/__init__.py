"""
Project Hares: Sovereign Programmable Guardrails Engine.

Built on NVIDIA NeMo Guardrails, this module enforces deterministic safety boundaries:
1. Input Rails: Class B Citizen PII Masking & Adversarial Prompt Injection Defense.
2. Dialog Rails: Topical Cyber Fraud & Phishing Triage Bounding.
3. Output Rails: Pydantic v2 Schema Enforcement & Dubai Police Escalation Verification.
"""

from __future__ import annotations

from hares.ai.guardrails.engine import GuardrailResult, SovereignGuardrailsEngine

__all__ = [
    "SovereignGuardrailsEngine",
    "GuardrailResult",
]
