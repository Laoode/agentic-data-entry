# Klaudia Receipt Extraction — Project Memory

> Baca ini dulu sebelum mulai. Semua plan sudah DONE. Ini state terakhir project.

---

## Stack & Transport

| Komponen | Detail |
|----------|--------|
| LLM Agent | `langchain-google-genai` + `ChatGoogleGenerativeAI` — support dual transport (dev API & Vertex AI via `vertexai=True` flag, unified SDK) |
| LLM Builder | `klaudia/core/supervisor/llm.py` → `build_chat_llm()` — single helper, transport-agnostic |
| Model | `gemini-3-flash-preview` (agents) |
| Gemini Transport | Toggle via env: `GOOGLE_GENAI_USE_VERTEXAI=True` → Vertex AI; `False` → Developer API (`LLM_API_KEY`) |
| Guardrails | Groq/Llama (prompt injection) + Gemini via `LLMClient` (scope check, output check) |
| KIE (Extraction) | Routing via `MOCK_KIE` + `OCR_MODE` + `KIE_MODEL` (default `gemini-3-flash-preview` direct image→JSON). `OCR_MODE=true` reserved for GLM-OCR text + Gemini KIE two-stage path. |
| DB | SQLite via `mcp-sqlite` (11 tools) + private blob registry (`file_blob`, `file_blob_page`, `blob_extraction`, `metadata_file_blob`) hidden from LLM |
| Sheets | Google Sheets via `mcp-gsheets` (16 tools, `SHEET_ID` dari env) |
| Cache + Queue | Redis (L1 dedup cache + Taskiq broker) — fail-soft when unreachable |
| Object Store | MinIO (S3-compatible) — content-addressed via BLAKE3, per-user prefix |
| MCP Transport | **stdio** (default). Rollback ke SSE: `MCP_TRANSPORT=sse ./startup.sh` |
| Extraction Mode | `EXTRACTION_MODE=sync` (inline, default) atau `async` (Taskiq workers + Redis pubsub progress) |
| Observability | Langfuse v4 (OpenTelemetry), fail-open |

---

## Env Vars (lengkap)

| Var | Keterangan |
|-----|-----------|
| `LLM_API_KEY` | Gemini Developer API key — aktif kalau `GOOGLE_GENAI_USE_VERTEXAI=False` |
| `GOOGLE_GENAI_USE_VERTEXAI` | `True` / `False` — toggle Vertex AI global |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID (Vertex) |
| `GOOGLE_CLOUD_LOCATION` | Region, mis. `global` atau `us-central1` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path ke service account JSON, mis. `gcp_service_account.json` |
| `MOCK_KIE` | `true` = return content-keyed fixture from `sample-data/labels/`. (Old `USE_MOCK_OCR` still honored as fallback.) |
| `OCR_MODE` | `false` (default) = single-call image→JSON via `KIE_MODEL`. `true` = vLLM GLM-OCR text recog → `KIE_MODEL` → JSON. |
| `KIE_MODEL` | KIE provider: `gemini-3-flash-preview` (current) or `zai-org/GLM-OCR` (future fine-tune). |
| `EXTRACTION_MODE` | `sync` (inline) or `async` (Taskiq queue + workers + Redis pubsub). |
| `REDIS_URL`, `MINIO_*`, `TASKIQ_*` | Cache, object store, queue. See `docs/OPERATIONS.md`. |
| `MCP_TRANSPORT` | `stdio` (default) atau `sse` |
| `SHEET_ID` | Google Sheets default spreadsheet ID |

> **Keamanan:** `gcp_service_account.json` & `service_account.json` **sudah di .gitignore**. Jangan di-commit.

---

## Arsitektur Agent

```
Orchestrator.process() / .stream()
  ├── Guardrail (input)
  ├── ExtractionAgent  (kalau ada file attachment)
  ├── SupervisorAgent (LangGraph)
  │   ├── router_llm  [tag: nostream]  → routing
  │   ├── final_llm   [tag: final_answer] → token stream ke client
  │   ├── sql_agent   (ReAct + MCP-SQLite tools)
  │   └── data_entry_team
  │       ├── read_agent
  │       ├── sheet_agent
  │       └── write_agent  ← juga punya tool_get_sheet_data + tool_list_sheets
  └── Guardrail (output)
```

---

## SSE Event Schema (`POST /v1/chat/stream`)

| Event | Payload |
|-------|---------|
| `session` | `session_id` |
| `guardrail` | `stage`, `status`, `message?` |
| `extraction` | `status`, `file_name`, `file_id?`, `pages?`, `summary?` |
| `step` | `node`, `next` |
| `tool` | `name` |
| `token` | `text` |
| `done` | `session_id`, `processing_time_ms`, `tools_used`, `content` |
| `error` | `message` |

---

