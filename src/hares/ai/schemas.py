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
    "none",
]


class TextTriageInferenceResult(BaseModel):
    """
    Structured SLM Intent and Social Engineering Classification Result (FR-2.4).
    Constrained at the token generation level via Guided JSON Decoding (Outlines/vLLM).
    """
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
        description="Whether message employs artificial urgency (e.g., immediate account suspension or impound threat)",
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
        description="Sanitized concise justification for the classification without echoing citizen PII",
    )


class AudioTriageInferenceResult(BaseModel):
    """
    Structured Audio Anti-Spoofing and Deepfake Detection Result (FR-1.2, FR-1.4).
    Integrates raw acoustic anomaly score with conformal statistical calibration.
    """
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    is_synthetic: bool = Field(
        ...,
        description="Whether the voice note is classified as synthetic/deepfake speech",
    )
    non_conformity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Non-conformity score s(x) = 1 - f_bonafide(x)",
    )
    p_value: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Conformal empirical p-value relative to genuine UAE reference distribution",
    )
    is_abstaining: bool = Field(
        ...,
        description="Whether the conformal evaluator abstains due to statistical ambiguity (routing to Amber)",
    )
    duration_seconds: float = Field(
        ...,
        ge=0.0,
        le=120.0,
        description="Audio duration in seconds (capped at 120s per FR-1.5)",
    )
    spectral_anomaly_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Raw acoustic/spectral artifact score from neural feature extractor",
    )


class ASRResult(BaseModel):
    """
    Automatic Speech Recognition Output (FR-1.1).
    Transcribes voice note speech into structured text for downstream triage.
    """
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    text: str = Field(..., description="Transcribed audio speech text")
    detected_language: str = Field(
        ...,
        description="ISO language code of primary detected speech (e.g., 'ar', 'en', 'ur', 'hi')",
    )
    duration_seconds: float = Field(..., ge=0.0, description="Audio length in seconds")


class UnifiedAudioTriageResult(BaseModel):
    """
    Unified Audio Triage Output (Phase 5 - Unified Whisper Dual-Head Architecture).
    Combines ASR text transcription and acoustic deepfake classification from a single forward pass.
    """
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    transcript_text: str = Field(..., description="Transcribed audio speech text")
    detected_language: str = Field(..., description="ISO language code (e.g., 'ar', 'en', 'ur')")
    is_synthetic: bool = Field(..., description="Whether audio is classified as synthetic voice clone/deepfake")
    non_conformity_score: float = Field(..., ge=0.0, le=1.0, description="Non-conformity score s(x)")
    p_value: float = Field(..., ge=0.0, le=1.0, description="Conformal empirical p-value")
    is_abstaining: bool = Field(..., description="Whether conformal evaluator abstains (routes to Amber)")
    duration_seconds: float = Field(..., ge=0.0, le=120.0, description="Audio duration in seconds")
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Raw acoustic deepfake anomaly score from MLP head")
    verdict_band: Literal["RED", "GREEN", "AMBER"] = Field(..., description="Tri-band classification verdict")
