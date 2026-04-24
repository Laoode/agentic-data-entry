# PLAN — Klaudia Receipt Extraction System

> Dokumen ter-versi. Setiap iterasi perbaikan/penambahan di-append sebagai versi baru di bawah (tidak overwrite).
> Format tiap versi: findings → rencana → hasil test → open questions → done criteria.

---

## Plan v1 — Align ke PRD 1.1 + smoke test SQL Agent & Data Entry Team

**Tanggal:** 2026-04-16
**Status:** DONE

### 0. Keputusan dari User (2026-04-16)

| # | Topik | Keputusan |
|---|-------|-----------|
| K1 | `mcp-config.json` & `mcp-config-stdio.json` | Sudah diisi user (SSE di port 8001/8002, stdio via `python main.py`). Saya verifikasi valid — **tidak perlu ubah**. |
| K2 | Spreadsheet ID untuk test MCP-GSheets | Pakai service account yang ada (`mcp-gsheets/service_account.json`, email `mcp-gsheet@hazel-circlet-393014.iam.gserviceaccount.com`). **Butuh user buat satu Google Sheet**, share dengan service account email tsb sebagai Editor, lalu kasih `SHEET_ID` via `.env`. Tanpa ini write-path tidak bisa diuji end-to-end. |
| K3 | Hapus kolom `pages.ocr_output` | **Setuju.** Schema di `mcp-sqlite/app/infra/db_client.py` + project-level init script akan di-update. |
| K4 | GLM-OCR masih training (fine-tune) | **Pakai mockup JSON dulu.** Saya ganti `MOCK_OCR_TEXT` jadi `MOCK_EXTRACTION_JSON` yang sudah sesuai `EXTRACTION_SCHEMA`, return langsung dict tanpa ke vLLM. Real endpoint dipakai nanti saat training kelar. |

### 1. Findings

| # | Area | Kondisi | Target PRD 1.1 | Gap |
|---|------|---------|----------------|-----|
| F1 | Extraction flow | 2-step: GLM-OCR text → Gemini JSON | 1-step: GLM-OCR direct JSON | Refactor `ExtractionAgent` + `OCRClient` |
| F2 | Prompt extraction | English CoT → Gemini | Chinese prompt + schema ke GLM-OCR | Ganti (tapi saat ini pakai mock, jadi prompt hanya disiapkan untuk masa depan) |
| F3 | Kolom `pages.ocr_output` | Ada (di 2 tempat: `mcp-sqlite` dan fixture tests) | Tidak ada | Drop kolom + update `create_page`, `update_page`, `tool_*` di MCP-SQLite |
| F4 | Schema DB init | Ada di `mcp-sqlite/app/infra/db_client.py` (auto-run saat connect) | OK, tapi perlu update tanpa `ocr_output` | Edit SCHEMA_SQL |
| F5 | `app_dev.db` | Terisi (26 sessions, 53 msg, 2 file) | Bersih | Delete file, auto re-create via MCP-SQLite connect |
| F6 | MCP-SQLite test | Cuma cek SSE endpoint reachable | Invoke tool real | Tambah test pakai MCP client, panggil `tool_get_document`, `tool_list_pages`, dst |
| F7 | MCP-GSheets test | Cuma cek SSE endpoint | Invoke tool real (list, read, write, append) | Tambah test pakai MCP client + `SHEET_ID` |
| F8 | SQL Agent (`klaudia/.../sql_agent/`) | Code ada, tapi belum pernah invoked end-to-end | Harus bisa ReAct pakai MCP-SQLite tools | Tambah test integrasi supervisor → sql_agent → MCP |
| F9 | Data Entry Team (`klaudia/.../data_entry_team/`) | Code ada (read/sheet/write subagent) | Harus bisa orchestrate via team supervisor ke MCP-GSheets | Tambah test integrasi supervisor → data_entry_team → MCP |
| F10 | `ExtractionAgent` di PRD section 3.3 | Full kode di PRD menulis langsung ke DB pakai `self.db_client.execute(...)` | Seharusnya pakai MCP-SQLite (konsisten dengan "No Raw SQL from LLM") | **Clarify:** ExtractionAgent bukan LLM → boleh raw SQL, atau harus pakai MCP? (lihat Q1 di bawah) |

### 2. Rencana Eksekusi (per-phase)

**Phase A — Simplify ExtractionAgent ke mock direct-JSON**
- `app/services/extraction/infra/ocr_client.py`:
  - Tambah `MOCK_EXTRACTION_JSON` (dict sesuai `EXTRACTION_SCHEMA` + data receipt contoh)
  - Method baru `extract_json_from_image(bytes) -> dict` dan `extract_json_from_pdf(bytes) -> list[dict]`
  - Di dev mode / `USE_MOCK_OCR=true`: skip vLLM, return mock dict
  - Di production: call GLM-OCR dengan prompt schema (siapkan tapi tidak dites sekarang)
  - Hapus `extract_text_from_image`/`extract_text_from_pdf` lama, hapus `MOCK_OCR_TEXT`
- `app/services/extraction/agents/base.py`:
  - Hapus dep `LLMClient`, `EXTRACTION_PROMPT`, `_extract_structured`
  - Pipeline: `ocr.extract_json_*` → `_validate_schema` → `_save_page`