## Bugs yang Sudah Difix (JANGAN diulangi)

| ID | File | Bug | Fix |
|----|------|-----|-----|
| B1 | `klaudia/interfaces/tool_registry.py` | `StructuredTool` tanpa `args_schema` → semua LLM tool call gagal | Build Pydantic schema dari MCP `inputSchema` |
| B2 | `data_entry_team/agents.py` | Route normalization hilang → supervisor silent exit | Tambah `_normalize_route()` |
| B3 | `sql_agent/agent.py` + `data_entry_team/agents.py` | `.invoke()` sync pada async-only tools → crash | Ganti ke `.ainvoke()` |
| B4 | `tool_registry.py` | Gemini 400: nested `list[list[Any]]` — `items` kosong di-drop → schema invalid | `_normalize_schema()` helper, ganti `items: {}` → `items: {type: string}` |
| B5 | `llm_client.py` | `shutdown()` ter-indent ke dalam generator → hilang | Pindah ke level method yang benar |
| B6 | `orchestrator.py` | `_nullctx()` dipanggil tapi tidak didefinisikan | Tambah `@contextmanager def _nullctx()` |
| B7 | `guardrails/scope.py` + `prompts.py` | `SCOPE_CHECK_PROMPT` generic → false positive: "harga nasi kuning 16 ribu" ter-flag Financial Advice | Pisah ke `SARA_CHECK_PROMPT` + `FINANCIAL_ADVICE_CHECK_PROMPT` dengan definisi eksplisit + counterexample; `check_scope()` return `ScopeViolation` dataclass, twin-check jalan parallel via `asyncio.gather()` |
| B8 | `orchestrator.py` | `langfuse.flush()` di hot path → ~5s overhead per request (OTLP timeout ke Langfuse cloud) | Hapus `flush()` dari `process()` dan `stream()`; flush hanya di `container.shutdown()` |
| B9 | `orchestrator.py` | `get_conversation_history` + `get_session_files` sequential → buang ~50ms | Parallelkan keduanya via `asyncio.gather()` |
| B10 | `router.py` | `supervisor_node` sync → jalan di ThreadPoolExecutor, sync HTTP client, streaming tag tidak proper | Refactor `supervisor_node` + `_emit_final_reply` ke `async def`, ganti `.invoke()` → `.ainvoke()` |
| B11 | `agents.py` | `team_supervisor` sync → overhead ThreadPoolExecutor sama seperti B10 | Refactor ke `async def` + `.ainvoke()` (Fix E) |
| B12 | `router.py` + `agents.py` | `thinking_config` di `llm_client.py` tidak efek ke supervisor path — salah client (`google.genai` vs `langchain-google-genai`). `supervisor_final` tetap ~8s karena thinking token ~1000 | `_MINIMAL_THINK` dict via `.bind()` ke `_emit_final_reply`, routing call, dan `team_supervisor` — path yang benar (Fix G) |
| B13 | `agent.py` | `get_available_sheets()` JSON parse error — `tool_list_sheets` return space-separated objects, bukan array → `json.loads()` "Extra data", cache tidak pernah populate | `_parse_tool_json_output()` helper yang handle format MCP actual; cache TTL turun ke 60s |
| B14 | `agent.py` | Sheet cache stale setelah `sheet_agent` create/rename/delete sheet — TTL-only, tidak ada invalidation | `invalidate_sheets_cache()` public method; `make_data_entry_team_node` terima `on_sheet_mutation` callback, fire on `[SHEET_DONE]` |
---

## Keputusan Desain Penting

