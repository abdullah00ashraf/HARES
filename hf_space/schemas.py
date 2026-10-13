"""
Project Hares: Sovereign Triage Data Contracts.
"""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

TacticType = Literal[
    "traffic_fine_lure",
    "courier_delivery_fee",
    "banking_kyc_freeze",
    "lottery_prize",
    "account_suspension",
    "prompt_injection",
    "crypto_investment",
    "utility_freeze",
    "credential_harvesting",
    "none",
]


class TextTriageInferenceResult(BaseModel):
    """Structured SLM Intent and Social Engineering Classification Result (FR-2.4)."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    is_impersonation: bool = Field(
        ...,
        description="Whether message impersonates an official government or commercial entity",
    )
    impersonated_entity: str | None = Field(
        default=None,
        description="Name of the impersonated authority (e.g. 'Dubai Police', 'Emirates Post', 'DEWA', 'Salik')",
    )
    urgency_or_coercion: bool = Field(
        ...,
        description="Whether message employs artificial urgency",
    )
    financial_or_credential_demand: bool = Field(
        ...,
        description="Whether message demands payments, OTP codes, credit card details, or banking credentials",
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Model confidence score between 0.0 and 1.0",
    )
    detected_tactics: list[TacticType] = Field(
        default_factory=list,
        description="Identified social engineering tactic categories",
    )
    reasoning_summary: str = Field(
        ...,
        description="Sanitized concise justification without echoing citizen PII",
    )
