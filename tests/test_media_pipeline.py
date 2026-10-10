import pytest
from unittest.mock import patch
from hares.engine.verdict import TriageVerdict, VerdictSynthesizer
from hares.services.media_downloader import MediaDownloader
from hares.services.whatsapp_client import WhatsAppClient
from hares.workers.tasks import process_incoming_webhook


def test_media_downloader_mock_flow():
    downloader = MediaDownloader()
    audio_bytes, mime = downloader.fetch_media("mock_media_12345")
    assert len(audio_bytes) > 0
    assert "audio" in mime


def test_media_downloader_invalid_id():
    downloader = MediaDownloader()
    with pytest.raises(ValueError):
        downloader.fetch_media("")


def test_whatsapp_client_format_red_escalation():
    client = WhatsAppClient()
    synthesizer = VerdictSynthesizer()
    red_verdict = synthesizer.build_red_verdict(
        rule_triggered="spoof_detected",
        reason="Detected deceptive UAE entity spoofing",
        indicators=["dewaa.ae"],
    )
    msg_body = client._format_message_body(red_verdict)
    assert "https://www.ecrime.ae" in msg_body
    assert "901" in msg_body
    assert "عالي الخطورة" in msg_body
    assert "HIGH RISK" in msg_body


def test_whatsapp_client_send_verdict_reply_mock():
    client = WhatsAppClient()
    synthesizer = VerdictSynthesizer()
    amber_verdict = synthesizer.build_amber_verdict(reason="Unverified link")
    resp = client.send_verdict_reply("+971501234567", amber_verdict)
    assert resp["status"] == "delivered_mock"
    assert resp["verdict"] == TriageVerdict.AMBER.value


def test_process_incoming_webhook_voice_note_flow():
    # WhatsApp webhook payload containing a voice message
    voice_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "100200300",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "9714000000", "phone_number_id": "11223344"},
                            "messages": [
                                {
                                    "from": "971509998877",
                                    "id": "wamid.AUDIO_TEST_001",
                                    "timestamp": "1710000000",
                                    "type": "audio",
                                    "audio": {
                                        "id": "mock_media_audio_001",
                                        "mime_type": "audio/ogg; codecs=opus",
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    result = process_incoming_webhook(voice_payload)
    assert result["status"] == "processed"
    assert result["messages_handled"] == 1
    assert len(result["verdicts"]) == 1
    assert result["verdicts"][0]["message_id"] == "wamid.AUDIO_TEST_001"
    assert result["verdicts"][0]["verdict"] in [TriageVerdict.RED.value, TriageVerdict.AMBER.value, TriageVerdict.GREEN.value]
