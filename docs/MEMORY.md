# Klaudia Receipt Extraction + Financial Accounting Data Entry — Project Memory

> Baca ini dulu sebelum mulai. Semua plan sudah DONE. Ini state terakhir project.

---

## Stack & Transport

| Komponen | Detail |
|----------|--------|
| LLM Agent | `langchain-google-genai` (Gemini) atau `langchain-openai` (vLLM + DeepSeek, OpenAI-compatible) — toggle via `MODEL_PROVIDER` (`google`/`vllm`/`deepseek`). Lihat `docs/MODELS.md` |
| LLM Builder | `klaudia/core/supervisor/llm.py` → `build_chat_llm()` — branch `_build_gemini_llm` / `_build_openai_llm` (thinking extra_body per provider via `_openai_thinking_extra_body`); `with_structured(llm, schema)` provider-aware (DeepSeek=function_calling, vLLM=json_schema) |
| Model | `gemini-3-flash-preview` (Gemini) \| `Qwen/Qwen3.5-27B` (vLLM) \| `deepseek-v4-pro` (DeepSeek) |
| Gemini Transport | Toggle via env: `GOOGLE_GENAI_USE_VERTEXAI=True` → Vertex AI; `False` → Developer API (`LLM_API_KEY`) |
| Guardrails | Groq/Llama (prompt injection) + Gemini via `LLMClient` (scope check, output check) — **selalu Gemini**, tidak ikut `MODEL_PROVIDER` |
| KIE (Extraction) | Backend dipilih dari `KIE_MODEL` saja (tidak ada `OCR_MODE` lagi): `MOCK_KIE=true` → fixture; `KIE_MODEL` diawali `gemini` → `GeminiKIEClient` (full zero-shot prompt, image→JSON); selain itu → `VLLMKIEClient` (Qwen3.5-4B fine-tuned di vLLM, **image-only**, prompt ada di jinja template server). Tidak ikut `MODEL_PROVIDER`. Lihat `docs/MODELS.md` |
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
| `MODEL_PROVIDER` | `google` (default) \| `vllm` \| `deepseek` — toggle supervisor/router/worker LLM client. `openai` = alias lama untuk `vllm`. Guardrails + KIE tidak terpengaruh, selalu Gemini. Detail lengkap: `docs/MODELS.md` |
| `VLLM_LLM_ENDPOINT` / `VLLM_LLM_API_KEY` | Endpoint + bearer untuk agentic Qwen di vLLM (dipakai saat `MODEL_PROVIDER=vllm`). **Beda** dari `VLLM_BASE_URL` (server OCR Qwen3.5-4B) |
| `DEEPSEEK_BASE_URL` / `DEEPSEEK_API_KEY` | Endpoint (default `https://api.deepseek.com/v1`) + API key DeepSeek (dipakai saat `MODEL_PROVIDER=deepseek`) |
| `LLM_DISABLE_THINKING` | `true`/`false` — disable thinking pada agentic stack. extra_body per provider: vLLM `{"chat_template_kwargs":{"enable_thinking":False}}`, DeepSeek `{"thinking":{"type":"disabled"}}` |
| `MOCK_KIE` | `true` = return content-keyed fixture from `sample-data/labels/` (offline). Satu-satunya flag mock — `USE_MOCK_OCR` sudah dihapus |
| `KIE_MODEL` | Satu-satunya knob KIE backend: `gemini-*` → GeminiKIEClient (full prompt); selain itu → VLLMKIEClient (fine-tuned, image-only) |
| `VLLM_KIE_ENDPOINT` / `VLLM_KIE_API_KEY` | Endpoint full `/v1/chat/completions` + bearer untuk vLLM KIE fine-tuned. Dipakai hanya saat `KIE_MODEL` bukan gemini. **Beda** dari `VLLM_LLM_ENDPOINT` (agentic) |
| `EXTRACTION_MODE` | `sync` (inline) or `async` (Taskiq queue + workers + Redis pubsub) |
| `REDIS_URL`, `MINIO_*`, `TASKIQ_*` | Cache, object store, queue. See `docs/OPERATIONS.md` |
| `MCP_TRANSPORT` | `stdio` (default) atau `sse` |
| `SHEET_ID` | Google Sheets default spreadsheet ID |
| `LLM_THINKING_LEVEL_ROUTING` | Thinking level untuk routing nodes (supervisor_node, team_supervisor, final_reply). Default: `minimal` |
| `LLM_THINKING_LEVEL_WORKER` | Thinking level untuk worker agents (write/read/sheet/sql agent). Default: `low` |

