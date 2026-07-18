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
| Guardrails | Groq/Llama (prompt injection) + Gemini/Deepsek-v4-Flash via `LLMClient` (scope check, output check) |
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
| `MOCK_KIE` | `true` = return content-keyed fixture from `sample-data/labels/` (offline).
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
| B19 | `router.py` + `_content.py` | DeepSeek (thinking disabled) menaruh reasoning di `content` → scratchpad ("tapi tunggu dulu...") bocor ke user via **passthrough** (worker text diemit verbatim). | Re-voice by **marker semantics** (lihat B21). `strip_internal_markers` balik ke buang token saja (simpan semua teks sbg grounding). Worker cukup pegang **voice card** ringkas, bukan full persona |
| B21 | `router.py` | Setelah B19 di-set "SELALU re-voice", `[CLARIFY]` (pertanyaan ke user) ikut di-re-voice → LLM **menjawab pertanyaannya sendiri**: worker tanya "ketik 'ya, hapus semua' utk konfirmasi", re-voice malah output `"ya, hapus semua"` (bahaya: konfirmasi mass-delete palsu). Ini engineering bug (peran LLM ambigu: disuruh "tulis reply" utk konten yg justru pertanyaan ke user), bukan model jelek | **Hybrid by marker**: `[WRITE_DONE]/[READ_DONE]/[SHEET_DONE]` (laporan fakta) → re-voice full persona; `[CLARIFY]` (pertanyaan) → **passthrough verbatim** (strip marker + scrub), TIDAK di-re-voice. Restore safety property dari desain passthrough lama utk clarify |
| B22 | `router.py` `_prepare_finish_messages` | Worker report di-wrap sbg `HumanMessage(name=...)` → LLM re-voice baca tabel worker sbg **input user**, jadi bales "Sudah saya rangkum di atas kak ✅" (data hilang, user nggak pernah lihat "di atas"). Non-deterministic (kadang reproduce, kadang enggak) → keliatan di e2e whitebox | **Fold-in**: worker report TIDAK lagi jadi turn percakapan. Teksnya di-fold ke system instruction sbg blok berlabel `=== RESULT YOU JUST PRODUCED (internal; user has NOT seen it; NOT said by user) ===`. Message list ke final LLM = [persona, user turns, instruction+RESULT]. `_build_final_instruction(source)` compose; DELIVER rules larang "shown above"/"sudah di atas", wajib reproduce full tabel. Peran LLM jadi unambiguous |
| B20 | `data_entry_team/agents.py` + `prompts.py` | Team supervisor buta keberadaan sheet (persona di-strip di 168) → "buatkan sheet juli, masukkan ini" langsung ke write_agent → write_agent nolak/[CLARIFY] "buat sheet dulu". Salah urutan | **Deterministic compound sequencer**: create-intent + write-intent → `sheet_agent` dulu, parkir `write_agent` via `pending_worker`; setelah `[SHEET_DONE]` jalankan parked worker. Classifier dapat `sheets_context` (sheet-aware). write_agent trust sheet yg baru dibuat (SHEET_DONE exception) |

---

## Keputusan Desain Penting

