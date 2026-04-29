# Vietnamese BGE-M3 Embedding Service

Production-oriented baseline for serving a Vietnamese-tuned BGE-M3 embedding model with Hugging Face Text Embeddings Inference (TEI), two NVIDIA A30 GPUs, and a validating OpenAI-compatible gateway.

The large model weights are hosted on Hugging Face at `phambatien/bge-m3-vi-vists-best-eval`. This GitHub repo keeps only gateway code, deployment config, benchmark tooling, and small tokenizer/config files needed for gateway validation.

This baseline is intentionally conservative. It does not claim the `avg <= 50ms @ concurrency=100` SLA until benchmark results prove it for a specific token-length cap and traffic shape.

## 1. Architecture

```text
Client
  -> FastAPI gateway :8000
      -> bearer auth
      -> request body limit
      -> JSON/model/input validation
      -> single-string-only SLA endpoint
      -> tokenizer-based max token validation
      -> in-memory rate limit
      -> least-inflight load balancing
      -> /healthz liveness, /readyz upstream readiness
      -> Prometheus metrics + structured logs
  -> TEI worker 0 on GPU0, internal http://tei-gpu0:80
  -> TEI worker 1 on GPU1, internal http://tei-gpu1:80
      -> tokenization
      -> dynamic batching
      -> FP16 BGE-M3 inference
      -> CLS pooling
      -> OpenAI-compatible embedding response
```

The external API is:

```text
POST /v1/embeddings
```

The SLA endpoint only accepts one string in `input`. Arrays are rejected to keep latency predictable.

The built-in rate limiter is per gateway process and in-memory. Use Redis, Envoy global rate limiting, or an API-management layer if multiple gateway replicas must share quota state.

## Clone And Run

This repository is prepared for GitHub distribution without storing the large model weight in Git. TEI pulls the model from Hugging Face using:

```text
HF_MODEL_ID=phambatien/bge-m3-vi-vists-best-eval
```

The local `bge-m3-vi-vists-best-eval/` directory keeps tokenizer/config files for gateway token validation. Large weight files such as `model.safetensors` are ignored by `.gitignore`.

For a fresh clone:

```bash
git clone <github-repo-url>
cd <repo>
cp .env.example .env
# edit EMBEDDING_API_KEYS
docker compose up -d --build
```

## 2. Why TEI

TEI is used because it is purpose-built for embedding serving and already provides GPU inference, token-based dynamic batching, safetensors loading, OpenAI-compatible `/v1/embeddings`, Prometheus metrics, and OpenTelemetry hooks. It is the right first baseline before spending time on Triton, ONNX, or TensorRT.

## 3. Why 2 Data-Parallel Replicas

Each A30 has 24GB VRAM, and this BGE-M3/XLM-RoBERTa-class model fits on one GPU. The first topology is one TEI process per GPU:

```text
tei-gpu0 -> GPU0
tei-gpu1 -> GPU1
```

This doubles serving capacity without cross-GPU communication.

## 4. Why Not Tensor Parallel Initially

Tensor parallelism is unnecessary for a model that fits comfortably on a single A30. It adds coordination and cross-GPU communication overhead, while the expected bottlenecks are more likely sequence length, batching queue time, CPU tokenizer throughput, and JSON response overhead.

## 5. Start The Stack

Prerequisites:

```text
Docker with Compose v2
NVIDIA driver compatible with CUDA 12.2+
NVIDIA Container Toolkit
2x NVIDIA A30 GPUs
network access to pull ghcr.io/huggingface/text-embeddings-inference and the Hugging Face model
```

Create env:

```bash
cp .env.example .env
# edit EMBEDDING_API_KEYS before sharing or deploying
```

Start:

```bash
scripts/start.sh
```

Gateway:

```text
http://localhost:8000
```

Prometheus is optional:

```bash
docker compose --profile monitoring up -d prometheus
```

## 6. Smoke Test

Generate benchmark payloads:

```bash
python benchmarks/generate_payloads.py \
  --tokenizer-path bge-m3-vi-vists-best-eval/tokenizer.json
```

Run:

```bash
API_KEY=<your-token> benchmarks/smoke.sh
```

Example request:

```bash
curl http://localhost:8000/v1/embeddings \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"bge-m3-vi-vists","input":"xin chào","encoding_format":"float"}'
```

## 7. Benchmark

Payloads cover target token lengths:

```text
32, 64, 128, 256, 512
```

