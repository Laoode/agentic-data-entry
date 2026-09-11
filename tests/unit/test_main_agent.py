"""Deterministic model scripts exercise the alternative agent's control flow."""

from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from klaudia.core.agent.agent import MainAgent, RunLimits
from klaudia.core.agent.context import TaskContext


class ScriptedModel:
    """Return predefined responses while recording the exact model context."""

    def __init__(self, responses):
        """Store scripted messages for one isolated test run."""
        self.responses = iter(responses)
        self.inputs = []
        self.tools = []

    def bind_tools(self, tools):
        """Record the available capabilities and return this runnable."""
        self.tools = tools
        return self

    async def ainvoke(self, messages, config=None):
        """Record the model input before returning the next scripted response."""
        self.inputs.append(list(messages))
        return next(self.responses)


def call(name, arguments, identity="call_1"):
    """Build a model tool request using the provider-neutral message contract."""
    return AIMessage(
        content="",
        tool_calls=[
            {"name": name, "args": arguments, "id": identity, "type": "tool_call"}
        ],
    )


async def test_agent_loads_skill_then_discovers_without_changing_identity():
    """Skills load progressively and the task identity never enters tool schemas."""
    service = AsyncMock()
    service.search.return_value = {
        "candidates": [],
        "coverage": "registered_tables_only",
    }
    model = ScriptedModel(
        [
            call("load_skill", {"name": "resource-discovery"}),
            call("search_resources", {"intent": "taxi claims"}, "call_2"),
            AIMessage(content="No registered table matches yet."),
        ]
    )
    answer = await MainAgent(model, service).run(
        "Find my claims table", TaskContext(user_id=42, active_workbook_id="wb_active")
    )
    assert answer.status == "answered"
    assert answer.model_steps == 3
    assert answer.tools_called == ("load_skill", "search_resources")
    assert answer.loaded_skills == {"resource-discovery": "1"}
    assert service.search.await_args.args[0] == 42
    assert "wb_active" not in model.inputs[0][0].content
    assert "Procedure:" not in model.inputs[0][0].content
    assert any(
        isinstance(message, ToolMessage) and "Procedure:" in message.content
        for message in model.inputs[1]
    )


async def test_agent_limits_repeated_tool_calls():
    """Exhaustion cannot look like a completed user request."""
    service = AsyncMock()
    service.search.return_value = {"candidates": []}
    model = ScriptedModel(
        [
            call("search_resources", {"intent": "claims"}),
            call("search_resources", {"intent": "claims"}, "call_2"),
        ]
    )
    answer = await MainAgent(model, service, limits=RunLimits(max_steps=2)).run(
        "Find claims", TaskContext(user_id=1)
    )
    assert answer.status == "step_limit"
    assert service.search.await_count == 2


async def test_agent_handles_unknown_tool_and_invalid_scope_as_tool_errors():
    """The model can repair expected errors without receiving authority."""
    service = AsyncMock()
    model = ScriptedModel(
        [
            call("write_cells", {}),
            call("search_resources", {"intent": "claims", "user_id": 999}, "call_2"),
            AIMessage(content="I cannot change ledger data with these tools."),
        ]
    )
    answer = await MainAgent(model, service).run(
        "Write a claim", TaskContext(user_id=1)
    )
    assert answer.status == "answered"
    service.search.assert_not_awaited()
    assert model.inputs[1][-1].status == "error"
    assert model.inputs[2][-1].status == "error"


async def test_unexpected_service_failure_propagates():
    """Infrastructure failures must not be converted into plausible empty results."""
    service = AsyncMock()
    service.search.side_effect = RuntimeError("database unavailable")
    model = ScriptedModel([call("search_resources", {"intent": "claims"})])
    with pytest.raises(RuntimeError, match="database unavailable"):
        await MainAgent(model, service).run("Find claims", TaskContext(user_id=1))


async def test_context_limit_stops_before_model_call():
    """Oversized user input is rejected without spending a model call."""
    model = ScriptedModel([])
    answer = await MainAgent(
        model, AsyncMock(), limits=RunLimits(max_context_bytes=2048)
    ).run("x" * 4096, TaskContext(user_id=1))
    assert answer.status == "context_limit"
    assert answer.model_steps == 0
    assert model.inputs == []


