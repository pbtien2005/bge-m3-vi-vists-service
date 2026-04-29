from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass
class UpstreamTarget:
    name: str
    url: str
    inflight: int = 0
    healthy: bool = True
    unhealthy_until: float = 0.0


class UpstreamLease:
    def __init__(self, balancer: "LeastInflightLoadBalancer", target: UpstreamTarget) -> None:
        self._balancer = balancer
        self.target = target

    async def __aenter__(self) -> UpstreamTarget:
        return self.target

    async def __aexit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
        await self._balancer.release(self.target)


class LeastInflightLoadBalancer:
    def __init__(self, urls: tuple[str, ...], unhealthy_cooldown_seconds: float = 5.0) -> None:
        if not urls:
            raise ValueError("At least one upstream URL is required")
        self._targets = [
            UpstreamTarget(name=f"tei-{idx}", url=url.rstrip("/")) for idx, url in enumerate(urls)
        ]
        self._lock = asyncio.Lock()
        self._unhealthy_cooldown_seconds = unhealthy_cooldown_seconds

    async def acquire(self) -> UpstreamLease:
        now = time.monotonic()
        async with self._lock:
            candidates = [
                target
                for target in self._targets
                if target.healthy or target.unhealthy_until <= now
            ]
            if not candidates:
                raise RuntimeError("No healthy upstream embedding workers are available")

            target = min(candidates, key=lambda item: (item.inflight, item.name))
            target.inflight += 1
            return UpstreamLease(self, target)

    async def release(self, target: UpstreamTarget) -> None:
        async with self._lock:
            target.inflight = max(0, target.inflight - 1)

    async def mark_success(self, target: UpstreamTarget) -> None:
        async with self._lock:
            target.healthy = True
            target.unhealthy_until = 0.0

    async def mark_failure(self, target: UpstreamTarget) -> None:
        async with self._lock:
            target.healthy = False
            target.unhealthy_until = time.monotonic() + self._unhealthy_cooldown_seconds

    async def set_health(self, url: str, healthy: bool) -> None:
        async with self._lock:
            for target in self._targets:
                if target.url == url.rstrip("/"):
                    target.healthy = healthy
                    target.unhealthy_until = (
                        0.0 if healthy else time.monotonic() + self._unhealthy_cooldown_seconds
                    )

    async def snapshot(self) -> list[dict[str, object]]:
        async with self._lock:
            return [
                {
                    "name": target.name,
                    "url": target.url,
                    "inflight": target.inflight,
                    "healthy": target.healthy,
                }
                for target in self._targets
            ]

    @property
    def urls(self) -> tuple[str, ...]:
        return tuple(target.url for target in self._targets)
