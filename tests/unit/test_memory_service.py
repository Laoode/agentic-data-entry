"""MemoryService unit tests against a fake mem0 backend (hermetic, no DB/mem0).

Covers the wrapper logic: user-id scoping, result formatting, fail-soft recall,
message/metadata shaping on write, and cascade purge by spreadsheet/sheet.
"""

from app.services.core.memory import MemoryService


class FakeBackend:
    """Records calls; returns canned results. Mirrors the mem0 surface used."""

    def __init__(self, search_results=None, all_results=None):
        self._search = search_results or []
        self._all = all_results or []
        self.added: list[dict] = []
        self.deleted: list[str] = []
        self.reset_called = False
        self.raise_on_search = False
        self.last_search: dict | None = None

    async def add(self, messages, *, user_id=None, metadata=None, infer=True):
        self.added.append(
            {"messages": messages, "user_id": user_id, "metadata": metadata}
        )
        return {"results": []}

    async def search(self, query, *, filters=None, top_k=20):
        self.last_search = {"query": query, "filters": filters, "top_k": top_k}
        if self.raise_on_search:
            raise RuntimeError("embed service down")
        return {"results": self._search}

    async def get_all(self, *, filters=None, top_k=20):
        return {"results": self._all}

    async def delete(self, memory_id):
        self.deleted.append(memory_id)

    async def reset(self):
        self.reset_called = True


async def test_recall_formats_results_as_bullets():
    backend = FakeBackend(
        search_results=[
            {"memory": "User categorizes GoFood as Transport"},
            {"memory": "Fiscal month starts on the 25th"},
        ]
    )
    ctx = await MemoryService(backend, top_k=6).recall(7, "category for gofood")
    assert "GoFood" in ctx and "Transport" in ctx
    assert ctx.startswith("- ")


async def test_recall_scopes_by_user_id_string_and_top_k():
    backend = FakeBackend(search_results=[{"memory": "m"}])
    await MemoryService(backend, top_k=6).recall(7, "q")
    assert backend.last_search["filters"] == {"user_id": "7"}
    assert backend.last_search["top_k"] == 6


async def test_recall_empty_returns_blank():
    assert await MemoryService(FakeBackend(search_results=[])).recall(7, "x") == ""


async def test_recall_is_failsoft_on_backend_error():
    backend = FakeBackend()
    backend.raise_on_search = True
    assert await MemoryService(backend).recall(7, "x") == ""


async def test_recall_blank_query_skips_backend():
    backend = FakeBackend(search_results=[{"memory": "m"}])
    assert await MemoryService(backend).recall(7, "") == ""
    assert backend.last_search is None


async def test_remember_shapes_messages_metadata_and_userid():
    backend = FakeBackend()
    await MemoryService(backend).remember(7, "ss-123", "hi", "hello")
    add = backend.added[0]
    assert add["user_id"] == "7"
    assert add["metadata"] == {"spreadsheet_id": "ss-123"}
    assert [m["role"] for m in add["messages"]] == ["user", "assistant"]


async def test_remember_without_spreadsheet_has_no_metadata():
    backend = FakeBackend()
    await MemoryService(backend).remember(7, None, "hi", "hello")
    assert backend.added[0]["metadata"] is None


async def test_purge_spreadsheet_deletes_only_matching_metadata():
    backend = FakeBackend(
        all_results=[
            {"id": "a", "memory": "x", "metadata": {"spreadsheet_id": "S1"}},
            {"id": "b", "memory": "y", "metadata": {"spreadsheet_id": "S2"}},
            {"id": "c", "memory": "z", "metadata": {}},
        ]
    )
    deleted = await MemoryService(backend).purge_spreadsheet(7, "S1")
    assert deleted == 1
    assert backend.deleted == ["a"]


async def test_purge_sheet_matches_metadata_or_text_within_spreadsheet():
    backend = FakeBackend(
        all_results=[
            {
                "id": "a",
                "memory": "note about Jun sheet",
                "metadata": {"spreadsheet_id": "S1"},
            },
            {
                "id": "b",
                "memory": "unrelated",
                "metadata": {"spreadsheet_id": "S1", "sheet": "Jun"},
            },
            {"id": "c", "memory": "about Jun", "metadata": {"spreadsheet_id": "S2"}},
        ]
    )
    deleted = await MemoryService(backend).purge_sheet(7, "S1", "Jun")
    assert set(backend.deleted) == {"a", "b"}
    assert deleted == 2


async def test_reset_delegates_to_backend():
    backend = FakeBackend()
    await MemoryService(backend).reset()
    assert backend.reset_called
