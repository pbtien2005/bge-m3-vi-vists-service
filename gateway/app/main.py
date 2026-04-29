from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any
import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .auth import RateLimiter, authenticate
from .config import Settings
from .load_balancer import LeastInflightLoadBalancer
from .metrics import (
    INFLIGHT,
    INPUT_TOKENS,
    RATE_LIMIT_REJECTIONS,
    REQUEST_LATENCY,
    REQUESTS,
    UPSTREAM_HEALTH,
    UPSTREAM_INFLIGHT,
    VALIDATION_REJECTIONS,
    metrics_response,
)
from .schemas import ApiError, error_response, openai_error, parse_embedding_request
from .tokenizer import TokenCounter
from .upstream import UpstreamClient, UpstreamRequestError, UpstreamTimeout


class JsonFormatter(logging.Formatter):
    _standard = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in self._standard and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


logger = logging.getLogger("embedding_gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings.from_env()
    configure_logging(settings.log_level)

    app.state.settings = settings
    app.state.token_counter = TokenCounter(settings.tokenizer_path)
    app.state.rate_limiter = RateLimiter(
        rate_per_second=settings.rate_limit_per_second,
        burst=settings.rate_limit_burst,
    )
    app.state.load_balancer = LeastInflightLoadBalancer(settings.upstream_urls)
    app.state.upstream_client = UpstreamClient(
        timeout_seconds=settings.upstream_timeout_seconds,
        healthcheck_timeout_seconds=settings.healthcheck_timeout_seconds,
    )

    logger.info(
        "gateway_started",
        extra={
            "model": settings.model_name,
            "max_input_tokens": settings.max_input_tokens,
            "max_body_bytes": settings.max_body_bytes,
            "upstream_urls": list(settings.upstream_urls),
        },
    )
    try:
        yield
    finally:
        await app.state.upstream_client.close()


app = FastAPI(title="BGE-M3 Vietnamese Embedding Gateway", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def request_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    route = request.url.path
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    start = time.perf_counter()
    response = None
    INFLIGHT.labels(route).inc()

    try:
        if route == "/v1/embeddings" and request.method.upper() == "POST":
            settings: Settings = request.app.state.settings
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    content_length_value = int(content_length)
                except ValueError:
                    content_length_value = settings.max_body_bytes + 1
            else:
                content_length_value = 0

            if content_length_value > settings.max_body_bytes:
                response = openai_error(
                    413,
                    "request_body_too_large",
                    f"Request body exceeds {settings.max_body_bytes} bytes.",
                )
                VALIDATION_REJECTIONS.labels("request_body_too_large").inc()
                return response

            body = await request.body()
            if len(body) > settings.max_body_bytes:
                response = openai_error(
                    413,
                    "request_body_too_large",
                    f"Request body exceeds {settings.max_body_bytes} bytes.",
                )
                VALIDATION_REJECTIONS.labels("request_body_too_large").inc()
                return response
            request._body = body  # Starlette caches request bodies this way.

        response = await call_next(request)
        return response
    finally:
        elapsed = time.perf_counter() - start
        REQUEST_LATENCY.labels(route).observe(elapsed)
        INFLIGHT.labels(route).dec()
        status_code = "unknown"
        if response is not None:
            status_code = str(response.status_code)  # type: ignore[name-defined]
            response.headers["x-request-id"] = request_id  # type: ignore[name-defined]
        REQUESTS.labels(request.method, route, status_code).inc()


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    VALIDATION_REJECTIONS.labels(exc.code).inc()
    return error_response(exc)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_error",
        extra={"request_id": getattr(request.state, "request_id", None)},
    )
    return openai_error(
        500,
        "internal_server_error",
        "Internal server error.",
        error_type="server_error",
    )


@app.get("/healthz")
async def healthz(request: Request) -> JSONResponse:
    readiness = await _upstream_readiness(request)
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "ready": readiness["ready"],
            "upstreams": readiness["upstreams"],
        },
    )


