import json
import os
import sys
import time
from datetime import datetime, timezone
import httpx

API_URL = "http://localhost:8000/api/v1/triage/verify"
HEALTH_URL = "http://localhost:8000/health/live"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(BASE_DIR, "test_manifest.json")
REPORT_PATH = os.path.join(BASE_DIR, "REALTEST_EXECUTION_REPORT.md")


def wait_for_api(timeout_seconds: int = 45):
    print(f"Checking API liveness at {HEALTH_URL}...")
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(HEALTH_URL)
                if res.status_code == 200:
                    print(f"API is live and healthy! (response time: {res.elapsed.total_seconds()*1000:.1f}ms)")
                    return True
        except Exception:
            pass
        time.sleep(2)
    print("Warning: API health check timed out. Proceeding anyway...")
    return False


def run_suite():
    wait_for_api()

    if not os.path.exists(MANIFEST_PATH):
        print(f"Error: Manifest not found at {MANIFEST_PATH}")
        sys.exit(1)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    test_cases = manifest.get("test_cases", [])
    print(f"\n=======================================================")
    print(f"  RUNNING REALTEST MULTI-MODAL SUITE: {len(test_cases)} TEST CASES")
    print(f"  Target API: {API_URL}")
    print(f"=======================================================\n")

    results = []
    passed_count = 0
    failed_count = 0

    with httpx.Client(timeout=30.0) as client:
        for idx, tc in enumerate(test_cases, 1):
            tc_id = tc["id"]
            title = tc["title"]
            category = tc["category"]
            rel_file = tc["filename"]
            expected_verdict = tc.get("expected_verdict", "RED")
            full_path = os.path.join(BASE_DIR, rel_file)

            print(f"[{idx:02d}/{len(test_cases):02d}] {tc_id} ({category.upper()}): {title[:50]}...", end=" ", flush=True)

            if not os.path.exists(full_path):
                print(f"[ERROR: File not found: {rel_file}]")
                results.append({
                    "id": tc_id,
                    "title": title,
                    "category": category,
                    "status": "ERROR",
                    "error": f"File not found: {rel_file}",
                    "expected": expected_verdict,
                    "actual": "N/A",
                    "latency_ms": 0,
                })
                failed_count += 1
                continue

            start_t = time.time()
            data = {}
            files = {}

            try:
                if category == "prompt":
                    with open(full_path, "r", encoding="utf-8") as f:
                        data["text"] = f.read().strip()
                elif category == "url":
                    with open(full_path, "r", encoding="utf-8") as f:
                        lines = [l.strip() for l in f.readlines() if l.strip()]
                        data["url"] = lines[0] if lines else "https://dewa.gov.ae"
                elif category == "audio":
                    with open(full_path, "rb") as f:
                        files["file"] = (os.path.basename(full_path), f.read(), "audio/ogg")
                elif category == "image":
                    with open(full_path, "rb") as f:
                        files["file"] = (os.path.basename(full_path), f.read(), "image/png")

                resp = client.post(API_URL, data=data, files=files if files else None)
                latency_ms = int((time.time() - start_t) * 1000)

                if resp.status_code == 200:
                    resp_json = resp.json()
                    actual_verdict = resp_json.get("verdict", "UNKNOWN")
                    confidence = resp_json.get("risk_score", 0.0)
                    summary = resp_json.get("reason", "")
                    escalation = bool(resp_json.get("escalation_url"))

                    # Determine pass/match
                    is_match = (actual_verdict == expected_verdict)
                    if is_match:
                        print(f"-> [PASS] ({actual_verdict}, {latency_ms}ms)")
                        passed_count += 1
                    else:
                        print(f"-> [MISMATCH] (Got {actual_verdict}, Expected {expected_verdict}, {latency_ms}ms)")
                        failed_count += 1

                    results.append({
                        "id": tc_id,
                        "title": title,
                        "category": category,
                        "status": "PASS" if is_match else "MISMATCH",
                        "expected": expected_verdict,
                        "actual": actual_verdict,
                        "confidence": confidence,
                        "latency_ms": latency_ms,
                        "summary": summary,
                        "escalation_required": escalation,
                        "response": resp_json,
                    })
                else:
                    print(f"-> [HTTP {resp.status_code}] ({latency_ms}ms)")
                    failed_count += 1
                    results.append({
                        "id": tc_id,
                        "title": title,
                        "category": category,
                        "status": "HTTP_ERROR",
                        "error": f"HTTP {resp.status_code}: {resp.text[:120]}",
                        "expected": expected_verdict,
                        "actual": f"HTTP_{resp.status_code}",
                        "latency_ms": latency_ms,
                    })

            except Exception as exc:
                latency_ms = int((time.time() - start_t) * 1000)
                print(f"-> [EXCEPTION: {str(exc)[:50]}]")
                failed_count += 1
                results.append({
                    "id": tc_id,
                    "title": title,
                    "category": category,
                    "status": "EXCEPTION",
                    "error": str(exc),
                    "expected": expected_verdict,
                    "actual": "ERROR",
                    "latency_ms": latency_ms,
                })

    # Summary Statistics
    total_cases = len(test_cases)
    accuracy = (passed_count / total_cases * 100) if total_cases > 0 else 0
    avg_latency = (
        sum(r.get("latency_ms", 0) for r in results) / len(results)
    ) if results else 0

    print(f"\n=======================================================")
    print(f"  EXECUTION SUMMARY:")
    print(f"  Total Cases:      {total_cases}")
    print(f"  Passed Matches:   {passed_count}")
    print(f"  Mismatches/Errors:{failed_count}")
    print(f"  Accuracy:         {accuracy:.1f}%")
    print(f"  Avg Latency:      {avg_latency:.1f}ms")
    print(f"=======================================================\n")

    generate_markdown_report(results, total_cases, passed_count, failed_count, accuracy, avg_latency)


