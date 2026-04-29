#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
API_KEY="${API_KEY:-change-me}"
TOKEN_LENGTH="${TOKEN_LENGTH:-32}"
PAYLOAD_DIR="${PAYLOAD_DIR:-benchmarks/payloads}"
PAYLOAD_FILE="${PAYLOAD_FILE:-${PAYLOAD_DIR}/payload_${TOKEN_LENGTH}.json}"

if [[ ! -f "$PAYLOAD_FILE" ]]; then
  python benchmarks/generate_payloads.py --out-dir "$PAYLOAD_DIR"
fi

curl -sS "${API_BASE}/v1/embeddings" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  --data-binary @"${PAYLOAD_FILE}" | python -m json.tool
