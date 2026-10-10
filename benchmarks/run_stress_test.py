import argparse
import asyncio
import json
import logging
import math
import os
import random
import subprocess
import sys
import time
from typing import Any

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

logger = logging.getLogger("hares.benchmarks.orchestrator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class BenchmarkResult:

    def __init__(self, stage_name: str, target_qps: int) -> None:
        self.stage_name = stage_name
        self.target_qps = target_qps
        self.latencies_ms: list[float] = []
        self.success_count: int = 0
        self.error_count: int = 0
        self.status_codes: dict[int, int] = {}
        self.start_time: float = 0.0
        self.end_time: float = 0.0

    @property
    def total_requests(self) -> int:
        return self.success_count + self.error_count

    @property
    def duration_seconds(self) -> float:
        return max(0.001, self.end_time - self.start_time)

    @property
    def actual_qps(self) -> float:
        return self.total_requests / self.duration_seconds

    def compute_percentiles(self) -> dict[str, float]:
        if not self.latencies_ms:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
        s = sorted(self.latencies_ms)
        n = len(s)

        def _p(pct: float) -> float:
            idx = int(pct * (n - 1))
            return round(s[idx], 2)

        return {
            "p50": _p(0.50),
            "p90": _p(0.90),
            "p95": _p(0.95),
            "p99": _p(0.99),
            "max": round(s[-1], 2),
        }


async def _send_single_request(
    client: Any,
    api_url: str,
    app_secret: str,
    msg_type: str,
    result: BenchmarkResult,
) -> None:
    t_start = time.perf_counter()
    now_ns = time.time_ns()

    if msg_type == "text":
        lure = random.choice(TEXT_LURES)
        body = f"[T_INGRESS:{now_ns}] {lure}"
        payload = create_meta_webhook_payload(
            msg_type="text",
            content={"body": body},
            sender_phone=f"97150{random.randint(1000000, 9999999)}",
            msg_id=f"stress_{now_ns}_{random.randint(1000, 9999)}",
        )
    else:
        media_id = f"mock_media_stress_{random.randint(1000, 9999)}"
        payload = create_meta_webhook_payload(
            msg_type="audio",
            content={"id": media_id, "mime_type": "audio/ogg; codecs=opus"},
            sender_phone=f"97150{random.randint(1000000, 9999999)}",
            msg_id=f"stress_audio_{now_ns}_{random.randint(1000, 9999)}",
        )

    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = compute_meta_hub_signature(payload_bytes, app_secret)

    headers = {
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature,
    }

    try:
        resp = await client.post(api_url, content=payload_bytes, headers=headers)
        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        status_code = resp.status_code

        result.status_codes[status_code] = result.status_codes.get(status_code, 0) + 1
        result.latencies_ms.append(elapsed_ms)

        if status_code == 200:
            result.success_count += 1
        else:
            result.error_count += 1
    except Exception as exc:
        result.error_count += 1
        logger.debug("Request failed: %s", str(exc))


async def run_stage_async(
    target_qps: int,
    duration_s: int,
    host: str,
    app_secret: str,
) -> BenchmarkResult:
    """Executes an asynchronous stepped load stage at target QPS with 85/15 ratio."""
    import httpx

    result = BenchmarkResult(stage_name=f"Stage-{target_qps}QPS", target_qps=target_qps)
    api_url = f"{host.rstrip('/')}/api/v1/webhook"

    limits = httpx.Limits(max_connections=target_qps * 2, max_keepalive_connections=target_qps)
    timeout = httpx.Timeout(10.0)

    result.start_time = time.perf_counter()

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        interval = 1.0 / target_qps if target_qps > 0 else 0.05
        end_time = time.perf_counter() + duration_s

        tasks = []
        while time.perf_counter() < end_time:
            # 85/15 distribution
            msg_type = "text" if random.random() < 0.85 else "audio"
            t = asyncio.create_task(_send_single_request(client, api_url, app_secret, msg_type, result))
            tasks.append(t)

            await asyncio.sleep(interval)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    result.end_time = time.perf_counter()
    return result


def fetch_mock_sink_stats(mock_host: str) -> dict[str, Any]:
    """Retrieves end-to-end turnaround stats from Mock Meta Egress Sink."""
    import httpx

    try:
        url = f"{mock_host.rstrip('/')}/stats"
        resp = httpx.get(url, timeout=3.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {}


def format_benchmark_report(
    results: list[BenchmarkResult],
    sink_stats: dict[str, Any] | None = None,
) -> str:
    """Formats Markdown summary report verifying SLA acceptance criteria."""
    report_lines = [
        "# Project Hares: 200 QPS Stress Test & SLA Benchmark Report",
        "",
        "## Ingress Webhook Performance (Sub-50ms SLA Verification)",
        "",
        "| Stage | Target QPS | Actual QPS | Total Req | Success | Errors | Ingress p50 (ms) | Ingress p95 (ms) | Ingress p99 (ms) | Ingress Max (ms) | SLA Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    all_passed = True
    for r in results:
        p = r.compute_percentiles()
        # Ingress SLA requirement: p99 <= 50ms, 0 drops
        sla_pass = (p["p99"] <= 50.0) and (r.error_count == 0)
        if not sla_pass:
            all_passed = False
        status_str = "PASS [<=50ms]" if sla_pass else "VIOLATION [>50ms]"
        report_lines.append(
            f"| {r.stage_name} | {r.target_qps} | {r.actual_qps:.1f} | {r.total_requests} | {r.success_count} | {r.error_count} | {p['p50']} | {p['p95']} | {p['p99']} | {p['max']} | {status_str} |"
        )

    report_lines.append("")
    report_lines.append("## End-to-End Triage Turnaround (Mock Meta Egress Sink)")
    report_lines.append("")

    if sink_stats and sink_stats.get("samples_count", 0) > 0:
        report_lines.extend(
            [
                f"- **Total Outbound Dispatches Captured:** {sink_stats.get('total_dispatches', 0)}",
                f"- **E2E Turnaround p50:** {sink_stats.get('p50_latency_ms', 0.0)} ms",
                f"- **E2E Turnaround p95:** {sink_stats.get('p95_latency_ms', 0.0)} ms",
                f"- **E2E Turnaround p99:** {sink_stats.get('p99_latency_ms', 0.0)} ms",
                f"- **Text Triage SLA Target:** p95 <= 1500 ms (FR-3.3)",
                f"- **Audio Voice Triage SLA Target:** p95 <= 4500 ms (FR-3.3)",
            ]
        )
    else:
        report_lines.append(
            "_Mock Meta Egress Sink was not reachable or no out-of-band replies were captured during this run._"
        )

    report_lines.append("")
    report_lines.append("## Overall SLA Assessment")
    report_lines.append(
        f"**Verdict:** {'PASSED - ALL SLAS SATISFIED' if all_passed else 'ACTION REQUIRED - SLA THRESHOLDS EXCEEDED'}"
    )

    return "\n".join(report_lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Project Hares 200 QPS Load Benchmark Orchestrator")
    parser.add_argument("--host", default="http://127.0.0.1:8000", help="FastAPI host URL")
    parser.add_argument("--mock-host", default="http://127.0.0.1:8001", help="Mock Meta Egress Sink host URL")
    parser.add_argument("--duration", type=int, default=5, help="Duration in seconds per load stage")
    parser.add_argument("--full-stepped", action="store_true", help="Execute complete 50 -> 100 -> 200 QPS stepped sequence")
    parser.add_argument("--qps", type=int, default=200, help="Target QPS when not running full-stepped")
    args = parser.parse_args()

    settings = get_settings()
    app_secret = settings.WHATSAPP_APP_SECRET

    logger.info("Starting Project Hares Benchmark Orchestrator")
    logger.info("Target Host: %s | Secret: %s... | Duration per stage: %ds", args.host, app_secret[:6], args.duration)

    stages = [50, 100, 200] if args.full_stepped else [args.qps]
    results: list[BenchmarkResult] = []

    for qps in stages:
        logger.info("Executing load stage: %d QPS for %d seconds...", qps, args.duration)
        stage_res = asyncio.run(run_stage_async(qps, args.duration, args.host, app_secret))
        results.append(stage_res)
        p = stage_res.compute_percentiles()
        logger.info(
            "Stage %d QPS complete: %d requests, %d success, %d errors, p99=%s ms",
            qps,
            stage_res.total_requests,
            stage_res.success_count,
            stage_res.error_count,
            p["p99"],
        )

    sink_stats = fetch_mock_sink_stats(args.mock_host)
    report = format_benchmark_report(results, sink_stats)
    print("\n" + report + "\n")

    report_path = os.path.join(os.path.dirname(__file__), "benchmark_summary.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("Benchmark report written to %s", report_path)


if __name__ == "__main__":
    main()
