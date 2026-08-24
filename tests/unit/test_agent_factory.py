import warnings
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.warnings import LangGraphDeprecatedSinceV10

from klaudia.core.supervisor.agents.data_entry_team import agents as team_agents
from klaudia.core.supervisor.agents.data_entry_team.prompts import (
    READ_AGENT_PROMPT,
    SHEET_AGENT_PROMPT,
    WRITE_AGENT_PROMPT,
)
from klaudia.core.supervisor.agents.sql_agent import agent as sql_agent
from klaudia.core.supervisor.agents.sql_agent.prompts import SQL_AGENT_PROMPT


def _capture_agent_calls(
    calls: list[dict[str, Any]],
) -> Callable[..., object]:
    """Return a fake stable agent factory that records its inputs.

    Args:
        calls: Target list for captured factory arguments.

    Returns:
        A factory stub that records each call.
    """

    def create_agent(model: Any, tools: list[Any], *, system_prompt: str) -> object:
        """Record one agent factory call.

        Args:
            model: Chat model passed to the factory.
            tools: Tools passed to the factory.
            system_prompt: System prompt passed to the factory.

        Returns:
            An unused agent stub.
        """
        calls.append({"model": model, "tools": tools, "system_prompt": system_prompt})
        return object()

    return create_agent


def test_sql_worker_uses_stable_agent_factory(monkeypatch):
    """Build the SQL worker with LangChain's stable agent factory."""
    calls: list[dict[str, Any]] = []
    model = object()
    registry = SimpleNamespace(tools=[])
    monkeypatch.setattr(sql_agent, "create_agent", _capture_agent_calls(calls))

    sql_agent.make_sql_agent_node(model, registry)

    assert calls == [{"model": model, "tools": [], "system_prompt": SQL_AGENT_PROMPT}]


def test_data_entry_workers_use_stable_agent_factory(monkeypatch):
    """Build each spreadsheet worker with LangChain's stable agent factory."""
    calls: list[dict[str, Any]] = []
    model = object()
    registry = SimpleNamespace(tools=[])
    monkeypatch.setattr(team_agents, "create_agent", _capture_agent_calls(calls))

    team_agents.make_data_entry_team(model, model, registry)

    assert calls == [
        {"model": model, "tools": [], "system_prompt": READ_AGENT_PROMPT},
        {"model": model, "tools": [], "system_prompt": SHEET_AGENT_PROMPT},
        {"model": model, "tools": [], "system_prompt": WRITE_AGENT_PROMPT},
    ]


def test_worker_graphs_compile_without_deprecated_factory_warning():
    """Compile every worker without the removed LangGraph factory."""
    model = FakeListChatModel(responses=["done"])
    registry = SimpleNamespace(tools=[])

    with warnings.catch_warnings(record=True) as captured_warnings:
        warnings.simplefilter("always")
        sql_agent.make_sql_agent_node(model, registry)
        team_agents.make_data_entry_team(model, model, registry)

    deprecated_warnings = [
        warning
        for warning in captured_warnings
        if issubclass(warning.category, LangGraphDeprecatedSinceV10)
    ]
    assert deprecated_warnings == []


async def test_sql_worker_keeps_async_agent_result_contract():
    """Return the stable agent's final message to the supervisor."""
    model = FakeListChatModel(responses=["done"])
    registry = SimpleNamespace(tools=[])
    sql_node = sql_agent.make_sql_agent_node(model, registry)

    command = await sql_node({"messages": [{"role": "user", "content": "hello"}]})

    assert command.update["messages"][0].content == "done"
