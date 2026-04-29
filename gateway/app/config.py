from __future__ import annotations

import os
from dataclasses import dataclass


def _csv(name: str, default: str) -> tuple[str, ...]:
    raw = os.getenv(name, default)
    return tuple(item.strip().rstrip("/") for item in raw.split(",") if item.strip())


def _int(name: str, default: int, minimum: int | None = None) -> int:
    raw = os.getenv(name)
    value = default if raw is None or raw == "" else int(raw)
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _float(name: str, default: float, minimum: float | None = None) -> float:
    raw = os.getenv(name)
    value = default if raw is None or raw == "" else float(raw)
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


@dataclass(frozen=True)
class Settings:
    service_name: str
    model_name: str
    api_keys: tuple[str, ...]
    tokenizer_path: str
    max_input_tokens: int
    max_body_bytes: int
    upstream_urls: tuple[str, ...]
    upstream_timeout_ms: int
    rate_limit_rpm: int
    rate_limit_burst: int
    healthcheck_timeout_ms: int
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            service_name=os.getenv("SERVICE_NAME", "bge-m3-embedding-gateway"),
            model_name=os.getenv("MODEL_NAME", "bge-m3-vi-vists"),
            api_keys=_csv("EMBEDDING_API_KEYS", ""),
            tokenizer_path=os.getenv(
                "TOKENIZER_PATH",
                "/models/bge-m3-vi-vists-best-eval/tokenizer.json",
            ),
            max_input_tokens=_int("MAX_INPUT_TOKENS", 128, minimum=1),
            max_body_bytes=_int("MAX_BODY_BYTES", 128 * 1024, minimum=1024),
            upstream_urls=_csv("UPSTREAM_URLS", "http://tei-gpu0:80,http://tei-gpu1:80"),
            upstream_timeout_ms=_int("UPSTREAM_TIMEOUT_MS", 300, minimum=1),
            rate_limit_rpm=_int("RATE_LIMIT_RPM", 6000, minimum=1),
            rate_limit_burst=_int("RATE_LIMIT_BURST", 200, minimum=1),
            healthcheck_timeout_ms=_int("HEALTHCHECK_TIMEOUT_MS", 250, minimum=1),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )

    @property
    def upstream_timeout_seconds(self) -> float:
        return self.upstream_timeout_ms / 1000.0

    @property
    def healthcheck_timeout_seconds(self) -> float:
        return self.healthcheck_timeout_ms / 1000.0

    @property
    def rate_limit_per_second(self) -> float:
        return self.rate_limit_rpm / 60.0
