"""
Project Hares: ARLUE / Digital Dubai Ethical AI Dialect Equity Benchmark Harness.

Evaluates demographic fairness, linguistic parity, and fraud recall across the 4 UAE resident dialects:
1. Emirati Gulf Arabic (National demographic)
2. Modern Standard Arabic (Formal public notices)
3. Expat English (International resident base)
4. Arabizi (Code-switched Latinized Arabic)

Validates compliance with Digital Dubai AI Ethics Principles (Fairness, Equity, and Non-Discrimination).
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from hares.ai.schemas import TextTriageInferenceResult
from hares.ai.slm_client import LocalSLMClient

logger = logging.getLogger("hares.benchmarks.dialect_equity")


class DialectCohortMetric(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    dialect_name: str
    total_evaluated: int
    malicious_count: int
    benign_count: int
    accuracy_pct: float
    precision_pct: float
    recall_pct: float
    false_positive_rate_pct: float
    tp: int
    fp: int
    tn: int
    fn: int


class DialectEquityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    benchmark_name: str = "ARLUE & Digital Dubai Ethical AI Dialect Equity Benchmark"
    version: str = "1.0.0-uae-sovereign"
    evaluation_timestamp_utc: str
    total_samples_evaluated: int
    cohorts: dict[str, DialectCohortMetric]
    min_recall_pct: float = Field(..., description="Lowest recall across any dialect")
    max_recall_pct: float = Field(..., description="Highest recall across any dialect")
    disparity_ratio: float = Field(..., description="Fairness Disparity Ratio: Target >= 0.80 (80% rule)")
    statistical_parity_passed: bool
    determination: str = Field(..., description="CERTIFIED_ETHICAL_EQUITY or BIAS_VIOLATION")


class DialectEquityHarness:
    """
    Automated evaluation harness running the ARLUE / Digital Dubai dialect equity benchmark protocol.
    """

    def __init__(self, corpus_path: Path | None = None, slm_client: LocalSLMClient | None = None) -> None:
        self.corpus_path = corpus_path or Path("opensource/datasets/localized_fraud_corpus/uae_smishing_100k.jsonl")
        self.slm_client = slm_client or LocalSLMClient(mock_mode=True)

    def run_benchmark(self, sample_per_dialect: int = 125) -> DialectEquityResult:
        """Runs the dialect equity benchmark across all 4 UAE demographic cohorts."""
        logger.info("Executing Dialect Equity harness (%d samples per dialect)...", sample_per_dialect)

        target_strata = {
            "emirati_gulf": {"malicious": range(10000, 10088), "benign": range(32000, 32037)},
            "msa": {"malicious": range(50000, 50088), "benign": range(65000, 65037)},
            "english": {"malicious": range(75000, 75088), "benign": range(86000, 86037)},
            "arabizi": {"malicious": range(93000, 93088), "benign": range(98500, 98537)},
        }

        target_indices: dict[int, str] = {}
        for dialect, splits in target_strata.items():
            for idx in splits["malicious"]:
                target_indices[idx] = dialect
            for idx in splits["benign"]:
                target_indices[idx] = dialect

        samples_by_dialect: dict[str, list[dict[str, Any]]] = {k: [] for k in target_strata}
        max_idx = max(target_indices.keys())

        with open(self.corpus_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx > max_idx:
                    break
                if idx in target_indices:
                    record = json.loads(line)
                    messages = record.get("messages", [])
                    if len(messages) >= 3:
                        clean_msg = re.sub(r"</?citizen_forwarded_text>", "", messages[1]["content"]).strip()
                        gt = json.loads(messages[2]["content"])
                        d_name = target_indices[idx]
                        samples_by_dialect[d_name].append({
                            "text": clean_msg,
                            "gt_is_imp": bool(gt.get("is_impersonation", False)),
                        })

        cohort_results: dict[str, DialectCohortMetric] = {}
        recalls: list[float] = []

        for d_name, items in samples_by_dialect.items():
            tp = fp = tn = fn = 0
            mal_count = sum(1 for it in items if it["gt_is_imp"])
            ben_count = len(items) - mal_count

            for it in items:
                res = self.slm_client.triage_text(it["text"])
                pred = res.is_impersonation
                gt = it["gt_is_imp"]

                if gt and pred:
                    tp += 1
                elif not gt and pred:
                    fp += 1
                elif not gt and not pred:
                    tn += 1
                elif gt and not pred:
                    fn += 1

            tot = tp + fp + tn + fn
            acc = ((tp + tn) / tot) * 100.0 if tot > 0 else 0.0
            prec = (tp / (tp + fp)) * 100.0 if (tp + fp) > 0 else 0.0
            rec = (tp / (tp + fn)) * 100.0 if (tp + fn) > 0 else 0.0
            fpr = (fp / (fp + tn)) * 100.0 if (fp + tn) > 0 else 0.0

            recalls.append(rec)
            cohort_results[d_name] = DialectCohortMetric(
                dialect_name=d_name.replace("_", " ").title(),
                total_evaluated=tot,
                malicious_count=mal_count,
                benign_count=ben_count,
                accuracy_pct=round(acc, 2),
                precision_pct=round(prec, 2),
                recall_pct=round(rec, 2),
                false_positive_rate_pct=round(fpr, 2),
                tp=tp,
                fp=fp,
                tn=tn,
                fn=fn,
            )

        min_rec = min(recalls) if recalls else 0.0
        max_rec = max(recalls) if recalls else 1.0
        disparity_ratio = round(min_rec / max_rec, 4) if max_rec > 0 else 1.0

        # Standard fairness threshold: 80% rule (disparity >= 0.80)
        passed_parity = disparity_ratio >= 0.80 and min_rec >= 85.0
        determination = "CERTIFIED_ETHICAL_EQUITY" if passed_parity else "BIAS_VIOLATION"

        logger.info(
            "Dialect Equity complete: Disparity Ratio=%.4f (Min=%.2f%%, Max=%.2f%%) Determination=%s",
            disparity_ratio, min_rec, max_rec, determination
        )

        return DialectEquityResult(
            evaluation_timestamp_utc=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            total_samples_evaluated=sum(c.total_evaluated for c in cohort_results.values()),
            cohorts=cohort_results,
            min_recall_pct=round(min_rec, 2),
            max_recall_pct=round(max_rec, 2),
            disparity_ratio=disparity_ratio,
            statistical_parity_passed=passed_parity,
            determination=determination,
        )
