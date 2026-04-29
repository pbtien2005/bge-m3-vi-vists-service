from __future__ import annotations

import asyncio
import secrets
import time
from dataclasses import dataclass

from .config import Settings
from .schemas import ApiError


def authenticate(authorization: str | None, settings: Settings) -> str:
    if not authorization:
        raise ApiError(
            401,
            "invalid_request_error",
            "missing_authorization",
            "Missing Authorization header.",
        )

    scheme, sep, token = authorization.partition(" ")
    if sep == "" or scheme.lower() != "bearer" or not token:
        raise ApiError(
            401,
            "invalid_request_error",
            "invalid_authorization",
            "Authorization must use Bearer token format.",
        )

    if not settings.api_keys:
        raise ApiError(
            500,
            "server_error",
            "api_keys_not_configured",
            "Gateway API keys are not configured.",
        )

    for configured in settings.api_keys:
        if secrets.compare_digest(token, configured):
            return token

    raise ApiError(
        401,
        "invalid_request_error",
        "invalid_api_key",
        "Invalid API key.",
    )


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


class RateLimiter:
    """Small in-memory token bucket for a single gateway instance."""

    def __init__(self, rate_per_second: float, burst: int) -> None:
        self._rate_per_second = rate_per_second
        self._burst = float(burst)
        self._buckets: dict[str, _Bucket] = {}
        self._lock = asyncio.Lock()

    async def allow(self, key: str) -> bool:
        now = time.monotonic()
        async with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                self._buckets[key] = _Bucket(tokens=self._burst - 1.0, updated_at=now)
                return True

            elapsed = max(0.0, now - bucket.updated_at)
            bucket.tokens = min(self._burst, bucket.tokens + elapsed * self._rate_per_second)
            bucket.updated_at = now

            if bucket.tokens < 1.0:
                return False

            bucket.tokens -= 1.0
            return True
