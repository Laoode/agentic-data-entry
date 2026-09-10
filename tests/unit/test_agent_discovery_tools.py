"""Task-local discovery tools bind identity outside model arguments."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from klaudia.core.agent.context import TaskContext
from klaudia.core.agent.tools import DiscoveryTools
from ledger.resources import ResourceNotFoundError


def descriptor(table_id: str = "tbl_claims", revision: int = 1) -> dict:
    """Return an inspected identity with revision evidence and no cell records."""
    return {
        "table_id": table_id,
        "spreadsheet_id": "wb_other",
        "sheet_id": 8,
        "range": "A1:B20",
        "catalogue_revision": revision,
        "source_revision": revision,
        "current_sheet_revision": revision,
        "freshness": "current",
        "columns": [],
    }


async def test_tools_hide_identity_and_keep_search_out_of_working_set():
    """Model arguments cannot choose authority or populate the task working set."""
    service = AsyncMock()
    service.search.return_value = {"candidates": [descriptor()]}
    session = DiscoveryTools(
        service, TaskContext(user_id=42, active_workbook_id="wb_active")
    )
    tools = {tool.name: tool for tool in session.tools}
    for tool in tools.values():
        assert "user_id" not in tool.args_schema.model_json_schema()["properties"]
        with pytest.raises(ValidationError):
            await tool.ainvoke({"user_id": 99})
    await tools["search_resources"].ainvoke({"intent": "claims"})
    assert service.search.await_args.args[0] == 42
    assert session.working_set == ()
    service.inspect.return_value = descriptor()
    inspected = await tools["inspect_resource"].ainvoke({"table_id": "tbl_claims"})
    assert service.inspect.await_args.args[0] == 42
    assert inspected["working_set_reference"]["spreadsheet_id"] == "wb_other"
    assert session.working_set[0].spreadsheet_id == "wb_other"
    assert session.context.active_workbook_id == "wb_active"


async def test_working_sets_and_identity_are_isolated_between_tasks():
    """Concurrent tasks never inherit another user's selected resource references."""
    service = AsyncMock()
    service.inspect.side_effect = [descriptor("tbl_one"), descriptor("tbl_two")]
    first = DiscoveryTools(service, TaskContext(user_id=1))
    second = DiscoveryTools(service, TaskContext(user_id=2))
    await asyncio.gather(
        first.tools[1].ainvoke({"table_id": "tbl_one"}),
        second.tools[1].ainvoke({"table_id": "tbl_two"}),
    )
    assert [call.args[0] for call in service.inspect.await_args_list] == [1, 2]
    assert first.working_set[0].table_id == "tbl_one"
    assert second.working_set[0].table_id == "tbl_two"


async def test_failed_reinspection_discards_previous_reference():
    """Revoked resources cannot remain in the working set after a failed read."""
    service = AsyncMock()
    session = DiscoveryTools(service, TaskContext(user_id=1))
    service.inspect.return_value = descriptor()
    await session.tools[1].ainvoke({"table_id": "tbl_claims"})
    service.inspect.side_effect = ResourceNotFoundError("Table not found")
    with pytest.raises(ResourceNotFoundError):
        await session.tools[1].ainvoke({"table_id": "tbl_claims"})
    assert session.working_set == ()


async def test_working_set_capacity_and_refresh_are_explicit():
    """A bounded set rejects additions while allowing existing identities to refresh."""
    service = AsyncMock()
    session = DiscoveryTools(service, TaskContext(user_id=1), capacity=1)
    service.inspect.return_value = descriptor()
    await session.tools[1].ainvoke({"table_id": "tbl_claims"})
    service.inspect.return_value = descriptor(revision=2)
    await session.tools[1].ainvoke({"table_id": "tbl_claims"})
    assert session.working_set[0].catalogue_revision == 2
    with pytest.raises(ValueError, match="Working set"):
        await session.tools[1].ainvoke({"table_id": "tbl_second"})
    assert len(session.working_set) == 1


async def test_failed_output_budget_does_not_select_resource():
    """An inspection that cannot return evidence does not mutate task state."""
    service = AsyncMock()
    service.inspect.return_value = {**descriptor(), "description": "x" * 65536}
    session = DiscoveryTools(service, TaskContext(user_id=1))
    with pytest.raises(ValueError, match="Evidence exceeds"):
        await session.tools[1].ainvoke({"table_id": "tbl_claims"})
    assert session.working_set == ()


async def test_concurrent_inspection_obeys_capacity_and_release_frees_slot():
    """Parallel model calls cannot exceed the working-set budget."""
    service = AsyncMock()
    service.inspect.return_value = descriptor("tbl_one")
    session = DiscoveryTools(service, TaskContext(user_id=1), capacity=1)
    outcomes = await asyncio.gather(
        session.tools[1].ainvoke({"table_id": "tbl_one"}),
        session.tools[1].ainvoke({"table_id": "tbl_two"}),
        return_exceptions=True,
    )
    assert sum(isinstance(outcome, ValueError) for outcome in outcomes) == 1
    assert len(session.working_set) == 1
    released = await session.tools[2].ainvoke({"table_id": "tbl_one"})
    assert released == {"table_id": "tbl_one", "released": True}
    service.inspect.return_value = descriptor("tbl_two")
    await session.tools[1].ainvoke({"table_id": "tbl_two"})
    assert session.working_set[0].table_id == "tbl_two"


async def test_direct_coroutine_calls_cannot_override_identity():
    """The boundary validates arguments even when called without LangChain parsing."""
    service = AsyncMock()
    session = DiscoveryTools(service, TaskContext(user_id=42))
    with pytest.raises(ValidationError):
        await session.tools[0].coroutine(intent="claims", user_id=99)
    with pytest.raises(ValidationError):
        await session.tools[1].coroutine(
            table_id="tbl_claims", spreadsheet_id="foreign"
        )
    service.search.assert_not_awaited()
    service.inspect.assert_not_awaited()