> **Keamanan:** `gcp_service_account.json` & `service_account.json` **sudah di .gitignore**. Jangan di-commit.

---

## Arsitektur Agent

```
Orchestrator.process() / .stream()
  ├── Guardrail (input)
  ├── ExtractionAgent  (kalau ada file attachment)
  ├── SupervisorAgent (LangGraph)
  │   ├── router_llm  [tag: nostream]  → routing
  │   ├── final_llm   [tag: final_answer] → token stream
  │   ├── sql_agent   (ReAct + MCP-SQLite tools)
  │   └── data_entry_team
  │       ├── read_agent
  │       ├── sheet_agent
  │       └── write_agent
  └── Guardrail (output)
```

> Semua node di atas dibangun lewat `build_chat_llm()` — provider (`google`/`openai`) di-resolve sekali di `container.py`, threaded ke `SupervisorAgent`.

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
| B1 | `tool_registry.py` | `StructuredTool` tanpa `args_schema` → semua LLM tool call gagal | Build Pydantic schema dari MCP `inputSchema` |
| B2 | `data_entry_team/agents.py` | Route normalization hilang → supervisor silent exit | Tambah `_normalize_route()` |
| B3 | `sql_agent/agent.py` + `agents.py` | `.invoke()` sync pada async-only tools → crash | Ganti ke `.ainvoke()` |
| B4 | `tool_registry.py` | Gemini 400: nested `list[list[Any]]` — `items` kosong di-drop → schema invalid | `_normalize_schema()`, ganti `items: {}` → `items: {type: string}` |
| B5 | `llm_client.py` | `shutdown()` ter-indent ke generator → hilang | Pindah ke level method yang benar |
| B6 | `orchestrator.py` | `_nullctx()` dipanggil tapi tidak didefinisikan | Tambah `@contextmanager def _nullctx()` |
| B7 | `guardrails/scope.py` + `prompts.py` | `SCOPE_CHECK_PROMPT` generic → false positive "harga nasi kuning 16 ribu" ter-flag Financial Advice | Pisah `SARA_CHECK_PROMPT` + `FINANCIAL_ADVICE_CHECK_PROMPT` + counterexample; `check_scope()` → `ScopeViolation`, parallel via `asyncio.gather()` |
| B8 | `orchestrator.py` | `langfuse.flush()` di hot path → ~5s overhead/request | Hapus dari `process()`/`stream()`; flush hanya di `container.shutdown()` |
| B9 | `orchestrator.py` | `get_conversation_history` + `get_session_files` sequential | Parallelkan via `asyncio.gather()` |
| B10 | `router.py` | `supervisor_node` sync → ThreadPoolExecutor overhead | `async def` + `.ainvoke()` |
| B11 | `agents.py` | `team_supervisor` sync → overhead sama seperti B10 | `async def` + `.ainvoke()` |
| B12 | `router.py` + `agents.py` | `thinking_config` di `llm_client.py` (salah client) tidak efek ke supervisor path | `_MINIMAL_THINK` via `.bind()` di path `ChatGoogleGenerativeAI` yang benar |
| B13 | `agent.py` | `get_available_sheets()` JSON parse error — MCP return space-separated objects, bukan array | `_parse_tool_json_output()` helper; cache TTL 60s |
| B14 | `agent.py` | Sheet cache stale setelah create/rename/delete sheet — TTL-only | `invalidate_sheets_cache()`; `on_sheet_mutation` callback fire on `[SHEET_DONE]` |
| B15 | `router.py` + `agents.py` | `_MINIMAL_THINK` hardcoded — tidak bisa tuning tanpa code change | Pindah ke `.env`: `LLM_THINKING_LEVEL_ROUTING`/`_WORKER`; `llm.py` terima `thinking_level` param via `.bind()` |
| B16 | `output.py` + `config.py` | `topics_str`/`blacklisted_topics` dead code — prompt tidak punya `{topics}` placeholder | Hapus dead code; tambah counterexample eksplisit ke `OUTPUT_CHECK_PROMPT` |
| B17 | `observability.py` | `LangfuseService.span()`/`trace_attributes()` double-yield — `except` re-`yield` setelah `throw()` → `RuntimeError`, masks real error | Pisah setup ke `try/except` sendiri; `yield` selalu di luar try |
| B18 | `gemini_kie.py` | `GeminiKIEClient` tidak set `thinking_config` → model thinking habiskan semua `max_output_tokens` untuk reasoning, `response.text` empty pada gambar besar (≥1MB) | Tambah `thinking_config=ThinkingConfig(thinking_level=MINIMAL)` ke `GenerateContentConfig` |

