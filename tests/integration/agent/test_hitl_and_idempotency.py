"""Tests for the data_entry_team idempotency + smart HITL behavior.

Background — 2 bugs found in v4.2:
1. write_agent appended 2 rows for a single user request (looping team supervisor).
2. Klaudia produced a confirmation-request ("apakah benar?") AFTER the action
   already ran, instead of a confirmation-of-result.

Fix v5 introduced:
- Workers tag their final reply with [WRITE_DONE] / [READ_DONE] / [SHEET_DONE] / [CLARIFY].
- Team supervisor finishes deterministically when it sees the marker — no second LLM
  call, no double dispatch.
- Worker prompts: pre-flight resolve sheet alias, only [CLARIFY] when truly blocked.

These tests pin those guarantees.
"""

import os
import time
import uuid
from typing import Any

import pytest
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END
from mcp import ClientSession
from mcp.client.sse import sse_client
import json

from config.settings import Settings
from klaudia.core.supervisor.agents.data_entry_team.agents import (
    COMPLETION_MARKERS,
    MEMBERS,
    NON_TERMINAL_MARKERS,
    TERMINAL_MARKERS,
    WORK_DONE_MARKERS,
    _ground_marker_against_tool_calls,
    _has_completion_marker,
    _is_terminal_marker,
    _normalize_route,
    make_data_entry_team,
)
from langchain_core.messages import AIMessage, ToolMessage
from klaudia.interfaces.tool_registry import MCPToolRegistry


SHEET_ID = "1sYmDi2o55tZktSbgy60rIwZa-3gPqH_b5U7iN4jTCIo"
SSE_GSHEETS = "http://localhost:8002/sse"
AGENT_TEST_MODEL = os.environ.get("AGENT_TEST_MODEL", "gemini-3-flash-preview")


# --------------------------------------------------------------------------- #
# Pure unit tests — no external deps.
# --------------------------------------------------------------------------- #


@pytest.mark.unit
def test_has_completion_marker_detects_all_known_markers():
    for marker in COMPLETION_MARKERS:
        assert _has_completion_marker(f"some text\n{marker} ok")
    assert not _has_completion_marker("Successfully appended one row.")
    assert not _has_completion_marker("")


@pytest.mark.unit
def test_terminal_vs_non_terminal_markers_partition():
    """Contract: TERMINAL ends the turn, NON_TERMINAL falls through to the LLM router."""
    assert set(TERMINAL_MARKERS) == {"[WRITE_DONE]", "[SHEET_DONE]", "[CLARIFY]"}
    assert set(NON_TERMINAL_MARKERS) == {"[READ_DONE]"}
    # Sanity: COMPLETION_MARKERS is the union; no overlap.
    assert set(COMPLETION_MARKERS) == set(TERMINAL_MARKERS) | set(NON_TERMINAL_MARKERS)
    assert not (set(TERMINAL_MARKERS) & set(NON_TERMINAL_MARKERS))


@pytest.mark.unit
def test_is_terminal_marker_only_fires_on_terminals():
    for m in TERMINAL_MARKERS:
        assert _is_terminal_marker(f"... {m} done")
    for m in NON_TERMINAL_MARKERS:
        assert not _is_terminal_marker(f"... {m} read finished")
    assert not _is_terminal_marker("plain text")
    assert not _is_terminal_marker("")


@pytest.mark.unit
def test_ground_marker_rewrites_done_without_tool_calls_to_clarify():
    """If a worker emits [WRITE_DONE] / [READ_DONE] / [SHEET_DONE] without
    actually calling any tool, we treat it as hallucination and rewrite to
    [CLARIFY] before the gate sees it.
    """
    for marker in WORK_DONE_MARKERS:
        msgs = [AIMessage(content=f"Saya akan rapikan. Mohon tunggu sebentar. {marker} done.")]
        out = _ground_marker_against_tool_calls("write_agent", msgs, "ulangi ya?")
        assert out.startswith("[CLARIFY]"), f"{marker} without tool calls must be downgraded; got {out!r}"


