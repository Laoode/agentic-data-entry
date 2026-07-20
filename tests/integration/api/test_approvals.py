"""ApprovalService: park, list, approve (replay), reject, ownership.

Runs against a temp SQLite database via the app's own DB client, so the
portable SQL is exercised on the dev backend too.
"""

import pytest

from app.services.core.approvals import ApprovalNotFoundError, ApprovalService
from app.services.extraction.infra.db_client import AppDBClient
from config.settings import Settings


class FakeTool:
    def __init__(self, name: str) -> None:
        self.name = name
        self.calls: list[dict] = []

    async def coroutine(self, **kwargs):
        self.calls.append(kwargs)
        return '{"cleared": true}'


class FakeRegistry:
    def __init__(self, *tools: FakeTool) -> None:
        self.tools = list(tools)


@pytest.fixture
async def service(tmp_path):
    db = AppDBClient(Settings(SQLITE_DB=str(tmp_path / "approvals.db")))
    await db.connect()
    tool = FakeTool("tool_clear_range")
    svc = ApprovalService(db, FakeRegistry(tool))
    await svc.ensure_schema()
    svc.test_tool = tool  # handle for assertions
    yield svc
    await db.close()


async def _park(service, user_id=1, sheet="Jun"):
    return await service.create(
        user_id=user_id,
        session_id=7,
        spreadsheet_id="ss-abc",
        tool_name="tool_clear_range",
        args={"sheet": sheet, "range": "A1:Z1000"},
        summary=f"Hapus permanen 40 baris di sheet '{sheet}'.",
        rows_affected=40,
        columns_affected=3,
    )


async def test_created_approval_is_listed_and_not_executed(service):
    parked = await _park(service)

    pending = await service.list_pending(1)

    assert [p["approval_id"] for p in pending] == [parked.approval_id]
    assert pending[0]["rows_affected"] == 40
    assert pending[0]["sheet"] == "Jun"
    assert service.test_tool.calls == []  # nothing ran


async def test_approve_replays_stored_call_verbatim(service):
    parked = await _park(service)

    result = await service.approve(1, parked.approval_id)

    assert result["executed"] is True
    assert service.test_tool.calls == [{"sheet": "Jun", "range": "A1:Z1000"}]
    assert await service.list_pending(1) == []


async def test_reject_does_not_execute(service):
    parked = await _park(service)

    result = await service.reject(1, parked.approval_id)

    assert result["executed"] is False
    assert service.test_tool.calls == []
    assert await service.list_pending(1) == []


async def test_double_approve_executes_once(service):
    parked = await _park(service)

    await service.approve(1, parked.approval_id)
    with pytest.raises(ApprovalNotFoundError):
        await service.approve(1, parked.approval_id)

    assert len(service.test_tool.calls) == 1


async def test_foreign_user_cannot_approve_or_see(service):
    parked = await _park(service, user_id=1)

    assert await service.list_pending(2) == []
    with pytest.raises(ApprovalNotFoundError):
        await service.approve(2, parked.approval_id)
    assert service.test_tool.calls == []


async def test_unknown_id_raises(service):
    with pytest.raises(ApprovalNotFoundError):
        await service.approve(1, "does-not-exist")
