import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Rate } from "k6/metrics";
import { SharedArray } from "k6/data";

const apiBase = __ENV.API_BASE || "http://localhost:8000";
const apiKey = __ENV.API_KEY || "change-me";
const payloadFile = __ENV.PAYLOAD_FILE || "benchmarks/payloads/payload_32.json";
const vus = Number(__ENV.VUS || "1");
const duration = __ENV.DURATION || "30s";

const payloads = new SharedArray("payloads", function () {
  return [open(payloadFile)];
});

export const options = {
  vus,
  duration,
  thresholds: {
    http_req_failed: ["rate<0.001"],
  },
};

export const embeddingLatency = new Trend("embedding_latency_ms");
export const embeddingErrors = new Rate("embedding_errors");

export default function () {
  const res = http.post(`${apiBase}/v1/embeddings`, payloads[0], {
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    timeout: "1s",
  });
  embeddingLatency.add(res.timings.duration);
  const ok = check(res, {
    "status is 200": (r) => r.status === 200,
    "has embedding data": (r) => {
      try {
        return Array.isArray(JSON.parse(r.body).data);
      } catch (_) {
        return false;
      }
    },
  });
  embeddingErrors.add(!ok);
  sleep(0.01);
}
