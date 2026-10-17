import io
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from hares.main import app

client = TestClient(app)


def test_triage_allowlisted_url():
    """Submitting a verified official UAE domain emits a GREEN verdict."""
    response = client.post(
        "/api/v1/triage/verify",
        data={"url": "https://ecrime.ae/report"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "GREEN"
    assert data["rule_triggered"] == "official_allowlist_match" or "allowlist" in data["rule_triggered"]
    assert "Verified Official" in data["reason"] or "allowlist" in data["reason"].lower() or "ecrime.ae" in data["reason"]
    assert data["allowlist_match"] is not None
    assert data["allowlist_match"]["verified_domain"] == "ecrime.ae"
    assert data["risk_score"] < 0.1


def test_triage_homograph_spoofed_domain():
    """Submitting a homograph spoof lookalike domain emits a RED verdict with escalation."""
    response = client.post(
        "/api/v1/triage/verify",
        data={"url": "http://xn--dubaipolice-97a.ae/pay"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "RED"
    assert "homograph" in data["rule_triggered"]
    assert data["risk_score"] >= 0.8
    assert data["escalation_url"] == "https://www.ecrime.ae"
    assert data["police_contact"] == "901"
    assert data["homograph_analysis"] is not None
    assert data["homograph_analysis"]["is_spoof"] is True


def test_triage_social_engineering_text():
    """Submitting urgent coercive social engineering text triggers SLM evaluation."""
    phishing_text = (
        "URGENT: Your Dubai Police traffic fine #98124 is unpaid. "
        "Pay immediately within 2 hours at http://police-fine-quick.cc or your Emirates ID will be cancelled."
    )
    response = client.post(
        "/api/v1/triage/verify",
        data={"text": phishing_text},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "RED"
    assert data["escalation_url"] == "https://www.ecrime.ae"
    assert "http://police-fine-quick.cc" in data["extracted_entities"]["urls"] or "police-fine-quick.cc" in data["extracted_entities"]["domains"]


def test_triage_image_upload():
    """Submitting an image screenshot processes through OCR."""
    img = Image.new("RGB", (300, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    response = client.post(
        "/api/v1/triage/verify",
        data={"text": "Please check this screenshot"},
        files={"file": ("screenshot.png", buf.getvalue(), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["input_type_detected"] == "image"
    assert data["verdict"] in ["RED", "AMBER", "GREEN"]


def test_triage_audio_upload():
    """Submitting an audio file triggers HTTP 503 during model retraining lockdown."""
    import struct
    import math

    # Generate 1.0 second 16kHz sine wave PCM in WAV format
    sample_rate = 16000
    num_samples = sample_rate
    pcm_data = bytearray()
    for i in range(num_samples):
        val = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
        pcm_data.extend(struct.pack("<h", val))

    # Basic WAV header
    wav_header = bytearray(b"RIFF")
    wav_header.extend(struct.pack("<I", 36 + len(pcm_data)))
    wav_header.extend(b"WAVEfmt ")
    wav_header.extend(struct.pack("<I", 16))
    wav_header.extend(struct.pack("<H", 1))  # PCM
    wav_header.extend(struct.pack("<H", 1))  # 1 channel
    wav_header.extend(struct.pack("<I", sample_rate))
    wav_header.extend(struct.pack("<I", sample_rate * 2))
    wav_header.extend(struct.pack("<H", 2))
    wav_header.extend(struct.pack("<H", 16))
    wav_header.extend(b"data")
    wav_header.extend(struct.pack("<I", len(pcm_data)))
    wav_bytes = bytes(wav_header + pcm_data)

    response = client.post(
        "/api/v1/triage/verify",
        files={"file": ("voicenote.wav", wav_bytes, "audio/wav")},
    )
    assert response.status_code == 503
    data = response.json()
    assert "retraining" in data["detail"].lower()
    assert "offline" in data["detail"].lower()


def test_triage_empty_request():
    """Empty request returns 400 Bad Request."""
    response = client.post(
        "/api/v1/triage/verify",
        data={"text": ""},
    )
    assert response.status_code == 400