| # | Keputusan |
|---|-----------|
| D1 | `ExtractionAgent` boleh raw SQL (bukan LLM, "No Raw SQL from LLM" tidak berlaku) |
| D2 | Mock KIE = explicit flag (`MOCK_KIE`), bukan auto dari `STAGE=development`.|
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
| D16 | Sheet list cache TTL=10s + event-driven invalidation via `on_sheet_mutation`. Parse pakai `_parse_tool_json_output()` |
| D17 | `RouterWithResponse` TypedDict — combined routing + inline response untuk FINISH path, eliminasi 1 LLM call. Fallback `_emit_final_reply()` jika `response` kosong |
| D18 | Thinking level single source of truth di `.env` (`LLM_THINKING_LEVEL_ROUTING`/`_WORKER`). Worker pakai `low` bukan `minimal` — butuh reasoning untuk Pattern B/C/D |
| D19 | Output guardrail **tidak** twin-prompt — assistant output lebih controlled dari user input. Revisit hanya jika false positive muncul di Langfuse |
| D20 | Multi-provider LLM (`MODEL_PROVIDER=google\|openai`) di `llm.py`: `_build_gemini_llm` (existing, unchanged) vs `_build_openai_llm` (`ChatOpenAI` → vLLM, thinking off via `extra_body`, empty bearer → `"EMPTY"`). Structured output lewat `with_structured(llm, schema)` — OpenAI pakai `method="json_schema"` (guided decoding), Gemini native. Guardrails + KIE **tetap Gemini-only**, tidak ikut switch ini |
| D21 | **DeepSeek sebagai provider ketiga** (`MODEL_PROVIDER=deepseek`). DeepSeek + vLLM sama-sama OpenAI-compatible tapi toggle thinking beda: `_openai_thinking_extra_body(provider, disable)` → DeepSeek `{"thinking":{"type":"disabled"}}`, vLLM `{"chat_template_kwargs":{"enable_thinking":False}}`. `with_structured` jadi per-provider: DeepSeek `method="function_calling"` (json_schema strict masih beta), vLLM `method="json_schema"`. Kredensial per-provider di `.env` (`VLLM_LLM_ENDPOINT`/`VLLM_LLM_API_KEY` vs `DEEPSEEK_BASE_URL`/`DEEPSEEK_API_KEY`); `Settings.active_openai_endpoint()` resolve sesuai `MODEL_PROVIDER`. Ganti provider = edit `MODEL_PROVIDER` + `LLM_MODEL` saja. Live-tested: plain chat + structured routing hijau. Detail: `docs/MODELS.md` |
| D22 | DeepSeek thinking **enabled** balikin `reasoning_content` yang wajib di-round-trip pada tool-call turn (kalau tidak → 400). react workers (langchain-openai) belum round-trip → `LLM_DISABLE_THINKING=true` wajib untuk `deepseek`. KV cache DeepSeek otomatis (no config); prefix completion butuh endpoint `/beta` (belum dipakai) |
| D23 | **Context isolation via explicit state** (`_context.py`). Context bukan lagi satu prompt persona monolitik untuk semua node. `KlaudiaState` bawa field terstruktur: `sheets_context`, `files_context`, `date_context`, `pending_worker`. Tiap layer compose prompt sendiri yg paling kecil: top supervisor + final-reply = full persona (pegang voice + passthrough in-voice); team classifier = routing rules + sheet list; worker (read/sheet/write) = **voice card** (~7 baris, ganti ~200 baris persona) + sheet list + date; sql_agent = voice card + file list + session id. Orchestrator populate field via `process/stream_conversation`. Untung: hemat token, fokus, KV-cache prefix stabil |
| D24 | **sheet_agent = STRUCTURE ONLY**. `get_sheet_tools` buang `tool_batch_update` (tool low-level yg bisa nulis cell values) → sheet_agent cuma create/rename/copy/delete tab lalu STOP + `[SHEET_DONE]`. Dulu DeepSeek pakai batch_update buat nulis header+data (overstep write_agent → parked write_agent jadi no-op redundant ~13s). Sekarang: sheet_agent bikin tab kosong, write_agent baca sibling (get_multiple_sheet_data) buat template lalu isi header+data |
| D25 | **Prompt per-agent (separation of concerns)**: `_CLARIFY_RULE` dipecah `_CLARIFY_READ`/`_CLARIFY_SHEET`/`_CLARIFY_WRITE` (read_agent nggak lagi bawa case write-only). write_agent FINANCIAL RULES jadi **schema-driven** (baca header asli, jangan asumsi sales/purchases/summary; sheet baru kosong → mirror header sibling). sheet_agent dapat naming-convention (Jul bukan Juli/July). SHEET-EXISTENCE rule: explicit create+write → create-then-write; write ke sheet hilang tanpa minta buat → [CLARIFY] (jaga HITL T16) |