- Hapus `app/services/extraction/agents/prompt.py`
- Update `container.py` — ExtractionAgent init tanpa `llm_client`
- Update test `tests/integration/agent/test_extraction.py` dengan flow baru

**Phase B — DB reset + drop `ocr_output`**
- Edit `mcp-sqlite/app/infra/db_client.py` → hapus `ocr_output TEXT,` dari SCHEMA_SQL
- Edit `mcp-sqlite/app/tools/page_ops.py` → hapus parameter `ocr_output` dari `create_page` & `update_page`
- Edit `mcp-sqlite/app/server.py` → drop `ocr_output` dari `tool_create_page` & `tool_update_page`
- Edit test fixtures di `tests/integration/agent/test_extraction.py` (sama-sama drop)
- Delete `app_dev.db` — auto re-created pada MCP-SQLite startup

**Phase C — MCP-SQLite end-to-end test**
- New file: `tests/integration/mcp-sqlite/test_tool_invocation.py`
- Start MCP-SQLite via `startup.sh` (atau spawn manual fixture)
- Pakai `mcp.client.session.ClientSession` (SSE) — connect ke `http://localhost:8001/sse`
- Flow test:
  1. `tool_create_document(session_id=1, user_id=1, file_type='image', file_name='t.jpg', total_pages=1)` → dapat doc_id
  2. `tool_create_page(metadata_file_id=doc_id, page_number=1)` → dapat page_id
  3. `tool_save_extraction(page_id, extraction_json=<MOCK_EXTRACTION_JSON>)` → ok
  4. `tool_get_document(doc_id)` → assert row match
  5. `tool_list_pages(doc_id)` → assert length==1
  6. `tool_get_extraction(doc_id, 1)` → assert JSON keys: info, items, payment
  7. `tool_get_session_files(session_id=1)` → assert nested pages

**Phase D — MCP-GSheets end-to-end test** _(butuh `SHEET_ID`)_
- New file: `tests/integration/mcp-gsheets/test_tool_invocation.py`
- `.env` tambah `SHEET_ID=<id from user>`
- Skip semua test kalau `SHEET_ID` belum diset (supaya CI tidak break)
- Flow test (idempotent, test sheet terpisah):
  1. `tool_get_spreadsheet_info(SHEET_ID)` → assert title
  2. `tool_list_sheets(SHEET_ID)` → assert ≥1
  3. `tool_create_sheet(SHEET_ID, title='test_klaudia_tmp')` → dapat new_sheet_id
  4. `tool_append_rows(SHEET_ID, 'test_klaudia_tmp', data=[['store','date','total'],['Indomaret','2026-04-16',15540]])` → ok
  5. `tool_get_sheet_data(SHEET_ID, 'test_klaudia_tmp')` → assert values match
  6. `tool_update_cells(SHEET_ID, 'test_klaudia_tmp', 'A3', [['edited']])` → ok
  7. `tool_clear_range(SHEET_ID, 'test_klaudia_tmp', 'A1:Z10')` → ok
  8. `tool_delete_sheet(SHEET_ID, 'test_klaudia_tmp')` → cleanup

**Phase E — SQL Agent integration test**
- New file: `tests/integration/agent/test_sql_agent.py`
- Seed DB: 1 user, 1 session, 1 metadata_file (status=completed), 1 pages (agent_extracted = mock JSON)
- Build SQL agent with `create_react_agent(llm, get_sql_tools(mcp_sqlite), SQL_AGENT_PROMPT)` — seperti di `klaudia/core/supervisor/agents/sql_agent/agent.py`
- Pertanyaan uji:
  - "Ambil detail file dengan id=1, sebutkan store_name dan grand_total dari page 1"
  - "Berapa total file di session 1?"
- Assert: response berisi field yang benar dari mock JSON

**Phase F — Data Entry Team integration test** _(butuh `SHEET_ID`)_
- New file: `tests/integration/agent/test_data_entry_team.py`
- Build subgraph via `make_data_entry_team(llm, mcp_gsheets)`
- Pertanyaan uji:
  - "Buat sheet baru bernama 'test_entry', lalu append header [tanggal, toko, total] dan data [2026-04-16, Indomaret, 15540]"
  - "Baca isi sheet 'test_entry' dan laporkan"
- Assert: via API Google Sheets langsung, sheet bener dibuat + row bener ter-insert
- Cleanup: delete sheet di akhir

### 3. Open Questions (sebelum/selama eksekusi)

- **Q1 (blocking Phase A):** `ExtractionAgent` di kode PRD §3.3 tulis ke DB via `self.db_client.execute(...)` (raw SQL). Ini konflik dengan prinsip "No Raw SQL from LLM" (§2.1). Opsi:
  - **(a) Tetap raw SQL di ExtractionAgent** — dia bukan LLM, jadi prinsip tidak berlaku. Lebih simpel. ← saya prefer ini.
  - **(b) Ubah ExtractionAgent pakai MCP-SQLite client** — konsisten tapi overhead kompleks (nambah MCP connection dari dalam FastAPI proses, bukan hanya dari supervisor).