| # | Keputusan |
|---|-----------|
| D1 | `ExtractionAgent` boleh raw SQL (bukan LLM, jadi "No Raw SQL from LLM" tidak berlaku) |
| D2 | `USE_MOCK_OCR=true` = explicit flag, bukan auto dari `STAGE=development` |
| D3 | `spreadsheet_id` optional di semua MCP-GSheets tools — fallback ke `SHEET_ID` env via `_resolve_sheet_id()` |
| D4 | Klaudia **tidak boleh minta spreadsheet ID/URL** ke user (sudah di prompt + MCP layer) |
| D5 | `gcp_service_account.json` & `service_account.json` di .gitignore — jangan commit |
| D6 | Worker write_agent include `tool_get_sheet_data` + `tool_list_sheets` (Pattern B/D dependency) |
| D7 | Stream orchestrator pakai manual `__enter__`/`__exit__` (bukan `with`) karena async generator |
| D8 | MCP log di stdio mode muncul di `logs/fastapi.log` (bukan file MCP terpisah) |
| D9 | Vertex AI toggle global — tidak ada hybrid mode. Semua Gemini call (guardrails + supervisor + sub-agents) ikut flag yang sama |
| D10 | `ChatVertexAI` dari `langchain-google-vertexai` **deprecated** sejak v3.2 — pakai `ChatGoogleGenerativeAI` dengan `vertexai=True` |
| D11 | `_ensure_gcp_credentials()` di `container.py` resolve path ke absolute dan export ke `os.environ` supaya MCP subprocesses inherit |
| D12 | Guardrails scope check pakai twin-prompt policy-based (SARA + Financial Advice terpisah), bukan generic topic string. `check_scope()` return `ScopeViolation(violated, policy)` — rejection message di-route per policy. `base.py` (Groq injection) tidak disentuh. |
| D13 | `langfuse.flush()` **tidak boleh** di hot path (`process()`/`stream()`) — SDK background thread sudah handle export. `flush()` hanya di `container.shutdown()`. |
| D14 | `supervisor_node` harus `async def` + `.ainvoke()` — LangGraph native support async node, jangan pakai sync `.invoke()` di ThreadPoolExecutor. |
| D15 | Thinking disable (`_MINIMAL_THINK` / `thinking_budget=0`) harus di-apply via `.bind()` ke `ChatGoogleGenerativeAI` path (`langchain-google-genai`), bukan ke `llm_client.py` (`google.genai` SDK). Dua code path yang berbeda. Workers (write/read/sheet/sql agent) **tidak** di-disable thinking — mereka butuh reasoning untuk composition patterns. |
| D16 | Sheet list cache di `SupervisorAgent` TTL=60s + event-driven invalidation via `on_sheet_mutation` callback. Cache parse pakai `_parse_tool_json_output()` karena MCP return space-separated JSON objects, bukan array. |
| D17 | `SUPERVISOR_ROUTING_PROMPT` pakai `RouterWithResponse` TypedDict — combined routing + inline response untuk conversational FINISH path, eliminasi satu LLM call. Jika `response` kosong meski `next==FINISH`, fallback ke `_emit_final_reply()`. |

---

## Data Entry Team — Pattern Menulis ke Sheet

| Pattern | Kapan | Cara |
|---------|-------|------|
| A | Replace seluruh sheet | `clear_range` → `update_cells` A1 |
| B | Append baris baru | `add_rows` (start_row = jumlah baris existing + 1) |
| C | Tambah header tanpa hapus data | `add_rows` start_row=0 → `update_cells` A1 (non-destructive) |
| D | Tambah kolom baru di kanan | Baca dulu → `update_cells` ke kolom kosong pertama, **bukan** `clear_range` |

---

## Test Suite (semua harus hijau)

| Suite | File | Tests | Catatan |
|-------|------|-------|---------|
| Agent | `test_data_entry_team.py` | 3+ | Butuh MCP-GSheets + `LLM_API_KEY` atau Vertex creds |
| Agent | `test_extraction.py` | 2 | Mock OCR |
| Agent | `test_guardrails.py` | 4 | |
| Agent | `test_llm_client.py` | 2 | Skip: `LLM_API_KEY` OR (`use_vertexai` + `google_cloud_project`) |
| Agent | `test_sql_agent.py` | 2 | Butuh `LLM_API_KEY` atau Vertex creds |
| Agent | `test_streaming.py` | 2 | Butuh `LLM_API_KEY` atau Vertex creds |
| DB | `test_db_client.py` | 4 | |
| MCP | `test_gsheets_tools.py` | 6 | Butuh `SHEET_ID` |
| MCP | `test_mcp_gsheets.py` | 1 | |
| MCP | `test_mcp_sqlite.py` | 1 | |
| MCP | `test_sqlite_tools.py` | 3 | |
| OCR | `test_ocr_mock.py` | 2 | |
| **Total** | | **32+** | `uv run pytest tests/ -v` |

> Test yang butuh MCP (`test_sql_agent`, `test_data_entry_team`, `test_streaming`, `test_hitl`) — jalankan `./startup.sh` dulu.

---

## Open Items (belum difix)

| # | Item |
|---|------|
| O1 | Error handling kalau MCP server down (timeout, retry, circuit breaker) |
| O2 | Rate limit Google Sheets API (100 req/100s) — butuh backoff |
| O3 | Observability: structured logging (request_id, session_id, file_id) |
| O4 | `MCPToolRegistry.connect()` tidak ada timeout — pytest hang kalau MCP down |
| O5 | GLM-OCR fine-tune masih training — `OCR_MODE=true` belum diuji end-to-end, akan dilakukan saat vLLM di Lightning AI aktif |
| O6 | Frontend mobile (Klaudia native app) — next phase |
| O7 | `output.py` guardrail belum direfactor ke twin-prompt approach — masih generic `{topics}` string. Kandidat next jika false positive output check muncul. |
| O7 | Refactor thinking config to single source of truth into .env so easyly to maintain and testing in different level thinking as well as the type of agents aka which agent should use level thinking mode. |