"""Copy every tab of the Google Sheet into the Postgres ledger.

One-shot migration/import: reads all tabs via mcp-gsheets and writes them
into an mcp-ledger workspace, preserving tab order and cell values. Safe to
re-run; existing ledger tabs with the same title are replaced.

Usage:
    uv run python scripts/migrate_sheets_to_ledger.py
    uv run python scripts/migrate_sheets_to_ledger.py --workspace default

Requires: .env with gsheets credentials (SHEET_ID et al in mcp-gsheets/.env)
and DATABASE_URL for the ledger.
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _transport(server_dir: str, extra_env: dict[str, str]) -> StdioTransport:
    return StdioTransport(
        command=sys.executable,
        args=["main.py", "--transport", "stdio"],
        cwd=str(_PROJECT_ROOT / server_dir),
        env={**os.environ, **extra_env},
    )


async def _call(client: Client, tool: str, args: dict):
    result = await client.call_tool(tool, args, raise_on_error=False)
    texts = [c.text for c in result.content if getattr(c, "text", None)]
    if result.is_error:
        raise RuntimeError(f"{tool} failed: {' '.join(texts)[:300]}")
    if not texts:
        return []
    if len(texts) > 1:
        return [json.loads(t) for t in texts]
    return json.loads(texts[0])


async def migrate(workspace: str) -> None:
    """Read all tabs from gsheets, write them into the ledger workspace."""
    async with Client(_transport("mcp-gsheets", {}), mode="auto") as gsheets:
        tabs = await _call(gsheets, "tool_list_sheets", {})
        if isinstance(tabs, dict):
            tabs = [tabs]
        print(f"Source spreadsheet has {len(tabs)} tabs")

        grids: list[tuple[str, list[list]]] = []
        for tab in tabs:
            title = tab["title"]
            data = await _call(gsheets, "tool_get_sheet_data", {"sheet": title})
            values = data.get("values", [])
            grids.append((title, values))
            print(f"  read {title!r}: {len(values)} rows")

    ledger_env = {"LEDGER_WORKSPACE": workspace}
    async with Client(_transport("mcp-ledger", ledger_env), mode="auto") as ledger:
        existing = await _call(ledger, "tool_list_sheets", {})
        if isinstance(existing, dict):
            existing = [existing]
        existing_titles = {tab["title"] for tab in existing}

        for title, values in grids:
            if title in existing_titles:
                await _call(ledger, "tool_delete_sheet", {"sheet": title})
            await _call(ledger, "tool_create_sheet", {"title": title})
            if values:
                await _call(
                    ledger,
                    "tool_update_cells",
                    {"sheet": title, "range": "A1", "data": values},
                )
            print(f"  wrote {title!r}: {len(values)} rows")

    print(f"Done: {len(grids)} tabs migrated into workspace {workspace!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Sheets -> ledger migration")
    parser.add_argument(
        "--workspace", default=os.environ.get("LEDGER_WORKSPACE", "default")
    )
    args = parser.parse_args()
    asyncio.run(migrate(args.workspace))
