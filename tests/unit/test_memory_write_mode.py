"""Hermetic tests for the orchestrator's memory write-mode branching.

Covers MEMORY_WRITE_MODE=inline vs taskiq without real mem0, Taskiq, or infra:
inline runs mem0.remember in a background task; taskiq enqueues the task instead;
both are drainable and never block; both are gated by MEMORY_MODE=write. Also
covers MemoryService.remember strict re-raise (used by the Taskiq worker).
"""

import sys
import types

import pytest

from app.services.core.memory import MemoryService
from app.services.core.orchestrator import KlaudiaOrchestrator


class _Settings:
    def __init__(self, memory_mode="write", memory_write_mode="inline"):
        self.memory_mode = memory_mode
        self.memory_write_mode = memory_write_mode


class _RecordingMemory:
    def __init__(self):
        self.remembered: list = []

    async def remember(self, user_id, spreadsheet_id, user_text, assistant_text):
        self.remembered.append((user_id, spreadsheet_id, user_text, assistant_text))


class _Container:
    def __init__(self, memory=None, settings=None):
        self.memory = memory
        self.settings = settings or _Settings()
        self.extraction_agent = None
        self.langfuse = None


def _orch(memory=None, settings=None):
    return KlaudiaOrchestrator(_Container(memory=memory, settings=settings))


async def test_inline_mode_calls_remember_in_background():
    mem = _RecordingMemory()
    orch = _orch(memory=mem, settings=_Settings(memory_write_mode="inline"))
    orch._remember(7, "S1", "hi", "hello")
    await orch.drain_background()
    assert mem.remembered == [(7, "S1", "hi", "hello")]


async def test_disabled_when_mode_not_write():
    mem = _RecordingMemory()
    orch = _orch(memory=mem, settings=_Settings(memory_mode="read"))
    orch._remember(7, "S1", "hi", "hello")
    await orch.drain_background()
    assert mem.remembered == []


async def test_noop_when_memory_absent():
    orch = _orch(memory=None)
    orch._remember(7, "S1", "hi", "hello")  # must not raise
    await orch.drain_background()


async def test_taskiq_mode_enqueues_and_does_not_call_remember(monkeypatch):
    mem = _RecordingMemory()
    calls: list = []

    class _FakeTask:
        async def kiq(self, **kwargs):
            calls.append(kwargs)

    fake_module = types.ModuleType("app.services.core.memory_tasks")
    fake_module.persist_memory_task = _FakeTask()
    monkeypatch.setitem(sys.modules, "app.services.core.memory_tasks", fake_module)

    orch = _orch(memory=mem, settings=_Settings(memory_write_mode="taskiq"))
    orch._remember(7, "S1", "hi", "hello")
    await orch.drain_background()

    assert mem.remembered == []  # inline path not taken
    assert calls == [
        {
            "user_id": 7,
            "spreadsheet_id": "S1",
            "user_text": "hi",
            "assistant_text": "hello",
        }
    ]


async def test_taskiq_enqueue_failure_is_failsoft(monkeypatch):
    class _BrokenTask:
        async def kiq(self, **kwargs):
            raise RuntimeError("redis down")

    fake_module = types.ModuleType("app.services.core.memory_tasks")
    fake_module.persist_memory_task = _BrokenTask()
    monkeypatch.setitem(sys.modules, "app.services.core.memory_tasks", fake_module)

    orch = _orch(
        memory=_RecordingMemory(), settings=_Settings(memory_write_mode="taskiq")
    )
    orch._remember(7, None, "hi", "hello")
    await orch.drain_background()  # must not raise


class _RaisingBackend:
    async def add(self, *a, **k):
        raise RuntimeError("boom")


async def test_remember_strict_reraises_for_worker_retry():
    svc = MemoryService(_RaisingBackend())
    # inline default swallows
    await svc.remember(7, None, "u", "a")
    # strict re-raises so Taskiq can retry
    with pytest.raises(RuntimeError):
        await svc.remember(7, None, "u", "a", strict=True)
