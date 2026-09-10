# mcp-ledger

Postgres-backed MCP server with the 16 Google Sheets-compatible tools plus
snapshot reads, revision-checked appends and labelled aggregation.

Drop-in replacement for the data-entry agents: prompts and the e2e dataset
retain their existing tools, with no Sheets API quotas. Individual grid mutations
are transactional; a sequence of legacy tool calls is not one transaction.

## Configuration

| Env | Meaning |
|-----|---------|
| `DATABASE_URL` | Postgres DSN (required) |
| `LEDGER_WORKSPACE` | Default workspace when `spreadsheet_id` is omitted (default `default`) |
| `LEDGER_TITLE` | Workspace display title (default `Klaudia Ledger`) |
| `FASTMCP_HOST` / `FASTMCP_PORT` | HTTP or legacy SSE bind (default `0.0.0.0:8003`) |
| `MCP_JWT_SECRET` | HS256 verification key for HTTP bearer auth (32+ characters) |
| `MCP_JWT_ISSUER` / `MCP_JWT_AUDIENCE` | Optional JWT claim checks |
| `MCP_ALLOW_INSECURE_HTTP` | Local-only override for an unauthenticated HTTP smoke test |

## Run

```bash
python main.py --transport stdio   # local subprocess (default)
python main.py --transport http    # stateless service at /mcp; auth required
python main.py --transport sse     # legacy rollback only
```

FastMCP is pinned to `4.0.0b3`. HTTP starts in stateless mode so requests can
reach any replica. Put TLS and rate limits at the gateway. For an external
endpoint, replace the shared HS256 verifier with an asymmetric key and JWKS.

## Storage

One row per sheet tab (`ledger_sheet`), the cell grid as a single JSONB 2D
array. Grid mutations use `FOR UPDATE` row locking. A database trigger increments
the sheet revision on every update, including direct SQL edits. Snapshot reads
still load the full grid from storage before returning the requested range.

## Checked appends

`tool_get_sheet_snapshot(sheet, range)` returns stable sheet identity, revision
and literal values from one database snapshot. The default range is `A1:Z20`;
explicit ranges must be finite rectangles of at most 2,000 cells.
Snapshot and aggregate responses also have a 65,536-byte JSON budget. Oversized
responses fail with a request to narrow the selection; they are never truncated.

`tool_append_rows_checked(operation)` accepts `sheet_id`, `expected_revision`,
`idempotency_key` and literal `rows`. It appends after the last populated row of
the whole sheet. It does not insert into an embedded table or above a footer.
Requests are limited to 1,000 rows and 256 cells per row. Non-finite numbers,
nested objects and empty rows are rejected. Text remains text, including strings
that resemble formulas; there is no formula evaluation in this backend yet.

The append and its receipt commit in one database transaction. Repeating the
same request with the same key returns the stored receipt without another write.
Reusing a key with changed arguments fails. A stale revision requires a fresh
read and a reassessed operation; a new action needs a new key. Keys are scoped
to a workbook. Receipts include the affected sheet, before/after revisions and
written row/cell counts. They explicitly report formula calculation as
`not_supported` and accounting validation as `not_run`.

The app's scope wrapper supplies the workbook. Stable sheet IDs do not bypass
that boundary. Direct MCP clients are trusted service callers and must provide
an authorised workbook; MCP bearer authentication does not itself implement
per-user resource permissions. The current chat workers retain their legacy
tools until the agent cutover; the new tools are available through MCP.

Operation receipts remain in `ledger_operation` if a sheet or workbook is
deleted. They retain IDs and change counts, not cell payloads. Retention and
user-erasure policy must be applied to this history before production rollout.

## Labelled aggregation

`tool_aggregate_sheet(sheet, query)` computes `sum` and nonblank `count` metrics
over a finite `table_range`. Its first row supplies unique headers. Select the
table itself, excluding nearby tables, subtotals and summary footers. Queries
support exact equality filters and up to three grouping columns. Numeric grouping
treats `1` and `1.0` alike while keeping booleans and text distinct.

The result includes the stable source sheet ID, revision, range, applied query,
matched record count and groups. Each metric retains its column and operation,
with its value encoded as decimal text and explicit nonblank/blank counts.
Empty cells are excluded; invalid selected operands abort the query. Raw records
are not returned. Limits are one million selected cells, eight metrics and up to
100 groups (20 by default). Group overflow fails instead of returning partial totals.

Sums use a fixed 64-digit decimal context and reject inexact arithmetic. Raw
numbers are accepted by default. For text known to use a decimal point without
thousands separators, set `numeric_text: "decimal"`. This is an explicit source
format declaration; the tool does not guess whether `15.000` means fifteen or
fifteen thousand. Currency symbols, comma separators and formulas are rejected.

Declare `unit_column` for currency/unit checks. Every matched row must then have
a nonblank text unit, and units must agree within each group. Filter or group by
currency to keep currencies separate. Without this declaration, unit is
unspecified; this tool makes no accounting-policy or currency-correctness claim.
Catalogue-derived unit declarations and labelled final-response verification are
later integration steps. Computation currently runs over the existing JSONB
snapshot in the ledger process, not a row-level SQL query engine.

## Registered resource catalogue

The catalogue stores multiple non-overlapping table regions per sheet, each with
stable table and column IDs. It requires PostgreSQL's `pg_trgm` extension; the
migration account must be able to install it, or an administrator must install it
before the service starts.

- `tool_register_table(definition)` registers finite bounds whose first row has
  complete, unique text headers. Supply the observed sheet revision, name and
  optional description, grain, aliases, entity and period coverage.
- `tool_update_table(change)` requires the table ID plus expected catalogue and
  source sheet revisions. Metadata and same-sheet bounds can change while IDs
  persist. Changed header names/order require future explicit column remapping.
- `tool_search_resources(query)` searches indexed metadata through exact names,
  aliases, full-text terms and trigrams. Model-provided `concepts` expand intent;
  optional required columns, entity and date act as hard filters. It returns up
  to 20 candidates, reasons, freshness and the first 16 columns per candidate.
- `tool_inspect_resource(table_id, column_offset, column_limit)` reads metadata
  and paginates columns (32 by default, at most 64). It does not load cell records.

Search and inspection share the 65,536-byte read budget. Narrow candidate limits
if metadata exceeds it. Register/update return compact commit confirmations, so
large schemas cannot cause a response-size failure after a successful write.
These metadata writes reject duplicate/stale requests; they do not yet provide
financial-operation idempotency receipts.

Search covers explicitly registered tables only. Descriptions, grain, entity and
period are caller-declared content; headers come from the source sheet. Any sheet
revision change marks old metadata stale. Refresh requires another checked update;
automatic detection, refresh, formula relationships and column remapping remain
pending. Existing legacy tools and chat workers do not consume this catalogue yet.
The trusted application still supplies the bound workbook. This adds no shared
workspace ACL or cross-workbook access.

The application also offers owner-scoped HTTP discovery through
`POST /v1/resources/search` and `GET /v1/resources/{table_id}`. Those routes obtain
the user ID from the verified application JWT and join current workbook ownership
within the catalogue read. They reuse the same search ranking, schema pagination
and byte budget. Direct MCP tools keep their existing trusted-service workbook
scope; they do not accept a model-provided user ID or gain cross-workbook access.
