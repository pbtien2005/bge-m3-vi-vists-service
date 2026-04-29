from __future__ import annotations

import time
from typing import Any

import httpx

from .load_balancer import UpstreamTarget
from .metrics import UPSTREAM_ERRORS, UPSTREAM_LATENCY


class UpstreamTimeout(Exception):
    pass


class UpstreamRequestError(Exception):
    pass


class UpstreamClient:
    def __init__(self, timeout_seconds: float, healthcheck_timeout_seconds: float) -> None:
        self._timeout = httpx.Timeout(timeout_seconds)
        self._health_timeout = httpx.Timeout(healthcheck_timeout_seconds)
        self._client = httpx.AsyncClient()

    async def close(self) -> None:
        await self._client.aclose()

    async def embeddings(
        self,
        target: UpstreamTarget,
        payload: dict[str, Any],
        request_id: str,
    ) -> tuple[int, dict[str, Any]]:
        start = time.perf_counter()
        try:
            response = await self._client.post(
                f"{target.url}/v1/embeddings",
                json=payload,
                headers={"x-request-id": request_id},
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            UPSTREAM_ERRORS.labels(target.name, "timeout").inc()
            raise UpstreamTimeout(str(exc)) from exc
        except httpx.HTTPError as exc:
            UPSTREAM_ERRORS.labels(target.name, "request_error").inc()
            raise UpstreamRequestError(str(exc)) from exc
        finally:
            UPSTREAM_LATENCY.labels(target.name).observe(time.perf_counter() - start)

        try:
            data = response.json()
        except ValueError as exc:
            UPSTREAM_ERRORS.labels(target.name, "invalid_json").inc()
            raise UpstreamRequestError("Upstream returned invalid JSON") from exc

        if response.status_code >= 500:
            UPSTREAM_ERRORS.labels(target.name, str(response.status_code)).inc()

        return response.status_code, data

    async def health(self, url: str) -> bool:
        try:
            response = await self._client.get(f"{url.rstrip('/')}/health", timeout=self._health_timeout)
            return response.status_code == 200
        except httpx.HTTPError:
            return False