---

## Keputusan Desain Penting

| # | Keputusan |
|---|-----------|
| D1 | `ExtractionAgent` boleh raw SQL (bukan LLM, "No Raw SQL from LLM" tidak berlaku) |
| D2 | Mock KIE = explicit flag (`MOCK_KIE`), bukan auto dari `STAGE=development`. Legacy `USE_MOCK_OCR` + validator-nya sudah dihapus total (D24) |
| D3 | `spreadsheet_id` optional di semua MCP-GSheets tools — fallback ke `SHEET_ID` env |
| D4 | Klaudia **tidak boleh minta spreadsheet ID/URL** ke user |
| D5 | `gcp_service_account.json` & `service_account.json` di .gitignore |
| D6 | Worker write_agent include `tool_get_sheet_data` + `tool_list_sheets` (Pattern B/D dependency) |
| D7 | Stream orchestrator pakai manual `__enter__`/`__exit__` karena async generator |
| D8 | MCP log di stdio mode muncul di `logs/fastapi.log` |
| D9 | Vertex AI toggle global — tidak ada hybrid; semua Gemini call ikut flag yang sama |
| D10 | `ChatVertexAI` deprecated sejak v3.2 — pakai `ChatGoogleGenerativeAI` dengan `vertexai=True` |
| D11 | `_ensure_gcp_credentials()` resolve path absolute + export ke `os.environ` agar MCP subprocess inherit |
| D12 | Guardrails scope check twin-prompt (SARA + Financial Advice terpisah). `base.py` (Groq injection) tidak disentuh |
| D13 | `langfuse.flush()` **tidak boleh** di hot path — flush hanya di `container.shutdown()` |
| D14 | `supervisor_node` + `team_supervisor` harus `async def` + `.ainvoke()` |
| D15 | Thinking-disable harus di `ChatGoogleGenerativeAI` path, bukan `llm_client.py` (`google.genai` SDK) — dua code path berbeda. Workers tidak di-disable thinking — butuh reasoning untuk composition pattern |
| D16 | Sheet list cache TTL=60s + event-driven invalidation via `on_sheet_mutation`. Parse pakai `_parse_tool_json_output()` |
| D17 | `RouterWithResponse` TypedDict — combined routing + inline response untuk FINISH path, eliminasi 1 LLM call. Fallback `_emit_final_reply()` jika `response` kosong |
| D18 | Thinking level single source of truth di `.env` (`LLM_THINKING_LEVEL_ROUTING`/`_WORKER`). Worker pakai `low` bukan `minimal` — butuh reasoning untuk Pattern B/C/D |
| D19 | Output guardrail **tidak** twin-prompt — assistant output lebih controlled dari user input. Revisit hanya jika false positive muncul di Langfuse |
| D20 | Multi-provider LLM (`MODEL_PROVIDER=google\|openai`) di `llm.py`: `_build_gemini_llm` (existing, unchanged) vs `_build_openai_llm` (`ChatOpenAI` → vLLM, thinking off via `extra_body`, empty bearer → `"EMPTY"`). Structured output lewat `with_structured(llm, schema)` — OpenAI pakai `method="json_schema"` (guided decoding), Gemini native. Guardrails + KIE **tetap Gemini-only**, tidak ikut switch ini |
| D21 | **DeepSeek sebagai provider ketiga** (`MODEL_PROVIDER=deepseek`). DeepSeek + vLLM sama-sama OpenAI-compatible tapi toggle thinking beda: `_openai_thinking_extra_body(provider, disable)` → DeepSeek `{"thinking":{"type":"disabled"}}`, vLLM `{"chat_template_kwargs":{"enable_thinking":False}}`. `with_structured` jadi per-provider: DeepSeek `method="function_calling"` (json_schema strict masih beta), vLLM `method="json_schema"`. Kredensial per-provider di `.env` (`VLLM_LLM_ENDPOINT`/`VLLM_LLM_API_KEY` vs `DEEPSEEK_BASE_URL`/`DEEPSEEK_API_KEY`); `Settings.active_openai_endpoint()` resolve sesuai `MODEL_PROVIDER`. Ganti provider = edit `MODEL_PROVIDER` + `LLM_MODEL` saja. Live-tested: plain chat + structured routing hijau. Detail: `docs/MODELS.md` |
| D22 | DeepSeek thinking **enabled** balikin `reasoning_content` yang wajib di-round-trip pada tool-call turn (kalau tidak → 400). react workers (langchain-openai) belum round-trip → `LLM_DISABLE_THINKING=true` wajib untuk `deepseek`. KV cache DeepSeek otomatis (no config); prefix completion butuh endpoint `/beta` (belum dipakai) |
| D23 | **KIE routing disederhanakan: `OCR_MODE` dihapus total** (path two-stage Qwen-text→Gemini dibuang, `text_ocr.py` dihapus, `gemini_kie.extract_from_text` dihapus). Backend = `KIE_MODEL` saja: `gemini-*` → `GeminiKIEClient` (full zero-shot prompt.py); selain itu → `VLLMKIEClient` (fine-tuned Qwen, **image-only** — prompt hidup di jinja template vLLM, bukan di kode). Deteksi via `_is_gemini_model()` (prefix `gemini`). `MOCK_KIE` tetap. Env: `VLLM_BASE_URL`→`VLLM_KIE_ENDPOINT`, `AUTH_TOKEN`→`VLLM_KIE_API_KEY`, `VLLM_OCR_MODEL` dihapus (pakai `KIE_MODEL`). Provenance DB: `ocr_model`/`schema_version` (kolom `ocr_lora` sudah di-drop, lihat D24) |
| D24 | **`ocr_lora` + `USE_MOCK_OCR` dihapus total** (image-only KIE terbukti jalan, LoRA-name provenance tak dipakai). Kolom `ocr_lora` di-DROP dari `blob_extraction` (SQLite 3.35+ `ALTER TABLE DROP COLUMN`, 19 row aman); hapus `OCR_LORA_NAME`/`ocr_lora_name`, `KIEClient.lora_name`, param `ocr_lora` di `upsert_extraction` + caller (ingest, tasks). `USE_MOCK_OCR`/`legacy_use_mock_ocr` + `_coalesce_mock_flag` validator dibuang; `MOCK_KIE` jadi `alias` biasa. Provenance tersisa: `ocr_model`, `schema_version` |

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
| O5 | `VLLMKIEClient` (Qwen3.5-4B fine-tuned, image-only) baru construction/wiring — endpoint vLLM belum aktif. Verifikasi nanti: set `KIE_MODEL=<served-name>` + `VLLM_KIE_ENDPOINT`, 1 real upload receipt → cek JSON valid |
| O6 | Frontend mobile (Klaudia native app) — next phase |
| O7 | `MODEL_PROVIDER=openai`: sub-agent tool-calling (sql_agent, data_entry_team via `create_react_agent`) butuh vLLM jalan dengan `--enable-auto-tool-choice --tool-call-parser hermes`. Routing/structured-output sudah jalan tanpa flag itu (json_schema/guided decoding) |
| O8 | Multi-provider switch (D20) belum live-tested terhadap endpoint vLLM asli — baru construction/wiring. Verifikasi: 1 real call tiap path (routing, worker tool-call) setelah GPU session tersedia |
| O9 | DeepSeek (D21): plain chat + structured routing sudah live-tested hijau. Belum diuji end-to-end lewat full graph dengan tool-calling workers (sql_agent, data_entry_team) terhadap MCP. Verifikasi: jalankan `./startup.sh` + 1 alur upload/sheet dengan `MODEL_PROVIDER=deepseek` |
| O10 | DeepSeek thinking mode (D22) belum dipakai — react workers harus round-trip `reasoning_content` dulu sebelum `LLM_DISABLE_THINKING=false` aman untuk deepseek |