@pytest.mark.unit
def test_ground_marker_keeps_done_when_tool_actually_called():
    """When the agent really used a tool, the *_DONE marker survives untouched."""
    msgs = [
        AIMessage(content="calling tool"),
        ToolMessage(content='{"ok": true}', tool_call_id="x", name="tool_append_rows"),
        AIMessage(content="Appended one row to Sheet1.\n[WRITE_DONE] nasi padang"),
    ]
    out = _ground_marker_against_tool_calls("write_agent", msgs, "fallback")
    assert "[WRITE_DONE]" in out
    assert not out.startswith("[CLARIFY]")


@pytest.mark.unit
def test_ground_marker_passthrough_on_clarify():
    """A genuine [CLARIFY] from the worker is not a *_DONE marker; do not touch."""
    msgs = [AIMessage(content="[CLARIFY] Sheet 'foo' belum ada. Mau saya buatkan?")]
    out = _ground_marker_against_tool_calls("write_agent", msgs, "fallback")
    assert out.startswith("[CLARIFY] Sheet 'foo'")


@pytest.mark.unit
def test_normalize_route_extracts_member_name():
    assert _normalize_route("write_agent") == "write_agent"
    assert _normalize_route("write_agent.tool_append_rows(...)") == "write_agent"
    assert _normalize_route(" read_agent ") == "read_agent"


@pytest.mark.unit
def test_normalize_route_finish_and_unknown_default():
    assert _normalize_route("FINISH") == "FINISH"
    assert _normalize_route("done") == "FINISH"
    assert _normalize_route("garbage_value") == "FINISH"


@pytest.mark.unit
def test_members_contract_unchanged():
    assert set(MEMBERS) == {"read_agent", "sheet_agent", "write_agent"}


# --------------------------------------------------------------------------- #
# Deterministic team-supervisor gate — verifies the loop fix without an LLM
# round-trip. We pass a state whose latest message already carries a marker;
# the gate must short-circuit to END before invoking the router LLM.
# --------------------------------------------------------------------------- #


from langchain_core.runnables import Runnable


class _NeverCallLLM(Runnable):
    """Sentinel that explodes if the supervisor tries to actually invoke the LLM.

    The deterministic gate is supposed to short-circuit before any LLM call on
    a terminal-marker-bearing state. If the gate is broken, this fixture will
    fail loudly instead of silently passing. Inherits from Runnable so
    LangGraph's create_react_agent accepts it at graph construction time.
    """

    def invoke(self, *_a, **_k):
        raise AssertionError("team_supervisor invoked the LLM despite a terminal marker")

    def with_structured_output(self, *_a, **_k):
        raise AssertionError("team_supervisor invoked the LLM despite a terminal marker")

    def bind_tools(self, *_a, **_k):
        # create_react_agent calls bind_tools at construction. Return self so the
        # subgraph can be built; we just don't expect it to *run* the agent here.
        return self


@pytest.mark.unit
def test_team_supervisor_deterministic_finish_on_write_done():
    """Marker [WRITE_DONE] from write_agent ⇒ END, no LLM call, no second dispatch."""
    fake_llm = _NeverCallLLM()
    fake_registry = type("R", (), {"tools": []})()  # no tools needed for gate test

    graph = make_data_entry_team(fake_llm, fake_registry)

    # Build a state that mimics "write_agent just finished".
    state = {
        "messages": [
            HumanMessage(content="tambahkan nasi goreng 25000 ke sheet pertama"),
            HumanMessage(
                content="Appended one row to Sheet1.\n[WRITE_DONE] nasi goreng 25000 → Sheet1",
                name="write_agent",
            ),
        ]
    }

    # Drive the supervisor node directly by stepping the compiled graph from
    # START — it will route through team_supervisor first.
    # We rely on the compiled subgraph: the entry edge is START → supervisor.
    result = graph.invoke(state)
    assert result.get("next") == "FINISH"


class _RouterCountingLLM(Runnable):
    """LLM stub whose only purpose is to verify the supervisor reached the
    LLM-router branch (i.e., the deterministic gate did NOT short-circuit).

    Returns a stub structured-output runnable that always replies FINISH.
    Inherits from Runnable so create_react_agent accepts it at construction.
    """

    def __init__(self):
        self.structured_calls = 0

    def invoke(self, *_a, **_k):
        # Not expected to be called by team_supervisor (it uses with_structured_output),
        # but create_react_agent's worker invocations also wouldn't hit this in our
        # tests because we never actually drive the worker nodes — the gate or the
        # router routes us straight to END.
        return None

    def with_structured_output(self, *_a, **_k):
        self.structured_calls += 1

        class _Stub:
            def invoke(self, *_a2, **_k2):
                return {"next": "FINISH"}

        return _Stub()

    def bind_tools(self, *_a, **_k):
        return self


