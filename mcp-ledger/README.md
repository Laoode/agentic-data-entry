# mcp-ledger

MCP server exposing the Google Sheets tool surface (16 tools, identical
names, parameters, and response shapes to `mcp-gsheets`) backed by Postgres.

Drop-in replacement for the data-entry agents: prompts and the e2e dataset
run unchanged, with no Sheets API quotas and full transactionality.

## Configuration

| Env | Meaning |
|-----|---------|
| `DATABASE_URL` | Postgres DSN (required) |
| `LEDGER_WORKSPACE` | Default workspace when `spreadsheet_id` is omitted (default `default`) |
| `LEDGER_TITLE` | Workspace display title (default `Klaudia Ledger`) |
| `FASTMCP_HOST` / `FASTMCP_PORT` | SSE transport bind (default `0.0.0.0:8003`) |

## Run

```bash
python main.py --transport stdio   # production transport (default)
python main.py --transport sse     # standalone service
```

## Storage

One row per sheet tab (`ledger_sheet`), the cell grid as a single JSONB 2D
array. Mutations are read-modify-write under `FOR UPDATE` row locking —
simple and transactional at receipt scale (hundreds of rows per tab).
