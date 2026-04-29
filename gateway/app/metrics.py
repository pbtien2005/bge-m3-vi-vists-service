from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.responses import Response

REQUESTS = Counter(
    "embedding_gateway_requests_total",
    "Gateway HTTP requests.",
    ["method", "route", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "embedding_gateway_request_duration_seconds",
    "Gateway end-to-end request latency.",
    ["route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5),
)

UPSTREAM_LATENCY = Histogram(
    "embedding_gateway_upstream_duration_seconds",
    "TEI upstream request latency.",
    ["upstream"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.2, 0.3, 0.5, 1.0, 2.5),
)

INPUT_TOKENS = Histogram(
    "embedding_gateway_input_tokens",
    "Input tokens per accepted request.",
    buckets=(1, 8, 16, 32, 64, 128, 256, 512, 1024),
)

VALIDATION_REJECTIONS = Counter(
    "embedding_gateway_validation_rejections_total",
    "Requests rejected by gateway validation.",
    ["code"],
)

RATE_LIMIT_REJECTIONS = Counter(
    "embedding_gateway_rate_limit_rejections_total",
    "Requests rejected by the gateway rate limiter.",
)

UPSTREAM_ERRORS = Counter(
    "embedding_gateway_upstream_errors_total",
    "Upstream errors seen by the gateway.",
    ["upstream", "code"],
)

INFLIGHT = Gauge(
    "embedding_gateway_inflight_requests",
    "In-flight gateway requests.",
    ["route"],
)

UPSTREAM_INFLIGHT = Gauge(
    "embedding_gateway_upstream_inflight",
    "In-flight requests by upstream worker.",
    ["upstream"],
)

UPSTREAM_HEALTH = Gauge(
    "embedding_gateway_upstream_healthy",
    "Gateway view of upstream health.",
    ["upstream"],
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