@pytest.mark.unit
def test_team_supervisor_does_not_finish_on_read_done():
    """[READ_DONE] is non-terminal: the gate must fall through to the LLM router
    so a compound 'read-then-write' request can still continue.
    """
    fake_llm = _RouterCountingLLM()
    fake_registry = type("R", (), {"tools": []})()
    graph = make_data_entry_team(fake_llm, fake_registry)

    state = {
        "messages": [
            HumanMessage(content="rapikan sheet testing, hapus duplikat, tambah header"),
            HumanMessage(
                content="Sheet has 10 rows.\n[READ_DONE] read 10 rows from testing",
                name="read_agent",
            ),
        ]
    }

    result = graph.invoke(state)
    # Router was called at least once (proving fall-through), then it routed FINISH.
    assert fake_llm.structured_calls >= 1, (
        "deterministic gate must NOT short-circuit on [READ_DONE]; "
        "the LLM router needs the chance to send the next worker"
    )
    # Either "FINISH" (gate path) or END sentinel (LLM-path) both signal the
    # team graph terminated after fall-through. We don't constrain the exact
    # token here — the load-bearing claim is structured_calls >= 1.
    assert result.get("next") in ("FINISH", END)


@pytest.mark.unit
def test_team_supervisor_deterministic_finish_on_clarify():
    """[CLARIFY] also short-circuits to FINISH so Klaudia can relay the question."""
    fake_llm = _NeverCallLLM()
    fake_registry = type("R", (), {"tools": []})()
    graph = make_data_entry_team(fake_llm, fake_registry)

    state = {
        "messages": [
            HumanMessage(content="tambahkan a ke sheet 'tidak_ada'"),
            HumanMessage(
                content="[CLARIFY] Sheet 'tidak_ada' belum ada. Mau saya buatkan?",
                name="write_agent",
            ),
        ]
    }

    result = graph.invoke(state)
    assert result.get("next") == "FINISH"


# --------------------------------------------------------------------------- #
# Integration tests — full subgraph + live LLM + live MCP.
# Skipped unless LLM_API_KEY and the mcp-gsheets SSE server are reachable.
# --------------------------------------------------------------------------- #

_settings = Settings()
_skip_live = pytest.mark.skipif(
    not _settings.llm_api_key,
    reason="LLM_API_KEY not set — live integration tests skipped",
)


async def _sheet_call(name: str, args: dict[str, Any]):
    async with sse_client(SSE_GSHEETS) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool(name, args)
            assert not res.isError, f"{name}: {res.content}"
            if not res.content:
                return {}
            if len(res.content) == 1:
                return json.loads(res.content[0].text)
            return [json.loads(c.text) for c in res.content]


@pytest.fixture
async def registry():
    reg = MCPToolRegistry("mcp-gsheets", SSE_GSHEETS)
    await reg.connect()
    try:
        yield reg
    finally:
        await reg.disconnect()


@pytest.fixture
def llm():
    return ChatGoogleGenerativeAI(
        model=AGENT_TEST_MODEL,
        google_api_key=_settings.llm_api_key,
        temperature=0.0,
    )


@pytest.fixture
async def temp_sheet():
    title = f"hitl_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    await _sheet_call("tool_create_sheet", {"spreadsheet_id": SHEET_ID, "title": title})
    yield title
    try:
        await _sheet_call("tool_delete_sheet", {"spreadsheet_id": SHEET_ID, "sheet": title})
    except AssertionError:
        pass


def _count_tool_calls(messages: list, tool_name: str) -> int:
    """Count ToolMessage entries whose name == tool_name."""
    return sum(1 for m in messages if getattr(m, "name", None) == tool_name)


def _final_text(messages: list) -> str:
    last = messages[-1]
    return last.content if isinstance(last.content, str) else str(last.content)


