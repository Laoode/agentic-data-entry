# Klaudia Whitebox E2E Suite

End-to-end behavioral testing for the Klaudia agentic pipeline, to run **before
production / before handing off to QA**. It measures what the system actually
does — guardrails, KIE extraction (cache hit/miss), routing to the right agent,
the right tool calls with the right parameters, single/multi turn and single/multi
tool flows, HITL clarification, and latency.

This is a **measurement harness, not a gate**: by default a behavioral miss is
recorded (not failed) so a full run produces a complete results table. Whether
the result is 100% or not, the suite's job is to surface it for the next phase
(fix the dataset, or fix the code).

## Layout

```
tests/e2e/
  dataset/
    SCHEMA.md              # the case/turn/expect schema (read this to add cases)
    cases/*.yaml           # the dataset — 45 cases, 11 categories (source of truth)
    fixtures/              # tiny support files (e.g. unsupported.txt)
  schema.py                # pydantic models for the dataset
  loader.py                # load + validate YAML, resolve attachment paths
  checks.py                # ResponseView + evaluate() — shared scoring
  spy.py                   # in-process MCP tool-call spy (granular assertions)
  report.py                # results table + JSON
  engine_inprocess.py      # run a case via KlaudiaOrchestrator (with spy)
  conftest.py              # pytest fixtures (real container, orchestrator, spy)
  test_e2e_dataset.py      # PYTEST layer (in-process, granular)
  runner_http.py           # HTTP layer (black-box POST /v1/chat, like endpoint_test/)
  gen_postman.py           # generate a Postman collection from the dataset
  outputs/                 # run artifacts (gitignored)
```

## Two layers, one dataset

| | In-process (`test_e2e_dataset.py`) | HTTP (`runner_http.py`) |
|--|--|--|
| Drives | `KlaudiaOrchestrator` directly | real server `POST /v1/chat` |
| Needs server running | no | yes (`./startup.sh`) |
| Granular MCP tool/param checks | **yes** (spy) | skipped (not visible over HTTP) |
| Routing + content + latency | yes | yes |
| Postman | — | `gen_postman.py` |

## Categories (45 cases / 60 turns)

`guardrails` (prompt injection, SARA, NFA, control) · `routing` (data source
disambiguation, FINISH) · `data_entry_read` · `data_entry_write` (mutating) ·
`sheet_ops` (mutating) · `sql_receipt` · `kie_extraction` (cache hit/miss measured
via `cache_hits`/`cache_misses`, multi-image, extract→write) · `hitl` (clarify, no
silent deletion) · `multi_turn` (read→update, anti-anchor, **10-row memory-window
recall**) · `attachment_shape` (pre-OCR rejects) · `tool_not_required` (answer from
injected context, no tool).

## Prerequisites

The live layers make **real** calls (DeepSeek agents, Gemini/Vertex guardrails,
vLLM Qwen KIE, real Google Sheets). Configure `.env` and ensure infra is up:

- LLM creds: `LLM_API_KEY` or Vertex (`GOOGLE_GENAI_USE_VERTEXAI=True` +
  `GOOGLE_CLOUD_PROJECT`) or `DEEPSEEK_API_KEY` (current `.env` uses DeepSeek).
- `SHEET_ID` pointing at the `docs/TABLE.md` spreadsheet.
- For the HTTP layer: `./startup.sh` (FastAPI + MCP servers).
- The in-process layer builds its own container (spawns MCP via stdio), so it
  does **not** need `./startup.sh`.

If creds/`SHEET_ID` are missing, the pytest layer **skips** cleanly.

## Running

```bash
# In-process, full suite (mutating writes self-clean):
uv run pytest tests/e2e/test_e2e_dataset.py -v -s

# Non-destructive subset only:
uv run pytest tests/e2e/test_e2e_dataset.py -v -s -m "not mutating"

# Gate mode — fail the run on any behavioral miss:
E2E_STRICT=1 uv run pytest tests/e2e/test_e2e_dataset.py -v -s

# A single case:
uv run pytest tests/e2e/test_e2e_dataset.py -v -s -k DR01

# HTTP black-box (server must be running); skips mutating by default:
python -m tests.e2e.runner_http
python -m tests.e2e.runner_http --filter guardrails
python -m tests.e2e.runner_http --include-mutating

# Generate Postman collection (safe subset by default):
python -m tests.e2e.gen_postman          # → outputs/klaudia_e2e.postman_collection.json
```

Results: a category table (pass rate + p50/max latency) and a per-turn breakdown
print to stdout; JSON lands in `outputs/results_inprocess.json` / `results_http.json`.
The in-process run also writes a per-model markdown summary to
`outputs/table-<model>.md` (e.g. `table-deepseek-v4-pro.md`, `table-qwen3.6-27b.md`)
— these are kept under version control so model runs can be compared over time.

## Mutating cases & safety

`data_entry_write`, `sheet_ops`, and `KIE03`/`MT01` write to the **real** sheet.
They are additive (a clearly fake `TOKO QA TEST` row, or a dedicated `QA E2E *`
tab) and each reverses itself via `cleanup` in a finally block, so a failed
cleanup leaves only obviously-synthetic residue. Deselect them entirely with
`-m "not mutating"` (pytest) or by omitting `--include-mutating` (HTTP/Postman).

## Notes for maintainers

- Content expectations come from `docs/TABLE.md`. If the live sheet changes,
  update amounts/merchants/items in the read/write cases.
- The granular MCP spy is best-effort: if a langchain/langgraph version invokes
  tools through a path the spy doesn't wrap, `mcp_tools_*` checks degrade to
  "skipped" rather than false-failing.
- `tools_used` is **sub-agent level** by design (see `dataset/SCHEMA.md`).
- The older `tests/integration/agent/test_behavioral.py` and
  `test_agentic_routing.py` predate the current container API
  (`KlaudiaContainer.create()`), so they no longer run as-is; this suite
  supersedes them with a maintainable dataset.