async def test_tool_budget_rejects_batch_before_execution():
    """A model batch cannot partially execute beyond the configured call budget."""
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "search_resources",
                "args": {"intent": "claims"},
                "id": str(index),
                "type": "tool_call",
            }
            for index in range(2)
        ],
    )
    service = AsyncMock()
    answer = await MainAgent(
        ScriptedModel([response]), service, limits=RunLimits(max_tool_calls=1)
    ).run("Find claims", TaskContext(user_id=1))
    assert answer.status == "tool_limit"
    service.search.assert_not_awaited()


async def test_timeout_is_explicit_and_external_cancellation_propagates():
    """The runtime distinguishes its deadline from caller cancellation."""
    import asyncio

    service = AsyncMock()
    started = asyncio.Event()

    async def wait_for_cancel(*args):
        """Block a tool until the deadline or caller cancels it."""
        started.set()
        await asyncio.Event().wait()

    service.search.side_effect = wait_for_cancel
    response = call("search_resources", {"intent": "claims"})
    answer = await MainAgent(
        ScriptedModel([response]), service, limits=RunLimits(timeout_seconds=0.01)
    ).run("Find claims", TaskContext(user_id=1))
    assert answer.status == "timeout"
    started.clear()
    task = asyncio.create_task(
        MainAgent(ScriptedModel([response]), service).run(
            "Find claims", TaskContext(user_id=1)
        )
    )
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def test_provider_timeout_is_not_mislabeled_as_runtime_budget():
    """An upstream timeout remains an infrastructure error."""
    service = AsyncMock()
    service.search.side_effect = TimeoutError("upstream timeout")
    model = ScriptedModel([call("search_resources", {"intent": "claims"})])
    with pytest.raises(TimeoutError, match="upstream timeout"):
        await MainAgent(model, service).run("Find claims", TaskContext(user_id=1))


@pytest.mark.parametrize(
    "response",
    [
        AIMessage(content=""),
        AIMessage(
            content="",
            invalid_tool_calls=[
                {
                    "name": "search_resources",
                    "args": "{",
                    "id": "bad",
                    "error": "invalid JSON",
                    "type": "invalid_tool_call",
                }
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "search_resources",
                    "args": {"intent": "claims"},
                    "id": "same",
                    "type": "tool_call",
                }
            ]
            * 2,
        ),
    ],
)
async def test_malformed_model_output_never_executes_tools(response):
    """Empty answers, unparsed calls and duplicate call IDs are protocol failures."""
    service = AsyncMock()
    answer = await MainAgent(ScriptedModel([response]), service).run(
        "Find claims", TaskContext(user_id=1)
    )
    assert answer.status == "invalid_model_output"
    service.search.assert_not_awaited()


async def test_context_limit_stops_remaining_tools_in_batch():
    """One large read cannot cause the rest of a batch to exceed the context cap."""
    service = AsyncMock()
    service.search.return_value = {"description": "x" * 8000}
    response = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "search_resources",
                "args": {"intent": "claims"},
                "id": str(index),
                "type": "tool_call",
            }
            for index in range(2)
        ],
    )
    answer = await MainAgent(
        ScriptedModel([response]), service, limits=RunLimits(max_context_bytes=6000)
    ).run("Find claims", TaskContext(user_id=1))
    assert answer.status == "context_limit"
    assert service.search.await_count == 1


async def test_reused_runtime_starts_each_task_with_fresh_context():
    """A shared model runtime must not carry prior skill or user context forward."""
    model = ScriptedModel(
        [
            call("load_skill", {"name": "schema-inspection"}),
            AIMessage(content="Ready to inspect."),
            AIMessage(content="What table should I find?"),
        ]
    )
    agent = MainAgent(model, AsyncMock())
    first = await agent.run(
        "Inspect my schema", TaskContext(user_id=1, active_workbook_id="wb_first")
    )
    second = await agent.run(
        "Find a table", TaskContext(user_id=2, active_workbook_id="wb_second")
    )
    assert first.loaded_skills == {"schema-inspection": "1"}
    assert second.loaded_skills == {}
    assert second.working_set == ()
    assert model.inputs[0][0].content == model.inputs[2][0].content
    assert "wb_first" not in str(model.inputs[2])