@_skip_live
@pytest.mark.asyncio
async def test_clear_append_executes_exactly_once(registry, llm, temp_sheet):
    """Bug regression: a clear write request must result in EXACTLY ONE append."""
    graph = make_data_entry_team(llm, registry)

    task = (
        f"Tambahkan satu baris ke sheet '{temp_sheet}': "
        "['INDOMARET', 'Indomie', '15540']. Jangan diulang."
    )
    result = await graph.ainvoke({"messages": [HumanMessage(content=task)]})

    n_appends = _count_tool_calls(result["messages"], "tool_append_rows")
    assert n_appends == 1, f"expected exactly 1 append, got {n_appends}"

    final = _final_text(result["messages"])
    assert "[WRITE_DONE]" in final, f"missing [WRITE_DONE] marker in final reply: {final!r}"

    # Sheet state must reflect exactly one appended row in A1:C1.
    got = await _sheet_call(
        "tool_get_sheet_data",
        {"spreadsheet_id": SHEET_ID, "sheet": temp_sheet, "range": "A1:C2"},
    )
    values = got.get("values", [])
    assert values == [["INDOMARET", "Indomie", "15540"]], f"unexpected sheet state: {values}"


@_skip_live
@pytest.mark.asyncio
async def test_compound_clear_and_replace_with_header(registry, llm, temp_sheet):
    """Bug #4 regression: a compound 'rapikan + hapus duplikat + tambah header'
    request must compose primitives (clear_range + update_cells) within a single
    team turn, NOT refuse with [CLARIFY].
    """
    # Arrange: seed 10 identical rows so dedup is trivially well-defined.
    seed_row = ["INDOMARET", "Indomie", "15540"]
    seed_values = [seed_row for _ in range(10)]
    await _sheet_call(
        "tool_update_cells",
        {
            "spreadsheet_id": SHEET_ID,
            "sheet": temp_sheet,
            "range": "A1",
            "data": seed_values,
        },
    )

    graph = make_data_entry_team(llm, registry)

    task = (
        f"Di sheet '{temp_sheet}', rapikan: hapus baris duplikat, simpan satu saja. "
        "Tambahkan juga header kolom: merchant, items, price."
    )

    # Act
    result = await graph.ainvoke({"messages": [HumanMessage(content=task)]})

    # Assert — final marker is terminal write completion, not refusal.
    final = _final_text(result["messages"])
    assert "[WRITE_DONE]" in final, (
        f"expected compound op to finish with [WRITE_DONE], got: {final!r}"
    )
    assert "[CLARIFY]" not in final, (
        f"worker must not refuse a clearly-defined compound op; got: {final!r}"
    )

    # Primitive-chaining: at least one clear and one write happened.
    n_clear = _count_tool_calls(result["messages"], "tool_clear_range")
    n_update = _count_tool_calls(result["messages"], "tool_update_cells")
    assert n_clear >= 1, f"expected ≥1 tool_clear_range call, got {n_clear}"
    assert n_update >= 1, f"expected ≥1 tool_update_cells call, got {n_update}"

    # End-state: header row + exactly one data row.
    got = await _sheet_call(
        "tool_get_sheet_data",
        {"spreadsheet_id": SHEET_ID, "sheet": temp_sheet, "range": "A1:C3"},
    )
    values = got.get("values", [])
    assert values == [
        ["merchant", "items", "price"],
        ["INDOMARET", "Indomie", "15540"],
    ], f"unexpected sheet state after compound op: {values}"


@_skip_live
@pytest.mark.asyncio
async def test_nonexistent_sheet_triggers_clarify_no_write(registry, llm):
    """Smart HITL: write to a sheet that doesn't exist → [CLARIFY], NO append."""
    graph = make_data_entry_team(llm, registry)

    bogus = f"definitely_not_a_sheet_{uuid.uuid4().hex[:6]}"
    task = (
        f"Tambahkan baris ['nasi goreng', '25000'] ke sheet '{bogus}'. "
        f"Sheet '{bogus}' belum ada di spreadsheet."
    )
    result = await graph.ainvoke({"messages": [HumanMessage(content=task)]})

    final = _final_text(result["messages"])
    assert "[CLARIFY]" in final, (
        f"expected [CLARIFY] when target sheet missing, got: {final!r}"
    )

    n_appends = _count_tool_calls(result["messages"], "tool_append_rows")
    assert n_appends == 0, f"must not write to a missing sheet, but got {n_appends} append(s)"