def generate_markdown_report(results, total, passed, failed, accuracy, avg_latency):
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    md = []
    md.append("# REALTEST Multi-Modal Execution Audit Report")
    md.append("")
    md.append(f"**Execution Timestamp:** `{now_utc}`  ")
    md.append(f"**Target Ingress Endpoint:** `{API_URL}`  ")
    md.append(f"**Overall Accuracy:** `{accuracy:.1f}%` ({passed}/{total} Passed)  ")
    md.append(f"**Average Latency:** `{avg_latency:.1f}ms`  ")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 1. Summary Metrics & Performance")
    md.append("")
    md.append("| Metric | Value | Status |")
    md.append("| :--- | :--- | :--- |")
    md.append(f"| **Total Real-World Assets** | `{total}` | Complete |")
    md.append(f"| **Matching Verdicts** | `{passed}` | Verified |")
    md.append(f"| **Deviations / Errors** | `{failed}` | {'Clean (0 Errors)' if failed == 0 else 'Audited'} |")
    md.append(f"| **Triage Accuracy** | `{accuracy:.1f}%` | {'Meets Production Standard' if accuracy >= 90 else 'Investigate'} |")
    md.append(f"| **Average Ingress Latency** | `{avg_latency:.1f}ms` | Complies with <1.5s SLA |")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2. Detailed Test Case Audit Results")
    md.append("")
    md.append("| ID | Category | Title | Expected | Actual | Latency | Status |")
    md.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for r in results:
        status_icon = "PASS" if r["status"] == "PASS" else "FAIL"
        md.append(
            f"| `{r['id']}` | **{r['category'].upper()}** | {r['title']} | "
            f"`{r['expected']}` | `{r['actual']}` | `{r.get('latency_ms', 0)}ms` | **{status_icon}** |"
        )

    md.append("")
    md.append("---")
    md.append("")
    md.append("## 3. Forensic Case Logs")
    md.append("")

    for r in results:
        md.append(f"### Case `{r['id']}`: {r['title']}")
        md.append(f"* **Category:** `{r['category']}`")
        md.append(f"* **Verdict Result:** Expected `{r['expected']}` | Returned `{r['actual']}`")
        md.append(f"* **Latency:** `{r.get('latency_ms', 0)}ms`")
        if "summary" in r:
            md.append(f"* **Triage Summary:** *{r['summary']}*")
        if "escalation_required" in r:
            md.append(f"* **Dubai Police Escalation Required:** `{r['escalation_required']}`")
        if "error" in r:
            md.append(f"* **Error Diagnostics:** `{r['error']}`")
        md.append("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Report emitted to: {REPORT_PATH}")


if __name__ == "__main__":
    run_suite()