- **Q2 (blocking Phase D+F):** Butuh `SHEET_ID` dari spreadsheet real yang sudah di-share ke `mcp-gsheet@hazel-circlet-393014.iam.gserviceaccount.com`. Tolong buat sheet baru (kosong juga OK), share sebagai **Editor**, paste ID-nya.
- **Q3:** `USE_MOCK_OCR` — mau via env flag terpisah (`USE_MOCK_OCR=true`), atau otomatis pakai mock kalau `STAGE=development`? Saya prefer **explicit flag** supaya saat GLM-OCR sudah live, gampang toggle.

### 4. Done Criteria Plan v1

- [x] Phase A: `ExtractionAgent` tanpa `LLMClient`, produce JSON via `OCRClient` mock
- [x] Phase B: schema SQLite tanpa `ocr_output`, DB di-reset, bisa CREATE ulang clean
- [x] Phase C: 7 tool MCP-SQLite dites via MCP client, semua hijau
- [x] Phase D: 8 tool MCP-GSheets dites terhadap real spreadsheet, semua hijau
- [x] Phase E: SQL Agent (ReAct + MCP-SQLite) jawab 2 pertanyaan dengan akurat
- [x] Phase F: Data Entry Team (read/write agents + MCP-GSheets) tool partitioning + single-turn write/read
- [x] `pytest tests/` hijau end-to-end (29 passed, 1 pre-existing LLM client failure)

### 5. Hasil Test (2026-04-16)

**Full suite: 29 passed, 1 failed (pre-existing)**

| Phase | File | Tests | Status | Time |
|-------|------|-------|--------|------|
| A | `tests/integration/agent/test_extraction.py` | 2 | PASS | 0.25s |
| A | `tests/integration/ocr/test_ocr_mock.py` | 2 | PASS | 0.25s |
| C | `tests/integration/mcp-sqlite/test_sqlite_tools.py` | 3 | PASS | 0.25s |
| D | `tests/integration/mcp-gsheets/test_gsheets_tools.py` | 6 | PASS | 25.8s |
| E | `tests/integration/agent/test_sql_agent.py` | 2 | PASS | 9.3s |
| F | `tests/integration/agent/test_data_entry_team.py` | 3 | PASS | 61.9s |
| — | `tests/integration/agent/test_llm_client.py` | 1/2 | 1 FAIL (pre-existing: Gemini returns empty for structured JSON prompt) | |

**Production bugs found and fixed:**

| # | File | Bug | Impact | Fix |
|---|------|-----|--------|-----|
| B1 | `klaudia/interfaces/tool_registry.py` | `StructuredTool.from_function(coroutine=**kwargs)` — no `args_schema` → LangChain wraps args as `{"kwargs": {...}}` → MCP validation fails | **CRITICAL**: No LLM tool call would ever work in production | Built Pydantic `args_schema` from MCP tool's `inputSchema` via `create_model()` |
| B2 | `klaudia/.../data_entry_team/agents.py` | `_normalize_route()` missing — LLM returns `"read_agent.get_sheet_data(...)"` instead of `"read_agent"` → Command routes to non-existent node → silent graph exit | **HIGH**: Team supervisor silently does nothing | Added `_normalize_route()` to extract agent name prefix |
| B3 | `klaudia/.../data_entry_team/agents.py` + `sql_agent/agent.py` | Worker nodes call `.invoke()` (sync) but MCP tools only support async → `NotImplementedError` | **HIGH**: All agent tool calls crash at runtime | Changed to `.ainvoke()` in all worker nodes + team_node wrapper |

### 6. Post-test Production-Readiness Checklist (review dari Phase C–F)

Poin ini diisi setelah test jalan — fokus edge case untuk production:

- [ ] Error handling kalau MCP server down (timeout, retry, circuit breaker)
- [ ] Concurrency: multiple simultaneous file upload di session yang sama
- [ ] Rate limit Google Sheets API (100 req/100s/user per project) — butuh backoff
- [x] Auth: `service_account.json` sekarang ada di repo — **harus dipindah keluar / .gitignore** sebelum push publik
- [ ] Observability: logging structured (request_id, session_id, file_id) untuk trace end-to-end
- [x] **B1 FIXED**: `tool_registry.py` args_schema — semua MCP tools sekarang punya Pydantic schema
- [x] **B2 FIXED**: Team supervisor route normalization — LLM freeform output di-sanitize ke node name valid
- [x] **B3 FIXED**: Semua worker nodes async — `.ainvoke()` bukan `.invoke()`
- [ ] `test_llm_client.py::test_gemini_structured_response` gagal (Gemini returns empty) — kemungkinan prompt format issue dengan `gemini-3-flash-preview` + OpenAI-compat, perlu investigasi
- [ ] `gemini-3-flash-preview` requires `thought_signature` for tool use via OpenAI-compat — LangChain belum support, untuk agent tests pakai `gemini-2.5-flash` dulu

