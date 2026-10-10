import pytest
from hares.ai.asr_client import LocalASRClient
from hares.ai.schemas import ASRResult


def test_asr_empty_audio_returns_empty_result():
    client = LocalASRClient()
    res = client.transcribe(b"", duration_seconds=0.0)
    assert isinstance(res, ASRResult)
    assert res.text == ""
    assert res.duration_seconds == 0.0


def test_asr_transcribe_pcm_buffer():
    client = LocalASRClient()
    # 1 second of 16kHz PCM
    synthetic_pcm = b"\x00\x00" * 16000
    res = client.transcribe(synthetic_pcm, duration_seconds=1.0)
    assert isinstance(res, ASRResult)
    assert len(res.text) > 0
    assert res.detected_language in ["ar", "en", "ur", "hi"]
    assert res.duration_seconds == 1.0
