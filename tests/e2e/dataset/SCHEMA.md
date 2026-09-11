# E2E Dataset Schema

The dataset is the single source of truth for both test layers. Each file in
`cases/*.yaml` is a YAML **list of cases**. Edit YAML to add or change scenarios —
no Python changes needed. The loader validates every case against `schema.py`
(pydantic) at collection time and fails fast with the offending file on error.

## Case

```yaml
- id: DR01-monthly-total        # unique, stable; used as the pytest/Postman id
  category: data_entry_read     # groups rows in the report table
  title: Read a monthly total   # human description
  tags: [read, single_turn]     # free-form labels
  mutating: false               # true → writes to the real sheet (auto-deselectable)
  turns: [ ... ]                # one or more turns, sharing a session
  cleanup:                      # best-effort prompts run after (finally) to reverse writes
    - "Hapus baris terakhir dari sheet Jun."
```

## Turn

```yaml
- user: "Berapa total pembelian bulan Mei?"   # the user message
  attachment: sample-data/receipt/002-receipt.png   # optional, path from repo root
  attachments: [ ... ]          # optional list (for >1 PDF / mixed / >5 image cases)
  note: "why this turn exists"  # optional
  new_session: false            # true → fresh session (empty window); engine drains
                                #        pending background memory writes first
  as_user: 90010                # optional → run this turn as a different user id
                                #        (default: the harness TEST_USER_ID); for
                                #        cross-user memory-isolation cases
  expect: { ... }               # the assertion block
```

## Expect

All fields optional. Empty list / null = "no assertion of this kind".
Unknown case and expectation keys fail validation, so a typo cannot disable a check.

Cases may declare `resource_scope: owned_workbooks` for the optional main-agent
adapter. The default remains `bound_workbook` for historical chat isolation cases.
Adapters reject unsupported contracts before execution and retain failed report rows.

| Field | Layer | Meaning |
|-------|-------|---------|
| `route` | both | `none` (tools_used empty / FINISH), `data_entry_team`, `sql_agent`, or `any` |
| `route_any_of` | both | list of acceptable routes (overrides `route`) |
| `forbid_agents` | both | sub-agents that must NOT appear in `tools_used` |
| `content_any` | both | ≥1 substring present (case-insensitive) |
| `content_all` | both | all substrings present |
| `content_none` | both | none of these substrings present |
| `contains_amount` | both | digit-normalized amounts present (`2.163.500` ≈ `2163500`) |
| `is_rejection` | both | response looks like a guardrail refusal |
| `is_clarification` | both | response asks a clarifying question (and didn't silently write) |
| `mcp_tools_any` | in-process only | ≥1 of these MCP tools was called |
| `mcp_tools_all` | in-process only | all of these MCP tools were called |
| `mcp_tools_none` | in-process only | none of these MCP tools were called |
| `mcp_args_contains` | in-process only | substring present in any tool's JSON args |
| `cache_hits` | in-process only | KIE pages served from cache (from ExtractionAgent result) |
| `cache_misses` | in-process only | KIE pages freshly extracted |
| `latency_ms_max` | both | soft budget; breach is reported (warn), not failed |
| `latency_hard` | both | make `latency_ms_max` a hard failure |
| `capabilities_all` | observed adapters | Require all named capability attempts; this alone does not prove completion |
| `metric_evidence` | native calculation observer | Match table ID, column, operation, group keys and exact signed value |
| `committed_operations_min` | receipt observer | Minimum distinct committed operation IDs; replays count once |
| `ledger_state` | fixture database probe | Exact full snapshot keyed by fixture sheet title, including detection of extra sheets |

Capability names are `read_records`, `discover_resources`, `inspect_resource`,
`calculate`, `append_records` and `search_documents`. A name is not a claim that
every adapter supports it. Missing required observations fail rather than skip.
Native metric and receipt checks do not infer evidence from legacy worker names.
Metric checks grade tool evidence separately from final-response content checks.

For generated cases, construct expectations from fixture truth and registered IDs:

```yaml
expect:
  capabilities_all: [calculate]
  metric_evidence:
    - table_id: tbl_fixture_id
      column: Amount
      operation: sum
      value: "-20"
      group: {}
```

The runner's `observe_state` callback reads the fixture database after the turn.
It never enters the model context. A requested state check without that observer
fails. State-read failures preserve the report row and any observed receipts.

### KIE cache assertions

Cache hit/miss is measured from the `ExtractionAgent` result (per-page
`from_cache`), aggregated over the turn's attachments — **never from latency**.
This mirrors the `extraction_agent.process` output (`cache_hits` / `cache_misses`).
A fresh image (never ingested) ⇒ `cache_misses: 1, cache_hits: 0`; a previously
ingested file ⇒ `cache_hits: 1`. A cache-MISS case is one-shot: after the first
run the file is cached, so re-running reports a hit. These checks are skipped on
the HTTP layer (cache isn't visible in the response).

### Why two layers of assertion

The public `POST /v1/chat` response exposes only **sub-agent names**
(`sql_agent`, `data_entry_team`) in `tools_used` — never the granular MCP tools.
So `mcp_tools_*` / `mcp_args_contains` are evaluated **only** by the in-process
pytest layer, which spies on the MCP registries. Over HTTP those checks are
skipped (not failed). Routing, content, and latency are scored on both layers.

> The orchestrator always calls `tool_list_sheets` itself (in Python) to refresh
> the system-prompt context, so never assert its absence — assert `route: none`
> plus `mcp_tools_none: [tool_get_sheet_data, ...]` for "tool-not-required" cases.

## Sheet source of truth

Content expectations are derived from `docs/TABLE.md` (tabs: `Rangkuman Total,
Jun, Mei, Apr, Mar, Feb, Jan`). If the live `SHEET_ID` layout changes, update the
amounts/merchants/items in the read/write cases accordingly.