Concurrency matrix:

```text
1, 10, 25, 50, 100, 150
```

Run `hey` matrix:

```bash
API_KEY=<your-token> benchmarks/hey.sh
```

Run `wrk` for one payload:

```bash
API_KEY=<your-token> \
PAYLOAD_FILE=benchmarks/payloads/payload_128.json \
wrk -t4 -c100 -d30s -s benchmarks/wrk_embeddings.lua http://localhost:8000/v1/embeddings
```

Run `k6`:

```bash
API_KEY=<your-token> \
PAYLOAD_FILE=benchmarks/payloads/payload_128.json \
VUS=100 \
DURATION=30s \
k6 run benchmarks/k6_embeddings.js
```

CSV-compatible results should use:

```text
benchmarks/results_schema.csv
```

Columns:

```text
timestamp, token_length, concurrency, max_batch_tokens, max_batch_requests, avg_latency_ms, p50_ms, p95_ms, p99_ms, rps, error_rate, timeout_rate, gpu0_util, gpu1_util, cpu_util, pass_fail, notes
```

## 8. SLA Interpretation

Do not sign off only on average latency. A candidate pass should include:

```text
avg latency <= 50ms at concurrency=100
p95 <= 100ms
p99 <= 200ms
error rate < 0.1%
timeout rate = 0
no worker restarts or GPU OOM
at least 10 minutes after warmup
```

The initial SLA candidate is only for:

```text
input is a single string
input <= 128 tokens
encoding_format = float
model = bge-m3-vi-vists
```

If 256 or 512 tokens fail, that does not invalidate the 128-token SLA. It defines a different SLA tier.

## 9. TEI Tuning

Initial settings:

```text
--dtype float16
--pooling cls
--max-concurrent-requests 128
--max-batch-tokens 8192
--max-batch-requests 64
--max-client-batch-size 1
AUTO_TRUNCATE=false
TOKENIZATION_WORKERS=8
```

Tuning ranges:

```text
max-batch-tokens: 4096, 8192, 16384
max-batch-requests: 32, 64, 128
max-concurrent-requests: 64, 128, 256
TOKENIZATION_WORKERS: 4, 8, 12, 16 depending on CPU cores
```

Larger batches can improve throughput and worsen p95/p99 latency. For this SLA, optimize queue time and tail latency before peak throughput.

## 10. Troubleshooting

High latency:

```text
Check gateway p95/p99, TEI queue time, tokenization time, GPU util, and input token histogram.
Lower max-batch-tokens or max-batch-requests if queue time dominates.
Lower MAX_INPUT_TOKENS if long inputs dominate.
```

5xx errors:

```text
Check gateway structured logs for upstream_error, upstream_timeout, or no_healthy_upstream.
Check TEI container logs.
Check /healthz and Prometheus upstream health.
Use /readyz when an orchestrator needs to gate traffic on at least one healthy TEI worker.
```

GPU OOM:

```text
Lower max-batch-tokens.
Lower max-batch-requests.
Verify max-client-batch-size=1.
Check that no separate direct TEI endpoint allows large client batches.
```

Tokenizer bottleneck:

```text
GPU utilization low + tokenization time high indicates CPU/tokenizer pressure.
Tune TOKENIZATION_WORKERS.
Avoid over-allocating all CPU cores to both TEI containers at once.
Consider CPU pinning in production.
```

One worker down:

```text
Gateway removes unhealthy workers after failures/health checks.
Remaining GPU may not maintain SLA alone.
Use 429/503 backpressure rather than unbounded queueing.
```

## 11. Production Checklist

```text
[ ] HF_MODEL_ID points to the intended Hugging Face model repo
[ ] tokenizer.json present for gateway token validation
[ ] gateway token count matches expected tokenizer behavior
[ ] AUTO_TRUNCATE=false verified
[ ] API keys configured via env
[ ] array input rejected on /v1/embeddings
[ ] over-limit input rejected with input_too_long
[ ] body limit enforced
[ ] rate limit configured for expected tenants
[ ] /healthz and /metrics scraped
[ ] TEI metrics scraped on both workers
[ ] GPU metrics scraped with DCGM exporter in production
[ ] benchmark matrix completed for 32/64/128/256/512 tokens
[ ] SLA signed off with p95/p99 and error rate, not only average latency
[ ] one-worker-down behavior tested
[ ] GPU OOM behavior tested
[ ] deployment-specific TLS and network policy configured
```
