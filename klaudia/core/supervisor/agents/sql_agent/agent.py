import logging
from typing import Literal

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from klaudia.core.supervisor._content import coerce_to_text
from klaudia.core.supervisor._context import build_sql_system, swap_system
from klaudia.core.supervisor.agents.sql_agent.prompts import SQL_AGENT_PROMPT
from klaudia.core.supervisor.state import SupervisorState
from klaudia.interfaces.tool_registry import MCPToolRegistry
from klaudia.core.supervisor.tools.wrappers import get_sql_tools

logger = logging.getLogger(__name__)


def make_sql_agent_node(llm: BaseChatModel, mcp_archive: MCPToolRegistry):
    """Create an SQL agent node for the supervisor graph."""
    tools = get_sql_tools(mcp_archive)
    agent = create_agent(llm, tools=tools, system_prompt=SQL_AGENT_PROMPT)

    async def sql_agent_node(state: SupervisorState) -> Command[Literal["supervisor"]]:
        # Focused context: file list + session id only, no parent persona and no
        # sheet context (sql_agent never touches Google Sheets).
        sql_messages = swap_system(state["messages"], build_sql_system(state))
        result = await agent.ainvoke({**state, "messages": sql_messages})
        return Command(
            update={
                "messages": [
                    HumanMessage(
                        content=coerce_to_text(result["messages"][-1].content),
                        name="sql_agent",
                    )
                ]
            },
            goto="supervisor",
        )

    return sql_agent_node
