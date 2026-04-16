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
- [ ] Mock tidak leak ke prod: env flag `USE_MOCK_OCR` harus false di prod
- [ ] Schema migration strategy kalau `EXTRACTION_SCHEMA` berkembang
- [x] Auth: `service_account.json` sekarang ada di repo — **harus dipindah keluar / .gitignore** sebelum push publik
- [ ] SQL Agent: guard terhadap prompt injection yang memicu tool call berbahaya
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

## Plan v2 — CI/CD Pipeline + Switch to langchain-google-genai

**Tanggal:** 2026-04-16
**Status:** IN PROGRESS

### 0. Konteks

Plan v1 selesai dengan 29/30 tests pass. 1 test gagal (`test_gemini_structured_response`) karena:
- `gemini-3-flash-preview` returns empty via OpenAI-compat endpoint
- `gemini-3-flash-preview` requires `thought_signature` for tool use via OpenAI-compat — LangChain `ChatOpenAI` tidak support
- Agent tests forced to use `gemini-2.5-flash` sebagai workaround

**Solusi:** Switch dari `langchain-openai` + OpenAI-compat endpoint ke `langchain-google-genai` + native Gemini API, yang handles `thought_signature` secara otomatis.

### 1. Phase A — CI/CD Pipeline + Initial Push (DONE)

**Tanggal:** 2026-04-16

#### 1.1 Security Audit (sebelum push)

| # | Issue | Severity | Action |
|---|-------|----------|--------|
| S1 | `tests/api/gemini.curl` — real Google API key | CRITICAL | Added `tests/api/*.curl` to `.gitignore` |
| S2 | `tests/api/groq.curl` — real Groq API key | CRITICAL | Added `tests/api/*.curl` to `.gitignore` |
| S3 | `app_dev.db` — dev database not ignored | HIGH | Added `*.db` to `.gitignore` |
| S4 | `docs/PRD.md` line 78 — real `AUTH_TOKEN` value | MEDIUM | Redacted to `<your-vllm-auth-token>` |
| S5 | `docs/PRD.md` line 77 — real vLLM endpoint URL | MEDIUM | Redacted to `<your-vllm-endpoint>` |
| S6 | `.env.template` — real vLLM URL | MEDIUM | Cleared value |
| S7 | `sample-data/` — 200 receipt images (large binaries) | LOW | Added to `.gitignore` |

#### 1.2 Repository Setup

| Repo | URL | Branch | Status |
|------|-----|--------|--------|
| `klaudia` | https://github.com/Laoode/klaudia | `feat/initial-setup` | Pushed |
| `mcp-sqlite` | https://github.com/Laoode/mcp-sqlite | `feat/initial-setup` | Pushed |
| `mcp-gsheets` | https://github.com/Laoode/mcp-gsheets | `feat/initial-setup` | Pushed (updated from existing) |
| `agentic-data-entry` | https://github.com/Laoode/agentic-data-entry | `feat/initial-setup` | Pushed (main repo + submodules) |

#### 1.3 Submodule Configuration

```
[submodule "klaudia"]     → https://github.com/Laoode/klaudia.git (branch: main)
[submodule "mcp-sqlite"]  → https://github.com/Laoode/mcp-sqlite.git (branch: main)
[submodule "mcp-gsheets"] → https://github.com/Laoode/mcp-gsheets.git (branch: main)
```

#### 1.4 CI/CD Pipeline (`.github/workflows/ci.yml`)

```
Jobs:
1. lint       — ruff check + ruff format (app/, klaudia/, config/, tests/)
2. unit-test  — pytest unit/mock tests (no live API needed)
```

Triggered on: push to `main`/`feat/**`, PRs to `main`.

#### 1.5 .gitignore Protections

```
*.db                    # Database files
tests/api/*.curl        # API test files with real tokens
sample-data/            # Large binary files
service_account.json    # Google credentials
.env                    # Environment variables
.claude/                # Claude Code dev files
CLAUDE.md               # Claude Code instructions
```

### 2. Phase B — Switch to langchain-google-genai (PENDING)

**Goal:** Replace `langchain-openai` + OpenAI-compat with `langchain-google-genai` native API → enable `gemini-3-flash-preview` for all agents → 30/30 tests.

#### 2.1 Rencana Perubahan

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

#### 2.2 Tidak Berubah

- MCP tools, tool_registry, prompts, graph structure, state management
- Guardrails prompt injection (Groq/Llama)
- ExtractionAgent/OCRClient (uses vLLM, not Gemini)
- All test logic — hanya swap LLM instantiation

#### 2.3 Done Criteria Phase B

- [ ] `langchain-google-genai` installed, `langchain-openai` removed
- [ ] SupervisorAgent uses `ChatGoogleGenerativeAI`
- [ ] LLMClient uses `google-genai` SDK
- [ ] All agent tests use `gemini-3-flash-preview`
- [ ] `test_gemini_structured_response` passes (previously failed)
- [ ] Full `pytest tests/` → **30/30 passed**

### 3. Open Questions

- **Q1:** Setelah PR `feat/initial-setup` di-merge ke `main` di keempat repo, submodule refs perlu di-update di main repo. Merge order: submodules dulu (klaudia, mcp-sqlite, mcp-gsheets), baru main repo.
- **Q2:** Phase B changes akan di-push ke branch baru (`feat/gemini-native`) setelah `feat/initial-setup` di-merge.

---
