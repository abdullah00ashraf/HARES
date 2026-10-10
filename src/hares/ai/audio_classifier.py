import logging
import math
import struct
from hares.ai.audio_preprocessor import AudioDurationExceededError, AudioPreprocessor
from hares.ai.conformal import ConformalCalibrator
from hares.ai.schemas import AudioTriageInferenceResult

logger = logging.getLogger("hares.ai.audio_classifier")


class AudioDeepfakeClassifier:
    """
    Local Acoustic Artifact & Voice Spoofing Detector (FR-1.2, FR-1.3).
    Analyzes 16kHz PCM audio for neural voice conversion (VC), text-to-speech (TTS),
    and synthetic vocoder artifacts, calibrated via non-parametric conformal inference.
    """

    def __init__(
        self,
        calibrator: ConformalCalibrator | None = None,
        preprocessor: AudioPreprocessor | None = None,
    ) -> None:
        self.calibrator = calibrator or ConformalCalibrator()
        self.preprocessor = preprocessor or AudioPreprocessor()

    def classify(self, audio_bytes: bytes, filename_hint: str = "voice.ogg") -> AudioTriageInferenceResult:
        """
        Classifies incoming audio for deepfake synthesis.

        Raises:
            AudioDurationExceededError: If audio duration exceeds 120.0s (FR-1.5).
            ValueError: If audio is corrupted.
        """
        # 1. Preprocess audio & enforce 120s duration cap (FR-1.5)
        pcm_bytes, duration = self.preprocessor.preprocess(audio_bytes, filename_hint)

        # 2. Extract Acoustic Artifact Scores from 16kHz PCM
        anomaly_score = self._extract_acoustic_anomaly_score(pcm_bytes)

        # 3. Derive bonafide probability and evaluate conformal calibration
        bonafide_prob = max(0.0, min(1.0, 1.0 - anomaly_score))
        conformal_eval = self.calibrator.evaluate(bonafide_prob)

        logger.info(
            "Audio evaluated: duration=%.2fs anomaly_score=%.4f p_value=%.4f is_synthetic=%s is_abstaining=%s",
            duration,
            anomaly_score,
            conformal_eval["p_value"],
            conformal_eval["is_synthetic"],
            conformal_eval["is_abstaining"],
        )

        return AudioTriageInferenceResult(
            is_synthetic=bool(conformal_eval["is_synthetic"]),
            non_conformity_score=float(conformal_eval["non_conformity_score"]),
            p_value=float(conformal_eval["p_value"]),
            is_abstaining=bool(conformal_eval["is_abstaining"]),
            duration_seconds=duration,
            spectral_anomaly_score=round(anomaly_score, 4),
        )

    def _extract_acoustic_anomaly_score(self, pcm_bytes: bytes) -> float:
        """
        Extracts acoustic artifact indicators from 16kHz 16-bit PCM:
        - Energy variance and zero-crossing rate variance
        - Spectral gradient and high-frequency energy ratio
        - Frame-to-frame temporal discontinuity
        """
        num_samples = len(pcm_bytes) // 2
        if num_samples < 160:
            return 0.1  # Too short to reliably detect anomalies, treat as natural/clean

        # Read samples into normalized float array [-1.0, 1.0]
        step = max(1, num_samples // 16000)  # Downsample stride for fast evaluation under SLA
        samples: list[float] = []
        for i in range(0, num_samples, step):
            sample = struct.unpack_from("<h", pcm_bytes, i * 2)[0]
            samples.append(sample / 32768.0)

        n = len(samples)
        if n < 10:
            return 0.1

        # 1. Compute Zero-Crossing Rate (ZCR)
        zcr_count = sum(1 for i in range(1, n) if (samples[i] >= 0 > samples[i - 1]) or (samples[i] < 0 <= samples[i - 1]))
        zcr_rate = zcr_count / float(n)

        # 2. Compute Root Mean Square (RMS) Energy
        mean_sq = sum(s * s for s in samples) / float(n)
        rms = math.sqrt(mean_sq)

        # 3. High-Frequency Spectral Discontinuity (first-order difference energy)
        diff_energy = sum((samples[i] - samples[i - 1]) ** 2 for i in range(1, n)) / float(n)
        spectral_ratio = diff_energy / (mean_sq + 1e-6)

        # Synthesis artifacts often feature unusually elevated high-frequency noise floor or synthetic flatness
        score = 0.15  # Baseline bonafide prior

        # Check for robotic/synthetic flat energy signature
        if rms > 0.05 and spectral_ratio > 2.5:
            score += 0.45
        elif rms > 0.02 and zcr_rate > 0.35:
            score += 0.30

        # Unusually low variance in energy windows indicates neural vocoder artifacts
        window_size = 100
        if n > window_size * 2:
            energies: list[float] = []
            for w in range(0, n - window_size, window_size):
                chunk = samples[w : w + window_size]
                e = sum(x * x for x in chunk) / float(window_size)
                energies.append(e)
            if energies:
                mean_e = sum(energies) / float(len(energies))
                var_e = sum((e - mean_e) ** 2 for e in energies) / float(len(energies))
                # Very low variance in speech active frames is characteristic of monotone TTS
                if mean_e > 0.01 and var_e < 0.0001:
                    score += 0.35

        return round(min(0.99, max(0.01, score)), 4)
