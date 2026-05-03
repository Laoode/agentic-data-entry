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
| OCR | `GLM-OCR` via vLLM — saat ini `USE_MOCK_OCR=true` (mock JSON, GLM belum selesai training) |
| DB | SQLite via `mcp-sqlite` (11 tools) |
| Sheets | Google Sheets via `mcp-gsheets` (16 tools, `SHEET_ID` dari env) |
| MCP Transport | **stdio** (default). Rollback ke SSE: `MCP_TRANSPORT=sse ./startup.sh` |
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
| `USE_MOCK_OCR` | `true` = skip vLLM, pakai mock extraction JSON |
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
| O2 | Concurrency: multiple simultaneous file upload di session yang sama |
| O3 | Rate limit Google Sheets API (100 req/100s) — butuh backoff |
| O4 | Observability: structured logging (request_id, session_id, file_id) |
| O5 | `MCPToolRegistry.connect()` tidak ada timeout — pytest hang kalau MCP down |
| O6 | Vertex token usage metadata shape sudah match dev API di google-genai SDK — monitor kalau ada perubahan |