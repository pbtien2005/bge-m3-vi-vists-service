#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"

echo "/healthz"
curl -fsS "${API_BASE}/healthz" | python -m json.tool
echo
echo "/readyz"
curl -sS "${API_BASE}/readyz" | python -m json.tool
echo
docker compose ps
