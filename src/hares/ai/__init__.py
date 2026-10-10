"""
Project Hares: Local Sovereign AI Inference Cluster (NFR-1.1).
Contains schemas, small language model clients, ASR speech transcription,
acoustic deepfake detection, conformal calibration, and unified dual-head Whisper pipeline.
"""

from hares.ai.audio_pipeline import UnifiedAudioTriage, WhisperDeepfakeMLPHead
from hares.ai.audio_preprocessor import AudioDurationExceededError, AudioPreprocessor
from hares.ai.conformal import ConformalCalibrator
from hares.ai.schemas import (
    ASRResult,
    AudioTriageInferenceResult,
    TextTriageInferenceResult,
    UnifiedAudioTriageResult,
)

__all__ = [
    "TextTriageInferenceResult",
    "AudioTriageInferenceResult",
    "ASRResult",
    "UnifiedAudioTriageResult",
    "UnifiedAudioTriage",
    "WhisperDeepfakeMLPHead",
    "AudioPreprocessor",
    "AudioDurationExceededError",
    "ConformalCalibrator",
]
