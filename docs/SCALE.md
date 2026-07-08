# Production Scale Analysis — Bottlenecks at 1M Users

> Findings only. This document does **not** change architecture; it records where
> the current design (PRD v1.2) breaks under load and what to do about it.
> Baseline: the 42.3s trace for `"tolong masukkan ini, buatkan bulan juli sheet"`.

## 1. Latency breakdown (the 42.3s request)

| Stage | Time | Nature | On critical path? |
|-------|------|--------|-------------------|
| `guardrail.validate_input` | 2.93s | 3 LLM calls (injection/SARA/financial), already parallel | yes |
| `extraction_agent` (KIE image) | 13.00s | 1 vision LLM call | yes (sync mode) |
| supervisor route | 3.00s | 1 LLM call | yes |
| team route | 2.28s | 1 LLM call | yes |
| write_agent | 17.87s | 2 LLM turns (5.6s + 7.1s) + 1 tool read (5.1s) | yes |
| `guardrail.validate_output` | 2.43s | 1 LLM call | yes |

**Critical-path shape: 6–8 *sequential* LLM round-trips per request.** The wall-clock
is dominated by serial model latency, not compute. Load does not change per-request
latency; it multiplies concurrency and token spend.

Worst part of this specific trace: ~18s was spent in `write_agent` to produce a
**wrong clarify** (read all sheets, then refused). Fixing the routing (Stage 2)
makes the expensive path also the correct one.

## 2. Hard walls (block correctness/availability, not just speed)

### 2.1 SQLite as source of truth — #1 blocker
PRD §5 stores users, sessions, conversations, files, and extractions in SQLite.
SQLite is single-writer with file-level locking. Under concurrent writes it
serializes and throws `database is locked`. This does not reach 1M users — it
degrades in the low thousands of concurrent sessions.
**Action:** migrate to Postgres (managed: Cloud SQL / RDS / Neon). Keep the
repository interface (PRD §Repository Pattern) so the swap is contained to the
data layer. The blob registry (`file_blob*`) moves too.

### 2.2 Google Sheets as the financial datastore — #2 blocker
Sheets API quotas: ~60 write req/min/user, ~300 read+write/min/project. It is
not transactional and has no row-level concurrency. At scale this throttles
(HTTP 429) and risks lost updates on concurrent edits to the same sheet.
**Action:** treat Sheets as an **export/mirror**, not the ledger. Authoritative
financial rows live in Postgres; a background job syncs to the user's Sheet.
This also removes read-before-write latency from the hot path.

### 2.3 MCP transport
`MCP_TRANSPORT=stdio` (default) runs the MCP servers as subprocesses. Confirm
they are **long-lived shared processes**, not spawned per request — per-request
subprocess spawn is a throughput killer. For horizontal scaling move MCP servers
behind SSE/HTTP as independent, replicable services.

## 3. Cost/throughput multipliers

- **Guardrails = 3 LLM calls on every input.** At 1M requests that is 3M extra
  calls. Collapse SARA + financial-advice into one structured call, and cache
  prompt-injection results by input hash. Consider a small local classifier
  (fastText/DistilBERT) as an L0 filter before spending any LLM call.
- **KIE 13s synchronous.** `EXTRACTION_MODE=async` (Taskiq + Redis pubsub)
  already exists — make it the production default so extraction leaves the
  request path; the user gets a "processing" event and a push when done.
- **DeepSeek KV cache** is automatic and keys on a stable system-prompt prefix
  (docs/MODELS.md). Keeping the persona prefix byte-stable across turns
  maximizes `prompt_cache_hit_tokens` and cuts cost materially. The Stage-2
  context-isolation work helps here: smaller, stable per-worker prefixes.
- **Sheet-list fetch per turn** is cached (TTL + event invalidation) — good.
  Keep it; do not regress to per-turn `tool_list_sheets`.

## 4. Availability / correctness under load

- **Fail-soft already present:** Redis, Langfuse, sheet-cache all degrade
  gracefully. Preserve this posture when adding Postgres (connection-pool
  exhaustion must degrade, not crash).
- **Per-user rate limiting** is not in the PRD's non-negotiables but is
  mandatory at scale (protects LLM spend and MCP quotas). Add at the FastAPI
  edge, keyed by user, before guardrails.
- **Idempotency:** a retried "insert this receipt" must not double-write.
  Key writes by `(session_id, file_id, page_id)` once Postgres is authoritative.

## 5. Priority order

1. Postgres migration (unblocks everything else). 
2. Async KIE as default (−13s off critical path).
3. Collapse guardrails to 1 call + cache (−~2s, −2M calls/1M req).
4. Sheets as mirror, not ledger (removes quota wall + read-before-write).
5. Edge rate limiting + write idempotency.
6. MCP servers as replicable HTTP services.

Items 2, 3, 6 are latency/cost; items 1, 4, 5 are correctness/availability walls.
