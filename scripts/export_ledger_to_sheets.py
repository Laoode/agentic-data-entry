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
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _params(server_dir: str, extra_env: dict[str, str]) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["main.py", "--transport", "stdio"],
        cwd=str(_PROJECT_ROOT / server_dir),
        env={**os.environ, **extra_env},
    )


async def _call(session: ClientSession, tool: str, args: dict):
    result = await session.call_tool(tool, args)
    texts = [c.text for c in result.content if getattr(c, "text", None)]
    if result.isError:
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
    async with stdio_client(_params("mcp-ledger", {"LEDGER_WORKSPACE": workspace})) as (
        l_read,
        l_write,
    ):
        async with ClientSession(l_read, l_write) as ledger:
            await ledger.initialize()
            tabs = _as_list(await _call(ledger, "tool_list_sheets", {}))
            print(f"Ledger workspace {workspace!r} has {len(tabs)} tabs")
            grids: list[tuple[str, list[list]]] = []
            for tab in tabs:
                data = await _call(
                    ledger, "tool_get_sheet_data", {"sheet": tab["title"]}
                )
                grids.append((tab["title"], data.get("values", [])))

    async with stdio_client(_params("mcp-gsheets", {})) as (g_read, g_write):
        async with ClientSession(g_read, g_write) as gsheets:
            await gsheets.initialize()
            existing = {
                t["title"]
                for t in _as_list(await _call(gsheets, "tool_list_sheets", {}))
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