---
 All 6 phases complete. 29/30 tests pass.

  Changes made:

  New test files (Phases C-F):
  - tests/integration/mcp-sqlite/test_sqlite_tools.py — 3 tests, full CRUD flow via MCP SSE
  - tests/integration/mcp-gsheets/test_gsheets_tools.py — 6 tests, create/append/read/update/clear/delete
  - tests/integration/agent/test_sql_agent.py — 2 tests, live LLM + MCP-SQLite ReAct
  - tests/integration/agent/test_data_entry_team.py — 3 tests, tool partitioning + single-turn write/read

  Production bugs fixed (3):

  ┌──────────────────────────────────────────────────────┬────────────────────────────────────────────────┬──────────┐
  │                         Bug                          │                      File                      │ Severity │
  ├──────────────────────────────────────────────────────┼────────────────────────────────────────────────┼──────────┤
  │ args_schema missing → all LLM tool calls fail        │ klaudia/interfaces/tool_registry.py            │ CRITICAL │
  ├──────────────────────────────────────────────────────┼────────────────────────────────────────────────┼──────────┤
  │ Route normalization → team supervisor silently exits │ klaudia/.../data_entry_team/agents.py          │ HIGH     │
  ├──────────────────────────────────────────────────────┼────────────────────────────────────────────────┼──────────┤
  │ Sync .invoke() on async-only tools → crash           │ sql_agent/agent.py + data_entry_team/agents.py │ HIGH     │
  └──────────────────────────────────────────────────────┴────────────────────────────────────────────────┴──────────┘

  Known issues logged in PLAN.md:
  - gemini-3-flash-preview requires thought_signature for tools (LangChain doesn't support yet) — agents use gemini-2.5-flash
  - 1 pre-existing test_llm_client.py failure (Gemini empty response)

✻ Brewed for 8m 55s

※ recap: All 6 test phases for the receipt extraction system are done with 29/30 passing, and 3 critical production bugs in the agent tool wiring.

※ Plan v1 is Done ※

## Plan v2 — Switch to langchain-google-genai

**Tanggal:** 2026-04-16 (plan) → 2026-04-19 (eksekusi + hasil)
**Status:** DONE

### 0. Konteks

Plan v1 selesai dengan 29/30 tests pass. 1 test gagal (`test_gemini_structured_response`) karena:
- `gemini-3-flash-preview` returns empty via OpenAI-compat endpoint
- `gemini-3-flash-preview` requires `thought_signature` for tool use via OpenAI-compat — LangChain `ChatOpenAI` tidak support
- Agent tests forced to use `gemini-2.5-flash` sebagai workaround

**Solusi:** Switch dari `langchain-openai` + OpenAI-compat endpoint ke `langchain-google-genai` + native Gemini API, yang handles `thought_signature` secara otomatis.

### 1. Phase A — Switch to langchain-google-genai (DONE)

**Goal:** Replace `langchain-openai` + OpenAI-compat with `langchain-google-genai` native API → enable `gemini-3-flash-preview` for all agents → 30/30 tests.

#### 1.1 Rencana Perubahan

| File | Dari | Ke |
|------|------|----|
| `klaudia/pyproject.toml` | `langchain-openai==0.3.13` | `langchain-google-genai>=4.0.0` |
| `pyproject.toml` | `openai>=1.30.0` | `google-genai>=1.0.0` |
| `klaudia/core/supervisor/agent.py` | `ChatOpenAI(base_url=..., api_key=...)` | `ChatGoogleGenerativeAI(model=..., google_api_key=...)` |
| `app/services/core/llm_client.py` | `httpx` + OpenAI-compat | `google-genai` SDK native |
| `app/services/core/container.py` | `SupervisorAgent(llm_endpoint=...)` | `SupervisorAgent(llm_api_key=...)` |
| `config/settings.py` | `llm_provider`, `llm_endpoint` | Remove (not needed for native API) |
| `tests/.../test_sql_agent.py` | `ChatOpenAI`, `gemini-2.5-flash` | `ChatGoogleGenerativeAI`, `gemini-3-flash-preview` |
| `tests/.../test_data_entry_team.py` | Same | Same |
| `tests/.../test_llm_client.py` | Adapt to new LLMClient | |
| `.env.template` | `LLM_PROVIDER`, `LLM_ENDPOINT` | Remove |

#### 1.2 Tidak Berubah

- MCP tools, tool_registry, prompts, graph structure, state management
- Guardrails prompt injection (Groq/Llama)
- ExtractionAgent/OCRClient (uses vLLM, not Gemini)
- All test logic — hanya swap LLM instantiation

#### 1.3 Done Criteria Phase A

- [x] `langchain-google-genai` installed, `langchain-openai` removed
- [x] SupervisorAgent uses `ChatGoogleGenerativeAI`
- [x] LLMClient uses `google-genai` SDK
- [x] All agent tests use `gemini-3-flash-preview`
- [x] `test_gemini_structured_response` passes (previously failed)

### 2. Hasil Test (2026-04-19)

`uv run pytest tests/ -v` → **30 passed, 0 failed** in 149.21s.

| Suite | File | Tests | Status |
|-------|------|-------|--------|
| Agent | `tests/integration/agent/test_data_entry_team.py` | 3 | ✅ |
| Agent | `tests/integration/agent/test_extraction.py` | 2 | ✅ |
| Agent | `tests/integration/agent/test_guardrails.py` | 4 | ✅ |
| Agent | `tests/integration/agent/test_llm_client.py` | 2 | ✅ (incl. `test_gemini_structured_response`) |
| Agent | `tests/integration/agent/test_sql_agent.py` | 2 | ✅ |
| DB | `tests/integration/database/test_db_client.py` | 4 | ✅ |
| MCP | `tests/integration/mcp-gsheets/test_gsheets_tools.py` | 6 | ✅ |
| MCP | `tests/integration/mcp-gsheets/test_mcp_gsheets.py` | 1 | ✅ |
| MCP | `tests/integration/mcp-sqlite/test_mcp_sqlite.py` | 1 | ✅ |
| MCP | `tests/integration/mcp-sqlite/test_sqlite_tools.py` | 3 | ✅ |
| OCR | `tests/integration/ocr/test_ocr_mock.py` | 2 | ✅ |
| **Total** | | **30** | **✅** |

### 3. Bug yang Ditemukan Saat Eksekusi Plan v2

**B4 — Gemini 400 INVALID_ARGUMENT: `items` missing on nested arrays** (`klaudia/interfaces/tool_registry.py`)

- **Gejala:** `test_write_agent_appends_row` gagal saat agent mencoba memanggil `tool_append_rows`/`tool_update_cells`/`tool_batch_update_cells`. Error dari Gemini: `GenerateContentRequest.tools[0].function_declarations[0].parameters.properties[data].items.items: missing field`.
- **Root cause:**
  1. FastMCP mengekspos `list[list[Any]]` sebagai JSON Schema `{"type": "array", "items": {"type": "array", "items": {}}}`.
  2. `langchain-google-genai._function_utils._dict_to_genai_schema` memperlakukan dict kosong `{}` sebagai falsy (`if schema:`) dan mengembalikan `None`, sehingga `items` pada inner array di-drop sebelum dikirim ke Gemini.
  3. Gemini menolak `type: array` tanpa `items`.
- **Fix:** Menambah helper `_normalize_schema()` di `klaudia/interfaces/tool_registry.py` yang mengganti `items` kosong/hilang dengan `{"type": "string"}` (permissive placeholder) sebelum schema diserahkan ke `StructuredTool`. Sekaligus mengganti jalur `_args_model()` + Pydantic `create_model` dengan dict passthrough (`StructuredTool.args_schema` menerima dict JSON Schema langsung), sehingga skema MCP tidak lagi kehilangan field `items` via Pydantic roundtrip.
- **Dampak:** Semua 3 tool GSheets dengan payload `list[list[Any]]` sekarang callable dari `gemini-3-flash-preview`.

### 4. Done Criteria Plan v2

- [x] Full `pytest tests/` → 30/30 passed
- [x] `test_gemini_structured_response` passes (sebelumnya gagal di Plan v1)
- [x] `langchain-google-genai` installed, `langchain-openai` removed
- [x] SupervisorAgent uses `ChatGoogleGenerativeAI`
- [x] LLMClient uses `google-genai` SDK
- [x] All agent tests use `gemini-3-flash-preview`
- [x] Bug B4 (Gemini tool-schema nested array) fixed

#### POTENTIAL CONCERNS:                                                                                                                            
  - Fix B4 mempertipiskan tipe inner-array menjadi string; untuk tool_append_rows(data=list[list[Any]]) aman karena GSheets menerima string.     
  Kalau tool lain kedepannya butuh nested numeric/bool dengan ketat, bisa re-assess pilihan placeholder.                                         
  - MCPToolRegistry.connect() masih tidak punya timeout — kalau MCP server down, pytest akan hang (dicatat di Plan v1 post-test checklist, bukan
  regresi baru). Siap untuk Plan v3. 

※ Plan v2 is Done ※

---

## Plan v3 — SSE Streaming: Token-by-token + Agentic Progress

**Tanggal:** 2026-04-19
**Status:** DONE
**Scope:** Backend only. Persiapan kontrak event untuk frontend di Plan v5.

### 1. Tujuan

Response Klaudia muncul kata-per-kata (seperti ChatGPT) plus event "agentic progress" (step routing, tool calls, extraction) sepanjang pipeline. Non-streaming endpoint (`POST /v1/chat`) tetap dipertahankan apa adanya untuk kebutuhan test & fallback.

### 2. Arsitektur Streaming

```
Client ──SSE── FastAPI (/v1/chat/stream)
                    │
                    ▼
        KlaudiaOrchestrator.stream()          (async generator, event dict)
                    │
        ┌───────────┼───────────────┐
        │ guardrail │ extraction    │
        │ session   │ save message  │
        └───────────┼───────────────┘
                    ▼
        SupervisorAgent.stream_conversation() (wraps graph.astream)
                    │
                    ▼
        LangGraph astream(stream_mode=["messages","updates"])
                    │
        ┌───────────┴───────────────┐
        │ messages  : per-token     │ ← filter by tag "final_answer"
        │ updates   : node state    │ ← emit "step" + harvest tool names
        └───────────────────────────┘
```

Kunci desain: **tag-based filtering pada LLM call**. Supervisor punya 2 panggilan LLM:
- routing (`with_structured_output(Router)`) — di-tag `nostream` agar tool-call chunk Gemini tidak bocor ke frontend.
- final reply (`llm.invoke(state["messages"])`) — di-tag `final_answer` agar hanya token inilah yang di-emit sebagai `type: token` ke client.

Token dari sub-agent (sql_agent ReAct loop, data_entry_team) tidak di-stream ke frontend — hanya namanya yang tampil via event `step`/`tool`.

### 3. Event Schema (SSE)

Frame SSE: `event: <type>\ndata: <json>\n\n`

| Event       | Payload fields                                                 | Emitted by                         |
|-------------|----------------------------------------------------------------|------------------------------------|
| `session`   | `session_id`                                                   | orchestrator (awal)                |
| `guardrail` | `stage` (input/output), `status` (checking/passed/rejected), `message?` | orchestrator                    |
| `extraction`| `status`, `file_name`, `file_id?`, `pages?`, `summary?`        | orchestrator                        |
| `step`      | `node`, `next`                                                 | supervisor (graph updates mode)     |
| `tool`      | `name`                                                         | supervisor (harvest dari update)    |
| `token`     | `text`                                                         | supervisor (messages mode, tag)     |
| `done`      | `session_id`, `processing_time_ms`, `tools_used`, `content`    | orchestrator (akhir)                |
| `error`     | `message`                                                      | orchestrator / endpoint (on error)  |

Client merakit teks dari rentetan `token.text`; `done.content` dipakai untuk rekonsiliasi post-guardrail-output (karena output guardrail bisa mengganti teks setelah streaming selesai).

### 4. Perubahan Kode

#### 4.1 `klaudia/core/supervisor/router.py`
Tambah tag pada 2 LLM call di `supervisor_node`:

```python
router_llm = llm.with_structured_output(Router).with_config({"tags": ["nostream"]})
response = router_llm.invoke(messages)
...
final_llm = llm.with_config({"tags": ["final_answer"]})
reply = final_llm.invoke(state["messages"])
```

#### 4.2 `klaudia/core/supervisor/agent.py`
Tambah `async def stream_conversation(messages, extraction_data) -> AsyncIterator[dict]`:
- panggil `self._graph.astream(state, config={"recursion_limit": 50}, stream_mode=["messages", "updates"])`
- mode `messages`: filter `"final_answer" in tags` → yield `{"type":"token","data":{"text":…}}`
- mode `updates`: yield `{"type":"step","data":{"node","next"}}` plus `{"type":"tool","data":{"name"}}` untuk setiap message ber-`name`
- fallback: kalau callback streaming Gemini tidak nyala, ambil konten AIMessage terakhir dari node `supervisor`
- terakhir yield `{"type":"final","data":{"content","tools_called","metadata":{"routed_to"}}}`

`process_conversation()` tetap apa adanya (non-breaking).

#### 4.3 `app/services/core/orchestrator.py`
Tambah `async def stream(messages, session_id, user_id, user_name) -> AsyncIterator[dict]`:
- replicate pipeline `process()` tapi yield event di setiap milestone
- konsumsi `supervisor.stream_conversation()`; event `final` tidak diteruskan — dipakai untuk rakit `content` + `tools_used`
- output guardrail tetap dijalankan; kalau gagal, emit `guardrail/output/rejected` dan swap `content` di event `done`
- exception di-wrap jadi `{"type":"error","data":{"message":…}}`

`process()` tetap; dipakai oleh `/v1/chat` non-streaming + test-suite lama.

#### 4.4 `app/routes/v1/chat.py`
- tambah `POST /v1/chat/stream` → `StreamingResponse(event_source(), media_type="text/event-stream", headers={Cache-Control, Connection, X-Accel-Buffering: no})`
- `event_source()` iterasi `orchestrator.stream(...)` dan format jadi frame SSE
- honor `req.is_disconnected()` agar client yang putus menghentikan loop
- endpoint `POST /v1/chat` tidak berubah

### 5. Testing

File baru: `tests/integration/agent/test_streaming.py` (mengikuti pola `test_sql_agent.py` — skip kalau `LLM_API_KEY` kosong).

- `test_stream_conversation_emits_final_event_with_content`: assert event `final` muncul terakhir, ada `step`, `final.content` tidak kosong, `routed_to ∈ {FINISH, sql_agent, data_entry_team}`.
- `test_stream_conversation_emits_only_known_event_types`: semua event harus salah satu dari `{step, tool, token, final}`.

Hasil run:

```
tests/integration/agent/test_streaming.py::test_stream_conversation_emits_final_event_with_content PASSED
tests/integration/agent/test_streaming.py::test_stream_conversation_emits_only_known_event_types     PASSED
2 passed in 22.29s
```

Verifikasi wiring FastAPI:

```python
>>> [r.path for r in app.routes if 'chat' in r.path]
['/v1/chat', '/v1/chat/stream']
```

### 6. Cara Pakai dari Client

```bash
curl -N -X POST http://localhost:8000/v1/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Hi"}],"user_id":1}'
```

Stream frame contoh:

```
event: session
data: {"session_id": 12}

event: guardrail
data: {"stage": "input", "status": "passed"}

event: step
data: {"node": "supervisor", "next": "FINISH"}

event: token
data: {"text": "Hel"}

event: token
data: {"text": "lo"}

event: done
data: {"session_id": 12, "processing_time_ms": 1845, "tools_used": [], "content": "Hello"}
```

### 7. Catatan untuk Plan v5 (Frontend)

- Parser SSE client cukup dispatch berdasarkan `event.type`; state machine: `session → guardrail → (extraction?) → step* → token* → done`.
- Token append ke state draft; ketika `done` datang, replace draft dengan `done.content` untuk antisipasi output-guardrail swap.
- `step` & `tool` bisa ditampilkan sebagai "Klaudia sedang memeriksa database…" / "Menulis ke GSheets…" (mapping node→label di frontend).
- Error handling: event `error` → tampilkan toast; juga handle `EventSource` close.

※ Plan v3 is Done ※

---

## Plan v4 — Observability dengan Langfuse

**Tanggal:** 2026-04-24
**Status:** DONE

### 1. Findings (State Sebelum v4)

| # | Area | Kondisi | Gap |
|---|------|---------|-----|
| F1 | Langfuse SDK | Belum terpasang | Tambah `langfuse>=4.5.0` (v4.x pakai OpenTelemetry di bawahnya) |
| F2 | LangChain/LangGraph tracing | Tidak ada | Butuh `CallbackHandler` di-inject ke `graph.ainvoke` / `graph.astream` |
| F3 | Non-LangChain LLM call | `LLMClient` (google-genai), `check_prompt_injection` (Groq), `OCRClient` (vLLM) tidak tercatat | Butuh manual span (`as_type="generation"`) |
| F4 | Top-level pipeline phase | Orchestrator `process()` / `stream()` tidak ada span wrapper | Butuh agent-level span + `trace_attributes` untuk propagate session/user id |
| F5 | Fail-behaviour | Belum ada; risiko hard-fail kalau Langfuse down | Semua wrapper wajib fail-open (tracing failure ≠ pipeline failure) |

### 2. Keputusan Desain

| # | Keputusan | Alasan |
|---|-----------|--------|
| D1 | Satu kelas `LangfuseService` sebagai thin wrapper di `app/services/core/observability.py` | DRY — client init + CallbackHandler + `span()` context + `trace_attributes()` + `langchain_config()` di satu tempat. Komponen lain cukup terima `Optional[LangfuseService]`. |
| D2 | **Fail-open** di semua level: kalau credential kosong → `enabled=False`, semua method no-op; kalau runtime error → log debug, lanjut | Observability tidak boleh menjatuhkan production pipeline. |
| D3 | LangChain/LangGraph di-instrument via `CallbackHandler` + `langchain_config()` (merge ke RunnableConfig) | v4 SDK sudah support; zero-touch di dalam graph code. Supervisor routing, sub-agent ReAct loop, LLM chunks → semua auto-traced. |
| D4 | Non-LangChain call (google-genai, Groq, vLLM) pakai `client.start_as_current_observation(as_type="generation", ...)` manual | Supaya usage tokens + prompt/response visible di dashboard sebagai proper "generation" (bukan generic span). |
| D5 | Orchestrator wrap seluruh turn dengan `span(as_type="agent")` + `trace_attributes(session_id, user_id, tags)` | Semua sub-span otomatis ikut parent trace + bisa di-filter per session di dashboard. |
| D6 | Pass `session_id`/`user_id` ke SupervisorAgent lewat `process_conversation` / `stream_conversation` argument, lalu di-inject ke RunnableConfig via `_graph_config()` helper | Sebelumnya supervisor buta terhadap context; sekarang trace Langfuse bisa di-filter dari dashboard. |
| D7 | Stream orchestrator pakai **manual `__enter__` / `__exit__`** untuk contextmanager, bukan `with` block | Async generator + `with` + `yield` = exit tidak deterministik. Manual enter/exit di `try/finally` aman untuk kasus streaming. |
| D8 | Tag trace dengan `["klaudia", "chat"]` / `["klaudia", "chat", "stream"]` / `["klaudia", "supervisor"]` | Filter cepat di dashboard antara chat vs stream vs sub-agent. |

### 3. Arsitektur Trace di Langfuse

```
Trace (root — session_id + user_id propagated)
├── klaudia.process  (agent)              ← orchestrator top-level
│   ├── guardrail.validate_input  (guardrail)
│   │   ├── guardrail.prompt_injection  (generation, Groq)
│   │   └── guardrail.scope_check       (generation, Gemini)
│   ├── extraction_agent.process  (agent, kalau ada attachment)
│   │   └── glm-ocr.extract_image     (generation, vLLM)
│   ├── LangGraph: klaudia.supervisor.invoke  (LangChain, auto)
│   │   ├── supervisor node
│   │   │   ├── router LLM call           (tag: nostream)
│   │   │   └── final reply LLM call      (tag: final_answer)
│   │   ├── sql_agent node               (ReAct + MCP tool calls)
│   │   └── data_entry_team node         (per sub-agent + MCP tool calls)
│   └── guardrail.validate_output  (guardrail)
│       └── guardrail.output_check     (generation, Gemini)
```

Stream variant (`klaudia.stream`) mirror sama tapi di-wrap manual contextmanager karena async generator.

### 4. Testing

Dua lapis:

**Layer A — unit (hermetic, selalu jalan):** `tests/unit/test_observability.py`
- 6 test yang verify fail-open semantics: missing credential → disabled; `LANGFUSE_ENABLED=false` → disabled; `langchain_config()` return `{}` saat disabled; `span()` yield `None` saat disabled; `trace_attributes()` no-op; `flush/shutdown` safe.

**Layer B — smoke (live, skip kalau cred kosong):** `tests/integration/observability/test_langfuse.py`
- 4 test yang benar-benar emit trace ke Langfuse cloud: init, manual span, trace_attributes + nested span, `langchain_config()` shape saat enabled.
- Fixture **module-scoped** (bukan function-scoped) — Langfuse 4.x pakai process-global OTel tracer, re-init setelah shutdown bisa deadlock. Satu instance per module, shutdown sekali di akhir.

Hasil run:

```
tests/unit/test_observability.py .......... 6/6 PASSED (0.06s)
tests/integration/observability/test_langfuse.py .... 4/4 PASSED (1.24s)
tests/integration/agent/test_extraction.py .......... PASSED
tests/integration/agent/test_guardrails.py .......... 4/4 PASSED
============================== 16 passed in 12.04s =============================
```
※ Plan v4 is Done ※

---

## Plan v4.1 — Catatan Implementasi & Lessons Learned

**Tanggal:** 2026-04-24
**Status:** DONE (appendix ke v4)

### 1. Bug yang Di-catch Saat Implementasi

#### 1.1 `LLMClient.shutdown` hilang
Saat refactor `llm_client.py` untuk tambah `_nullspan()` helper, method `async def shutdown(self)` tidak sengaja ikut ter-indent ke dalam generator `_nullspan()` (jadi body-nya tidak pernah jalan, dan `LLMClient` kehilangan method `shutdown`). Ini baru ketahuan waktu `KlaudiaContainer.shutdown()` call `await self.llm_client.shutdown()` — belum fail di runtime karena container shutdown path tidak di-test by default.

**Fix:** pindah `_nullspan()` + `contextmanager` import ke atas module; `shutdown()` kembali jadi method `LLMClient`.

#### 1.2 `_nullctx()` referenced but undefined
`orchestrator.py` sudah pakai `_nullctx()` di `process()` dan `stream()` tapi helper-nya belum di-define di module. Python tidak complain karena baru di-evaluate saat runtime; test-lah yang expose.

**Fix:** tambah `@contextmanager def _nullctx(): yield None` di atas class.

### 2. Lessons

| # | Observasi | Implikasi |
|---|-----------|-----------|
| L1 | Langfuse 4.x pakai **OpenTelemetry global tracer provider**. Multiple `Langfuse()` instances dalam satu process share state — `shutdown()` di test pertama bikin test kedua deadlock. | Semua test integrasi Langfuse harus pakai fixture **module/session-scoped**, bukan function-scoped. |
| L2 | `tail -N` di shell pipe **tidak streaming** — menunggu EOF. Waktu test lama, output kelihatan kosong sampai selesai. | Untuk test run lama, jangan pipe ke `tail` di background. Run langsung atau pakai `--capture=no`. |
| L3 | Async generator + `with` contextmanager + `yield` tidak reliable. `yield` di dalam `with` tidak trigger `__exit__` deterministik saat generator di-close. | Pakai manual `__enter__` / `__exit__` di try-except-finally untuk async generator yang butuh bungkus span. |
| L4 | Fail-open **bukan optional** untuk observability. Kalau Langfuse flush timeout 30s terjadi saat production down, bisa cascade ke latency user-facing. | Semua wrapper `try/except` harus swallow + log debug, tidak pernah raise ke caller. |

### 3. Siap untuk Plan v5

Dengan observability jalan, Plan v5 (React Native + Expo iOS) bisa dimulai dengan confidence:
- Semua bug di flow agent bisa di-replay dari dashboard per `session_id`.
- Pertanyaan dari user di mobile app → trace langsung muncul di Langfuse, tinggal filter by user_id.
- Sebelum ship ke TestFlight, sanity check visual di Langfuse sudah cukup untuk audit end-to-end.

※ Plan v4.1 is Done ※

## Plan v4.2 Fix Klaudia agent yang masih minta spreadsheet ID padahal SHEET_ID sudah di env
CHANGES MADE:                                                                                                                                  
- mcp-gsheets/app/server.py: 14 tool di-refactor. spreadsheet_id jadi Optional di semua tool. Tambah helper _resolve_sheet_id() yang pakai      SheetsContext.default_sheet_id (sudah ada, loaded dari SHEET_ID env) kalau arg kosong. tool_get_multiple_sheet_data pakai fallback per-query.   tool_copy_sheet punya 2 slot (src_, dst_), keduanya optional.
- klaudia/core/supervisor/agents/data_entry_team/prompts.py: tambah rule eksplisit ke semua 4 prompt ("never ask for spreadsheet ID — server has default"). Read agent juga diminta default-kan ke list_sheets → get_sheet_data kalau user generic.
- klaudia/core/supervisor/prompts.py: top-level Klaudia persona dapat aturan "JANGAN minta spreadsheet ID/URL".                                
THINGS I DIDN'T TOUCH:                                                                                                                         
- Internal ops (mcp-gsheets/app/tools/*.py): tetap wajib spreadsheet_id: str — fallback hanya di boundary (MCP tool layer), bukan di business logic. Good separation.
- mcp-sqlite/*: tidak ada masalah serupa.
- Test files: semua pakai kwargs, jadi tidak pecah meski saya re-order parameter.