"""Deterministic model scripts exercise the alternative agent's control flow."""

from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from klaudia.core.agent.agent import MainAgent, RunLimits
from klaudia.core.agent.context import TaskContext
from tests.unit.test_agent_discovery_tools import descriptor


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


async def test_optional_writes_bind_revisions_and_return_receipts():
    """Only an explicit executor enables writes with server-bound evidence."""
    service = AsyncMock()
    service.inspect.return_value = descriptor()
    operations = AsyncMock()
    operations.prepare.return_value = {
        "operation_ref": "prepared:one",
        "status": "prepared",
    }
    receipt = {
        "operation_id": "op_one",
        "status": "committed",
        "target": {"table_id": "tbl_claims", "sheet_id": 8},
        "calculation_status": "not_supported",
    }
    operations.execute.return_value = receipt
    model = ScriptedModel(
        [
            call("inspect_resource", {"table_id": "tbl_claims"}),
            call(
                "prepare_table_append",
                {"table_id": "tbl_claims", "records": [{"Amount": 20}]},
                "prepare",
            ),
            call("execute_operation", {"operation_ref": "prepared:one"}, "execute"),
            call("execute_operation", {"operation_ref": "prepared:one"}, "retry"),
            AIMessage(content="Added the record; formula calculation is unsupported."),
        ]
    )
    outcome = await MainAgent(model, service, operations=operations).run(
        "Add a claim", TaskContext(user_id=42)
    )
    user_id, checked = operations.prepare.await_args.args
    assert user_id == 42
    assert checked.expected_sheet_revision == 1
    assert checked.expected_catalogue_revision == 1
    assert operations.execute.await_args.args == (42, "prepared:one")
    assert outcome.operation_receipts == (receipt,)
    assert outcome.working_set == ()
    schemas = {
        tool.name: tool.args_schema.model_json_schema()["properties"]
        for tool in model.tools
    }
    assert set(schemas["prepare_table_append"]) == {"table_id", "records"}
    assert set(schemas["execute_operation"]) == {"operation_ref"}
    assert "read-only catalogue tools" not in model.inputs[0][0].content


async def test_writes_are_disabled_by_default_and_require_inspection():
    """Default runs expose no writes; opt-in preparation requires fresh evidence."""
    model = ScriptedModel([AIMessage(content="Ready")])
    await MainAgent(model, AsyncMock()).run("Hello", TaskContext(user_id=1))
    assert "execute_operation" not in {tool.name for tool in model.tools}
    operations = AsyncMock()
    model = ScriptedModel(
        [
            call(
                "prepare_table_append",
                {"table_id": "tbl_claims", "records": [{"Amount": 20}]},
            ),
            AIMessage(content="I need to inspect the table."),
        ]
    )
    await MainAgent(model, AsyncMock(), operations=operations).run(
        "Add a claim", TaskContext(user_id=1)
    )
    operations.prepare.assert_not_awaited()
    assert model.inputs[1][-1].status == "error"


async def test_execution_timeout_retains_reference_without_claiming_commit():
    """An unknown execution outcome remains recoverable by its original reference."""
    import asyncio

    async def uncertain_execution(*arguments):
        """Simulate waiting for a receipt after the request was sent."""
        await asyncio.Event().wait()

    operations = AsyncMock()
    operations.execute.side_effect = uncertain_execution
    model = ScriptedModel(
        [call("execute_operation", {"operation_ref": "prepared:old"})]
    )
    outcome = await MainAgent(
        model,
        AsyncMock(),
        operations=operations,
        limits=RunLimits(timeout_seconds=0.05),
    ).run("Retry the saved operation", TaskContext(user_id=42))
    assert outcome.status == "timeout"
    assert outcome.operation_references == ("prepared:old",)
    assert outcome.operation_receipts == ()


async def test_uncommitted_executor_response_cannot_become_receipt():
    """A broken executor contract propagates instead of certifying completion."""
    operations = AsyncMock()
    operations.execute.return_value = {"status": "prepared"}
    model = ScriptedModel(
        [call("execute_operation", {"operation_ref": "prepared:old"})]
    )
    from klaudia.core.agent.agent import AgentExecutionError

    with pytest.raises(AgentExecutionError) as failure:
        await MainAgent(model, AsyncMock(), operations=operations).run(
            "Execute", TaskContext(user_id=42)
        )
    assert "no committed receipt" in str(failure.value.__cause__)


async def test_execution_failure_exposes_original_reference_for_recovery():
    """A lost receipt propagates with the server reference needed for retry."""
    from klaudia.core.agent.agent import AgentExecutionError

    operations = AsyncMock()
    operations.execute.side_effect = ConnectionError("receipt response lost")
    model = ScriptedModel(
        [call("execute_operation", {"operation_ref": "prepared:old"})]
    )
    with pytest.raises(AgentExecutionError) as failure:
        await MainAgent(model, AsyncMock(), operations=operations).run(
            "Retry", TaskContext(user_id=42)
        )
    assert isinstance(failure.value.__cause__, ConnectionError)
    assert failure.value.outcome.operation_references == ("prepared:old",)
    assert failure.value.outcome.operation_receipts == ()


async def test_provider_failure_keeps_observed_commit_evidence():
    """A failed final model call must not hide an already committed append."""
    from klaudia.core.agent.agent import AgentExecutionError

    operations = AsyncMock()
    receipt = {
        "operation_id": "op_one",
        "status": "committed",
        "target": {"sheet_id": 8},
    }
    operations.execute.return_value = receipt
    model = ScriptedModel(
        [call("execute_operation", {"operation_ref": "prepared:old"})]
    )
    with pytest.raises(AgentExecutionError) as failure:
        await MainAgent(model, AsyncMock(), operations=operations).run(
            "Execute", TaskContext(user_id=42)
        )
    assert failure.value.outcome.operation_receipts == (receipt,)


async def test_cancelled_execution_preserves_reference_and_cancellation():
    """External cancellation propagates as cancellation with recovery evidence."""
    import asyncio
    from klaudia.core.agent.agent import AgentRunCancelled

    started = asyncio.Event()

    async def wait_for_cancel(*arguments):
        """Pause execution after its reference has been retained."""
        started.set()
        await asyncio.Event().wait()

    operations = AsyncMock()
    operations.execute.side_effect = wait_for_cancel
    model = ScriptedModel(
        [call("execute_operation", {"operation_ref": "prepared:old"})]
    )
    task = asyncio.create_task(
        MainAgent(model, AsyncMock(), operations=operations).run(
            "Execute", TaskContext(user_id=42)
        )
    )
    await started.wait()
    task.cancel()
    with pytest.raises(AgentRunCancelled) as cancellation:
        await task
    assert cancellation.value.outcome.operation_references == ("prepared:old",)
    assert task.cancelled()


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
    assert answer.loaded_skills == {"resource-discovery": "2"}
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