@app.get("/readyz")
async def readyz(request: Request) -> JSONResponse:
    readiness = await _upstream_readiness(request)
    return JSONResponse(
        status_code=200 if readiness["ready"] else 503,
        content={
            "status": "ready" if readiness["ready"] else "degraded",
            "upstreams": readiness["upstreams"],
        },
    )


async def _upstream_readiness(request: Request) -> dict[str, Any]:
    client: UpstreamClient = request.app.state.upstream_client
    balancer: LeastInflightLoadBalancer = request.app.state.load_balancer

    upstreams = []
    any_healthy = False
    for url in balancer.urls:
        healthy = await client.health(url)
        await balancer.set_health(url, healthy)
        UPSTREAM_HEALTH.labels(url).set(1 if healthy else 0)
        upstreams.append({"url": url, "healthy": healthy})
        any_healthy = any_healthy or healthy

    return {"ready": any_healthy, "upstreams": upstreams}


@app.get("/metrics")
async def metrics():
    return metrics_response()


@app.post("/v1/embeddings")
async def create_embedding(request: Request) -> JSONResponse:
    settings: Settings = request.app.state.settings
    token_counter: TokenCounter = request.app.state.token_counter
    rate_limiter: RateLimiter = request.app.state.rate_limiter
    balancer: LeastInflightLoadBalancer = request.app.state.load_balancer
    upstream_client: UpstreamClient = request.app.state.upstream_client
    request_id = request.state.request_id

    api_key = authenticate(request.headers.get("authorization"), settings)
    allowed = await rate_limiter.allow(api_key)
    if not allowed:
        RATE_LIMIT_REJECTIONS.inc()
        raise ApiError(
            429,
            "rate_limit_error",
            "rate_limit_exceeded",
            "Rate limit exceeded.",
        )

    try:
        payload = await request.json()
    except ValueError as exc:
        raise ApiError(
            400,
            "invalid_request_error",
            "invalid_json",
            "Request body must be valid JSON.",
        ) from exc

    embedding_request = parse_embedding_request(payload, expected_model=settings.model_name)
    input_tokens = token_counter.count(embedding_request.input)
    INPUT_TOKENS.observe(input_tokens)
    if input_tokens > settings.max_input_tokens:
        raise ApiError(
            400,
            "invalid_request_error",
            "input_too_long",
            f"Input has {input_tokens} tokens; maximum allowed is {settings.max_input_tokens}.",
        )

    try:
        lease = await balancer.acquire()
    except RuntimeError as exc:
        raise ApiError(
            503,
            "server_error",
            "no_healthy_upstream",
            "No healthy embedding worker is available.",
        ) from exc

    async with lease as target:
        UPSTREAM_INFLIGHT.labels(target.name).inc()
        try:
            status_code, data = await upstream_client.embeddings(
                target=target,
                payload=embedding_request.to_upstream_payload(),
                request_id=request_id,
            )
            await balancer.mark_success(target)
        except UpstreamTimeout as exc:
            await balancer.mark_failure(target)
            raise ApiError(
                504,
                "server_error",
                "upstream_timeout",
                "Embedding worker timed out.",
            ) from exc
        except UpstreamRequestError as exc:
            await balancer.mark_failure(target)
            raise ApiError(
                502,
                "server_error",
                "upstream_request_failed",
                "Embedding worker request failed.",
            ) from exc
        finally:
            UPSTREAM_INFLIGHT.labels(target.name).dec()

    if status_code >= 400:
        raise ApiError(
            502,
            "server_error",
            "upstream_error",
            f"Embedding worker returned status {status_code}.",
        )

    logger.info(
        "embedding_request_completed",
        extra={
            "request_id": request_id,
            "model": embedding_request.model,
            "input_tokens": input_tokens,
            "upstream": target.name,
            "status_code": status_code,
        },
    )
    return JSONResponse(status_code=status_code, content=data)
