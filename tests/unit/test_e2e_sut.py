"""Runtime adapters preserve scope and distinguish unsupported cases."""

from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage

from klaudia.core.agent.agent import MainAgent
from tests.e2e.schema import Case, Turn, Expect
from tests.unit.test_main_agent import ScriptedModel, call


async def test_main_adapter_observes_calculation_evidence():
    """The adapter captures tool results without exposing expected answers to the model."""
    from tests.e2e.sut import MainAgentSUT, TurnRequest
    from tests.unit.test_agent_discovery_tools import descriptor
    from app.models.chat import KlaudiaMessage

    service = AsyncMock()
    service.inspect.return_value = descriptor()
    evidence = {
        "source": {"table_id": "tbl_claims"},
        "groups": [
            {
                "key": {},
                "metrics": [{"column": "Amount", "operation": "sum", "value": "20"}],
            }
        ],
    }
    service.calculate.return_value = evidence
    model = ScriptedModel(
        [
            call("inspect_resource", {"table_id": "tbl_claims"}),
            call(
                "calculate",
                {
                    "table_id": "tbl_claims",
                    "metrics": [{"column": "Amount", "operation": "sum"}],
                },
                "sum",
            ),
            AIMessage(content="Amount: 20"),
        ]
    )
    sut = MainAgentSUT(MainAgent(model, service))
    view = await sut.run(
        TurnRequest(
            messages=[KlaudiaMessage(role="user", content="Sum claims")],
            user_id=42,
            spreadsheet_id="active",
        )
    )
    assert view.calculations == [evidence]
    assert view.capabilities_attempted == ["calculate", "inspect_resource"]
    assert view.runtime == "main"
    assert service.calculate.await_args.args[0] == 42


def test_main_adapter_rejects_legacy_scope_and_session_contracts():
    """Historical bound-workbook tests cannot silently become owned-workbook tests."""
    from tests.e2e.sut import MainAgentSUT

    sut = MainAgentSUT(AsyncMock())
    case = Case(
        id="scope", category="isolation", title="Bound", turns=[Turn(user="Read")]
    )
    assert "bound_workbook" in sut.unsupported(case)
    case.resource_scope = "owned_workbooks"
    assert sut.unsupported(case) is None
    case.turns.append(Turn(user="Continue"))
    assert "multi-turn" in sut.unsupported(case)


def test_main_adapter_does_not_rewrite_worker_expectations():
    """Authoring new capability checks must be explicit, never a tool-name substitution."""
    from tests.e2e.sut import MainAgentSUT

    case = Case(
        id="legacy",
        category="routing",
        title="Worker route",
        resource_scope="owned_workbooks",
        turns=[Turn(user="Read", expect=Expect(route="data_entry_team"))],
    )
    assert "legacy" in MainAgentSUT(AsyncMock()).unsupported(case)


def test_main_adapter_rejects_unobservable_cache_requirements():
    """Unavailable cache observations cannot silently pass through skip logic."""
    from tests.e2e.sut import MainAgentSUT

    case = Case(
        id="cache",
        category="cache",
        title="Cache hit",
        resource_scope="owned_workbooks",
        turns=[Turn(user="Read", expect=Expect(cache_hits=1))],
    )
    assert "cache" in MainAgentSUT(AsyncMock()).unsupported(case)


async def test_outer_timeout_retains_committed_operation_evidence(monkeypatch):
    """Runner cancellation after commit preserves receipts for state inspection."""
    import asyncio
    from tests.e2e import engine_inprocess
    from tests.e2e.sut import MainAgentSUT

    class WaitingModel(ScriptedModel):
        """Wait for the runner timeout after one successful tool call."""

        async def ainvoke(self, messages, config=None):
            """Execute once, then wait without emitting a final answer."""
            if self.inputs:
                await asyncio.Event().wait()
            return await super().ainvoke(messages, config)

    operations = AsyncMock()
    receipt = {
        "operation_id": "op_one",
        "status": "committed",
        "target": {"sheet_id": 8},
    }
    operations.execute.return_value = receipt
    model = WaitingModel([call("execute_operation", {"operation_ref": "prepared:old"})])
    monkeypatch.setattr(engine_inprocess, "TURN_TIMEOUT_S", 0.05)
    case = Case(
        id="timeout",
        category="write",
        title="Lost answer",
        resource_scope="owned_workbooks",
        turns=[Turn(user="Execute")],
    )
    records = await engine_inprocess.run_case_inprocess(
        None,
        None,
        None,
        case,
        sut=MainAgentSUT(MainAgent(model, AsyncMock(), operations=operations)),
    )
    assert not records[0].result.passed
    assert records[0].view.operation_receipts == [receipt]
    assert records[0].view.operation_references == ["prepared:old"]


async def test_state_observation_failure_retains_receipts_and_report_row():
    """A failed post-run database read must not lose the committed operation record."""
    from tests.e2e.engine_inprocess import run_case_inprocess
    from tests.e2e.sut import MainAgentSUT

    operations = AsyncMock()
    receipt = {
        "operation_id": "op_one",
        "status": "committed",
        "target": {"sheet_id": 8},
    }
    operations.execute.return_value = receipt
    model = ScriptedModel(
        [
            call("execute_operation", {"operation_ref": "prepared:old"}),
            AIMessage(content="Committed"),
        ]
    )
    case = Case(
        id="state-failure",
        category="write",
        title="State unavailable",
        resource_scope="owned_workbooks",
        turns=[Turn(user="Execute", expect=Expect(ledger_state={"Claims": [[20]]}))],
    )
    observer = AsyncMock(side_effect=ConnectionError("snapshot unavailable"))
    records = await run_case_inprocess(
        None,
        None,
        None,
        case,
        sut=MainAgentSUT(MainAgent(model, AsyncMock(), operations=operations)),
        observe_state=observer,
    )
    assert len(records) == 1
    assert not records[0].result.passed
    assert "state observation" in records[0].view.error
    assert records[0].view.operation_receipts == [receipt]
