import json
import logging
import os
import random
import sys
import time
from typing import Any

from locust import HttpUser, between, task

ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(ROOT_PATH, "src")
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from hares.core.config import get_settings
from benchmarks.traffic_payloads import (
    TEXT_LURES,
    compute_meta_hub_signature,
    create_meta_webhook_payload,
)

logger = logging.getLogger("hares.benchmarks.locustfile")


class HaresTrafficGenerator(HttpUser):
    """
    Locust traffic generator simulating 200 QPS citizen traffic split:
    - 85% Text Triage (Traffic, Banking, Courier lures with embedded nanosecond timestamps)
    - 15% Audio Triage (Synthetic voice notes simulating spoofing & deepfake scams)
    """

    wait_time = between(0.001, 0.005)

    def on_start(self) -> None:
        settings = get_settings()
        self.app_secret = settings.WHATSAPP_APP_SECRET

    @task(85)
    def submit_text_triage(self) -> None:
        """Simulates citizen forwarding suspicious SMS / WhatsApp text message (85% load)."""
        t_ingress_ns = time.time_ns()
        lure = random.choice(TEXT_LURES)
        # Embed nanosecond ingress timestamp into message body for end-to-end latency tracking
        body = f"[T_INGRESS:{t_ingress_ns}] {lure}"

        sender_phone = f"97150{random.randint(1000000, 9999999)}"
        msg_id = f"stress_text_{t_ingress_ns}_{random.randint(1000, 9999)}"

        payload_dict = create_meta_webhook_payload(
            msg_type="text",
            content={"body": body},
            sender_phone=sender_phone,
            msg_id=msg_id,
        )
        payload_bytes = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
        signature = compute_meta_hub_signature(payload_bytes, self.app_secret)

        headers = {
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        }

        with self.client.post(
            "/api/v1/webhook",
            data=payload_bytes,
            headers=headers,
            catch_response=True,
            name="/api/v1/webhook [text]",
        ) as response:
            if response.status_code == 200 and response.json().get("status") == "queued":
                response.success()
            else:
                response.failure(f"Unexpected text response: {response.status_code} - {response.text}")

    @task(15)
    def submit_audio_triage(self) -> None:
        """Simulates citizen forwarding suspicious voice note (15% load)."""
        t_ingress_ns = time.time_ns()
        media_id = f"mock_media_stress_{random.randint(1000, 9999)}"

        sender_phone = f"97150{random.randint(1000000, 9999999)}"
        msg_id = f"stress_audio_{t_ingress_ns}_{random.randint(1000, 9999)}"

        payload_dict = create_meta_webhook_payload(
            msg_type="audio",
            content={"id": media_id, "mime_type": "audio/ogg; codecs=opus"},
            sender_phone=sender_phone,
            msg_id=msg_id,
        )
        payload_bytes = json.dumps(payload_dict, separators=(",", ":")).encode("utf-8")
        signature = compute_meta_hub_signature(payload_bytes, self.app_secret)

        headers = {
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        }

        with self.client.post(
            "/api/v1/webhook",
            data=payload_bytes,
            headers=headers,
            catch_response=True,
            name="/api/v1/webhook [audio]",
        ) as response:
            if response.status_code == 200 and response.json().get("status") == "queued":
                response.success()
            else:
                response.failure(f"Unexpected audio response: {response.status_code} - {response.text}")
