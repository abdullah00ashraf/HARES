import logging
import math
import os
import re
import threading
import time
from collections import deque
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

logger = logging.getLogger("hares.benchmarks.mock_meta_sink")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="Meta WhatsApp Cloud API Mock Egress Sink",
    description="Captures outbound verdict replies and serves synthetic media for Project Hares E2E benchmark.",
    version="1.0.0",
)


class LatencyTracker:
    """
    Thread-safe latency tracker computing percentiles (p50, p95, p99)
    for end-to-end triage turnaround: Delta t = t_outbound - t_inbound.
    """

    def __init__(self, max_samples: int = 50000) -> None:
        self._lock = threading.Lock()
        self._samples_ms: deque[float] = deque(maxlen=max_samples)
        self._total_dispatches: int = 0
        self._timestamps_recorded: int = 0

    def record_e2e(self, latency_ms: float) -> None:
        with self._lock:
            self._samples_ms.append(latency_ms)
            self._total_dispatches += 1
            self._timestamps_recorded += 1

    def record_dispatch_without_timestamp(self) -> None:
        with self._lock:
            self._total_dispatches += 1

    def reset(self) -> None:
        with self._lock:
            self._samples_ms.clear()
            self._total_dispatches = 0
            self._timestamps_recorded = 0

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
            count = len(self._samples_ms)
            if count == 0:
                return {
                    "total_dispatches": self._total_dispatches,
                    "samples_count": 0,
                    "p50_latency_ms": 0.0,
                    "p95_latency_ms": 0.0,
                    "p99_latency_ms": 0.0,
                    "min_latency_ms": 0.0,
                    "max_latency_ms": 0.0,
                    "avg_latency_ms": 0.0,
                }

            sorted_samples = sorted(self._samples_ms)

            def _percentile(p: float) -> float:
                k = (len(sorted_samples) - 1) * p
                f = math.floor(k)
                c = math.ceil(k)
                if f == c:
                    return sorted_samples[int(k)]
                d0 = sorted_samples[int(f)] * (c - k)
                d1 = sorted_samples[int(c)] * (k - f)
                return d0 + d1

            return {
                "total_dispatches": self._total_dispatches,
                "samples_count": count,
                "p50_latency_ms": round(_percentile(0.50), 2),
                "p95_latency_ms": round(_percentile(0.95), 2),
                "p99_latency_ms": round(_percentile(0.99), 2),
                "min_latency_ms": round(sorted_samples[0], 2),
                "max_latency_ms": round(sorted_samples[-1], 2),
                "avg_latency_ms": round(sum(sorted_samples) / count, 2),
            }


tracker = LatencyTracker()
INGRESS_REGEX = re.compile(r"\[T_INGRESS:(\d+)\]")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "service": "hares-mock-meta-sink"}


@app.get("/stats")
async def get_stats() -> dict[str, Any]:
    return tracker.get_stats()


@app.post("/reset")
async def reset_stats() -> dict[str, str]:
    tracker.reset()
    return {"status": "reset_successful"}


@app.post("/v21.0/{phone_number_id}/messages")
@app.post("/{phone_number_id}/messages")
async def receive_outbound_message(phone_number_id: str, request: Request) -> dict[str, Any]:
    """
    Simulates Meta Cloud API: POST /{api_version}/{phone_number_id}/messages.
    Extracts embedded nanosecond timestamp from message body to compute E2E latency.
    """
    t_outbound_ns = time.time_ns()
    payload = await request.json()

    recipient = payload.get("to", "unknown")
    text_obj = payload.get("text", {})
    body = text_obj.get("body", "")

    # Check for embedded ingress timestamp [T_INGRESS:...]
    match = INGRESS_REGEX.search(body)
    if match:
        t_ingress_ns = int(match.group(1))
        latency_ms = (t_outbound_ns - t_ingress_ns) / 1_000_000.0
        if latency_ms >= 0:
            tracker.record_e2e(latency_ms)
        else:
            tracker.record_dispatch_without_timestamp()
    else:
        tracker.record_dispatch_without_timestamp()

    return {
        "messaging_product": "whatsapp",
        "contacts": [{"input": recipient, "wa_id": recipient}],
        "messages": [{"id": f"wamid.HBgL{t_outbound_ns}"}],
    }


@app.get("/v21.0/{media_id}")
@app.get("/{media_id}")
async def get_media_metadata(media_id: str, request: Request) -> dict[str, Any]:
    """
    Simulates Meta Cloud API: GET /{api_version}/{media_id}.
    Returns a temporary CDN download URL.
    """
    host = request.headers.get("host", "127.0.0.1:8001")
    scheme = "http"
    download_url = f"{scheme}://{host}/media/download/{media_id}"

    return {
        "url": download_url,
        "mime_type": "audio/ogg; codecs=opus",
        "sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
        "file_size": 32000,
        "id": media_id,
        "messaging_product": "whatsapp",
    }


@app.get("/media/download/{media_id}")
async def download_media(media_id: str) -> Response:
    """
    Simulates Meta CDN binary stream: GET {download_url}.
    Returns synthetic 16kHz audio bytes.
    """
    # 1 second of synthetic 16kHz mono 16-bit PCM (32,000 bytes)
    synthetic_audio = b"\x00\x00" * 16000
    return Response(
        content=synthetic_audio,
        media_type="audio/ogg; codecs=opus",
        headers={"Content-Disposition": f'attachment; filename="{media_id}.ogg"'},
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("MOCK_META_PORT", 8001))
    uvicorn.run("benchmarks.mock_meta_sink:app", host="0.0.0.0", port=port, log_level="info")
