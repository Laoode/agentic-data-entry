# Klaudia Operations Notes

Living doc for the bits that don't live in code: MinIO lifecycle, secrets
hygiene, worker scaling, and the order in which infra must come up.

## 1. Service Bring-Up Order

```
Redis            → DedupCache (L1) + Taskiq broker + result backend + pubsub
MinIO            → Object store for blobs + page renders
SQLite DB file   → Auto-bootstrapped on first FastAPI start (private + public
                   tables via AppDBClient.connect)
Taskiq worker    → ./scripts/run_worker.sh (Async mode only)
FastAPI app      → ./startup.sh
```

If `EXTRACTION_MODE=sync`, Taskiq worker is unused. If `MOCK_KIE=true`, the
KIE model is bypassed entirely.

## 2. MinIO Bucket Lifecycle

Bucket name comes from `MINIO_BUCKET` (default `klaudia-blobs`). It's
auto-created on FastAPI startup (idempotent). Recommended production
configuration:

| Concern            | Setting                                              |
|--------------------|------------------------------------------------------|
| Versioning         | OFF (content-addressed keys make versions redundant) |
| Object lock        | Optional — useful for compliance, otherwise off      |
| Lifecycle: blobs/  | Retain forever (or 365d if you don't need replay)    |
| Lifecycle: pages/  | Retain forever — used for re-extraction after model upgrades |
| Server-side encryption | SSE-S3 (recommended) or KMS                      |
| Bucket policy      | Deny anonymous; allow only the IAM principal used by FastAPI |

To set retention on a key prefix:

```bash
mc ilm rule add local/klaudia-blobs \
    --expire-days 365 --prefix "blobs/"
```

## 3. Secrets

| Secret                  | Where used                       |
|-------------------------|----------------------------------|
| `LLM_API_KEY`           | Gemini Developer API (when Vertex disabled) |
| `gcp_service_account.json` | Vertex AI + Google Sheets MCP — not in git |
| `AUTH_TOKEN`            | Bearer for vLLM Qwen3.5-4B endpoint  |
| `MINIO_*`               | Set non-default values for any prod-ish deploy |
| `GROQ_API_KEY`          | Prompt-injection guard            |
| `LANGFUSE_*`            | Observability — optional          |

Hard rules (already enforced in `.gitignore`):
- `gcp_service_account.json`, `service_account.json` — never commit
- `.env` — never commit; use `.env.template` as the reference

## 4. Taskiq Worker Scaling

Worker count and per-worker async concurrency are independent levers:

- `WORKER_COUNT` — number of OS processes
- `WORKER_CONCURRENCY` — asyncio tasks per process

The bottleneck is vLLM continuous batching, not Python. Recommended:

| Hardware             | WORKER_COUNT | WORKER_CONCURRENCY | --max-num-seqs (vLLM) |
|----------------------|--------------|---------------------|------------------------|
| Dev (MacBook + mock) | 1            | 4                   | n/a                    |
| 1× L4 24GB           | 1            | 8                   | 16                     |
| 1× A100 40GB         | 2            | 16                  | 32                     |

Tune up only after watching Langfuse latency histograms.

## 5. Pressure Relief Valve

The orchestrator reads `LLEN` on the Taskiq queue and rejects new uploads
when depth exceeds `EXTRACTION_QUEUE_DEPTH_REJECT` (default 200). Soft warn
at `EXTRACTION_QUEUE_DEPTH_WARN` (default 50) — currently logged, not yet
surfaced to the UI.

## 6. Mode Reference (KIE Routing)

Backend is chosen from `KIE_MODEL` alone (no `OCR_MODE`):

| Condition                        | Behavior                                          |
|----------------------------------|---------------------------------------------------|
| `MOCK_KIE=true`                  | Return fixture from `sample-data/labels/`         |
| `KIE_MODEL` starts with `gemini` | Gemini, full zero-shot prompt (image → JSON)      |
| `KIE_MODEL` anything else        | Fine-tuned Qwen on vLLM, image-only → JSON        |

For the fine-tuned model, set `KIE_MODEL` to the served model name and fill
`VLLM_KIE_ENDPOINT` (full `/v1/chat/completions` URL) + `VLLM_KIE_API_KEY`.

## 7. Smoke Tests

```bash
# Unit tests (fast, no infra)
uv run pytest tests/unit -q

# Ingest pipeline (needs Redis + MinIO)
uv run pytest tests/integration/extraction/test_ingest_pipeline.py -q

# Async pipeline (needs Redis + MinIO, spawns a real worker subprocess)
uv run pytest tests/integration/extraction/test_async_pipeline.py -q

# Gemini live test (needs LLM_API_KEY or Vertex creds)
uv run pytest tests/integration/extraction/test_gemini_kie.py -q
```

If MinIO is down, ingest_pipeline + async_pipeline tests skip cleanly.

## 8. Hash Isolation

Tables intentionally hidden from MCP-SQLite tools (and therefore from every
LLM in the system):

- `file_blob` — user_id, blake3, minio_key, size
- `file_blob_page` — per-page hash + minio key
- `blob_extraction` — KIE result keyed by content hash
- `metadata_file_blob` — link from public file row to private blob

The agent only ever sees `metadata_file` and `pages` (which contain the
validated extraction JSON, never the hash or storage key).


### Usage
```
redis-server
redis-cli shutdown
```

```
minio server /Users/yudhypr/Codex/minio/data
```