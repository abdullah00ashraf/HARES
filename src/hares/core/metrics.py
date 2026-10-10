import logging
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)

logger = logging.getLogger("hares.core.metrics")

# =========================================================================
# Custom Prometheus Metrics Registry for Project Hares (Phase 6)
# =========================================================================

WEBHOOK_INGRESS_LATENCY = Histogram(
    "hares_webhook_ingress_latency_seconds",
    "FastAPI webhook ingress acknowledgment latency (FR-3.3 <50ms SLA)",
    buckets=[0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500, 1.0],
    registry=REGISTRY,
)

TRIAGE_E2E_LATENCY = Histogram(
    "hares_triage_e2e_latency_seconds",
    "Total end-to-end triage latency from ingress to verdict dispatch",
    ["payload_type", "verdict"],
    buckets=[0.1, 0.25, 0.5, 1.0, 1.5, 2.5, 4.5, 6.0, 10.0],
    registry=REGISTRY,
)

TRIAGE_VERDICTS_TOTAL = Counter(
    "hares_triage_verdicts_total",
    "Cumulative triage verdicts emitted to citizens",
    ["verdict", "rule_triggered"],
    registry=REGISTRY,
)

QUEUE_DEPTH_GAUGE = Gauge(
    "hares_queue_depth",
    "Current task depth of Celery Redis queues",
    ["queue_name"],
    registry=REGISTRY,
)

RATE_LIMIT_REJECTIONS_TOTAL = Counter(
    "hares_rate_limit_rejections_total",
    "Cumulative queries rejected by token-bucket rate limiters",
    ["principal_type"],  # 'citizen' or 'analyst'
    registry=REGISTRY,
)

CONFORMAL_P_VALUES = Histogram(
    "hares_conformal_p_values",
    "Distribution of non-parametric conformal empirical p-values",
    buckets=[0.001, 0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 1.0],
    registry=REGISTRY,
)


def record_ingress_latency(duration_seconds: float) -> None:
    """Records webhook ingress acknowledgment latency."""
    WEBHOOK_INGRESS_LATENCY.observe(max(0.0, duration_seconds))


def record_e2e_latency(payload_type: str, verdict: str, duration_seconds: float) -> None:
    """Records total end-to-end triage latency."""
    TRIAGE_E2E_LATENCY.labels(payload_type=payload_type, verdict=verdict).observe(max(0.0, duration_seconds))


def record_verdict(verdict: str, rule_triggered: str) -> None:
    """Increments verdict counter."""
    TRIAGE_VERDICTS_TOTAL.labels(verdict=verdict, rule_triggered=rule_triggered).inc()


def record_queue_depth(queue_name: str, depth: int) -> None:
    """Updates queue depth gauge."""
    QUEUE_DEPTH_GAUGE.labels(queue_name=queue_name).set(max(0, depth))


def record_rate_limit_rejection(principal_type: str = "citizen") -> None:
    """Increments rate limit rejection counter."""
    RATE_LIMIT_REJECTIONS_TOTAL.labels(principal_type=principal_type).inc()


def record_conformal_p_value(p_val: float) -> None:
    """Records conformal empirical p-value."""
    CONFORMAL_P_VALUES.observe(min(1.0, max(0.0, p_val)))


def export_prometheus_metrics() -> tuple[bytes, str]:
    """Generates serialized OpenMetrics / Prometheus metrics payload and content-type."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
