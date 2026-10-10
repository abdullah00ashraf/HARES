import io
import math
import struct
import wave
import pytest
from hares.ai.audio_classifier import AudioDeepfakeClassifier
from hares.ai.audio_preprocessor import AudioDurationExceededError, AudioPreprocessor


def _generate_wav_bytes(duration_seconds: float, sample_rate: int = 16000, frequency: float = 440.0) -> bytes:
    """Generates standard in-memory WAV audio bytes for hermetic unit testing."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        n_frames = int(duration_seconds * sample_rate)
        frames = bytearray(n_frames * 2)
        for i in range(n_frames):
            val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
            struct.pack_into("<h", frames, i * 2, val)
        wf.writeframes(bytes(frames))
    return buf.getvalue()


def test_audio_duration_cap_allowed():
    preprocessor = AudioPreprocessor(max_duration_seconds=120.0)
    # 5 seconds of audio is well under 120s
    wav_bytes = _generate_wav_bytes(duration_seconds=5.0)
    pcm, duration = preprocessor.preprocess(wav_bytes)
    assert duration == pytest.approx(5.0, abs=0.1)
    assert len(pcm) == 5 * 16000 * 2


def test_audio_duration_cap_exceeded_raises_exception():
    preprocessor = AudioPreprocessor(max_duration_seconds=120.0)
    # 125 seconds of audio exceeds 120s limit (FR-1.5)
    wav_bytes = _generate_wav_bytes(duration_seconds=125.0)
    with pytest.raises(AudioDurationExceededError) as exc_info:
        preprocessor.preprocess(wav_bytes)
    assert "exceeds maximum allowed limit of 120.0s" in str(exc_info.value)


def test_audio_preprocessor_stereo_downmix():
    # Generate 1-second 2-channel WAV
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        n_frames = 16000
        frames = bytearray(n_frames * 4)
        for i in range(n_frames):
            struct.pack_into("<h", frames, i * 4, 1000)
            struct.pack_into("<h", frames, i * 4 + 2, 2000)
        wf.writeframes(bytes(frames))
    stereo_wav = buf.getvalue()

    preprocessor = AudioPreprocessor()
    mono_pcm, duration = preprocessor.preprocess(stereo_wav)
    assert duration == pytest.approx(1.0, abs=0.05)
    # Verify mono downmixed sample ( (1000 + 2000) // 2 = 1500 )
    first_sample = struct.unpack_from("<h", mono_pcm, 0)[0]
    assert first_sample == 1500


def test_audio_deepfake_classifier_benign_audio():
    classifier = AudioDeepfakeClassifier()
    # 2 seconds of smooth harmonic speech-like sine wave
    wav_bytes = _generate_wav_bytes(duration_seconds=2.0, frequency=220.0)
    res = classifier.classify(wav_bytes)
    assert res.duration_seconds == pytest.approx(2.0, abs=0.1)
    assert res.is_synthetic is False
    assert res.spectral_anomaly_score < 0.85


def test_audio_deepfake_classifier_corrupted_payload():
    classifier = AudioDeepfakeClassifier()
    with pytest.raises(ValueError):
        classifier.classify(b"too_short")
