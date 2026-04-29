#!/usr/bin/env bash
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
API_KEY="${API_KEY:-change-me}"
PAYLOAD_DIR="${PAYLOAD_DIR:-benchmarks/payloads}"
RESULTS_FILE="${RESULTS_FILE:-benchmarks/results.csv}"
LENGTHS="${LENGTHS:-32 64 128 256 512}"
CONCURRENCY="${CONCURRENCY:-1 10 25 50 100 150}"
DURATION="${DURATION:-30s}"
MAX_BATCH_TOKENS="${MAX_BATCH_TOKENS:-8192}"
MAX_BATCH_REQUESTS="${MAX_BATCH_REQUESTS:-64}"

if ! command -v hey >/dev/null 2>&1; then
  echo "hey is not installed. Install it first: go install github.com/rakyll/hey@latest" >&2
  exit 1
fi

python benchmarks/generate_payloads.py --out-dir "$PAYLOAD_DIR" >/dev/null

if [[ ! -f "$RESULTS_FILE" ]]; then
  cp benchmarks/results_schema.csv "$RESULTS_FILE"
fi

for token_length in $LENGTHS; do
  payload="${PAYLOAD_DIR}/payload_${token_length}.json"
  for concurrency in $CONCURRENCY; do
    tmp="$(mktemp)"
    hey -z "$DURATION" -c "$concurrency" \
      -m POST \
      -H "Authorization: Bearer ${API_KEY}" \
      -H "Content-Type: application/json" \
      -D "$payload" \
      "${API_BASE}/v1/embeddings" | tee "$tmp"

    avg_ms="$(awk '/Average:/ {printf "%.3f", $2 * 1000}' "$tmp")"
    p50_ms="$(awk '/50% in/ {printf "%.3f", $3 * 1000}' "$tmp")"
    p95_ms="$(awk '/95% in/ {printf "%.3f", $3 * 1000}' "$tmp")"
    p99_ms="$(awk '/99% in/ {printf "%.3f", $3 * 1000}' "$tmp")"
    rps="$(awk '/Requests\/sec:/ {print $2}' "$tmp")"
    non_2xx="$(awk '/Non-2xx or 3xx responses:/ {print $5}' "$tmp")"
    total="$(awk '/Total:/ {print $2}' "$tmp")"
    errors="${non_2xx:-0}"
    if [[ -z "${total:-}" || "$total" == "0" ]]; then
      error_rate="1"
    else
      error_rate="$(awk -v e="$errors" -v t="$total" 'BEGIN {printf "%.6f", e / t}')"
    fi
    pass_fail="$(awk -v avg="$avg_ms" -v er="$error_rate" 'BEGIN {print (avg <= 50 && er < 0.001) ? "PASS" : "FAIL"}')"
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

    echo "${timestamp},${token_length},${concurrency},${MAX_BATCH_TOKENS},${MAX_BATCH_REQUESTS},${avg_ms},${p50_ms},${p95_ms},${p99_ms},${rps},${error_rate},,,,$pass_fail,hey ${DURATION}" >> "$RESULTS_FILE"
    rm -f "$tmp"
  done
done
