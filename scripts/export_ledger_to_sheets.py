"""Mirror the Postgres ledger into the Google Sheet.

The ledger is the source of truth; this pushes every ledger tab to the
configured Google Sheet (SHEET_ID), replacing tab contents. Run manually,
from cron, or as a scheduled job. The reverse of
scripts/migrate_sheets_to_ledger.py.

Usage:
    uv run python scripts/export_ledger_to_sheets.py
    uv run python scripts/export_ledger_to_sheets.py --workspace default
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


def _as_list(result) -> list:
    return [result] if isinstance(result, dict) else result


async def export(workspace: str) -> None:
    """Read all ledger tabs, then replace the Google Sheet tab contents."""
    ledger_transport = _transport("mcp-ledger", {"LEDGER_WORKSPACE": workspace})
    async with Client(ledger_transport, mode="auto") as ledger:
        tabs = _as_list(await _call(ledger, "tool_list_sheets", {}))
        print(f"Ledger workspace {workspace!r} has {len(tabs)} tabs")
        grids: list[tuple[str, list[list]]] = []
        for tab in tabs:
            data = await _call(ledger, "tool_get_sheet_data", {"sheet": tab["title"]})
            grids.append((tab["title"], data.get("values", [])))

    async with Client(_transport("mcp-gsheets", {}), mode="auto") as gsheets:
        existing = {
            tab["title"]
            for tab in _as_list(await _call(gsheets, "tool_list_sheets", {}))
        }
        for title, values in grids:
            if title not in existing:
                await _call(gsheets, "tool_create_sheet", {"title": title})
            else:
                # Replace content: clear generously, then write.
                await _call(
                    gsheets,
                    "tool_clear_range",
                    {"sheet": title, "range": "A1:Z1000"},
                )
            if values:
                await _call(
                    gsheets,
                    "tool_update_cells",
                    {"sheet": title, "range": "A1", "data": values},
                )
            print(f"  mirrored {title!r}: {len(values)} rows")

    print(f"Done: {len(grids)} tabs mirrored to Google Sheets")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ledger -> Google Sheets mirror")
    parser.add_argument(
        "--workspace", default=os.environ.get("LEDGER_WORKSPACE", "default")
    )
    args = parser.parse_args()
    asyncio.run(export(args.workspace))
