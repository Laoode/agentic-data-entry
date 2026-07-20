import logging
from typing import Callable, Literal, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from typing_extensions import TypedDict

from klaudia.core.supervisor._content import coerce_to_text
from klaudia.core.supervisor._context import (
    build_team_classifier_context,
    build_worker_system,
    is_system_message,
    swap_system,
)
from klaudia.core.supervisor.llm import ainvoke_route, with_structured
from klaudia.core.supervisor.agents.data_entry_team.prompts import (
    DATA_ENTRY_SUPERVISOR_PROMPT,
    READ_AGENT_PROMPT,
    SHEET_AGENT_PROMPT,
    WRITE_AGENT_PROMPT,
)
from klaudia.core.supervisor.state import SupervisorState
from klaudia.core.supervisor.tools.wrappers import (
    get_read_tools,
    get_sheet_tools,
    get_write_tools,
)
from klaudia.interfaces.tool_registry import MCPToolRegistry

logger = logging.getLogger(__name__)

MEMBERS = ["read_agent", "sheet_agent", "write_agent"]
VALID_ROUTES = {*MEMBERS, "FINISH"}

TERMINAL_MARKERS = ("[WRITE_DONE]", "[SHEET_DONE]", "[CLARIFY]")
NON_TERMINAL_MARKERS = ("[READ_DONE]",)
COMPLETION_MARKERS = TERMINAL_MARKERS + NON_TERMINAL_MARKERS
WORK_DONE_MARKERS = ("[WRITE_DONE]", "[SHEET_DONE]", "[READ_DONE]")


class TeamRouter(TypedDict):
    # Constrained to the team's own namespace. Guided decoding (vLLM json_schema)
    # / function-calling (DeepSeek) then makes it impossible for the routing LLM
    # to echo a parent-layer name like "data_entry_team" or "sql_agent".
    next: Literal["read_agent", "sheet_agent", "write_agent", "FINISH"]


# Deterministic compound-intent detection. Unambiguous verb sets only: this is a
# SAFE SUBSET that forces the correct sheet_agent->write_agent ordering for the
# common "buatkan sheet X, masukkan ini" case. Anything it misses still falls to
# the sheet-aware LLM classifier below, so false negatives are harmless.
_CREATE_SHEET_VERBS = ("buat", "bikin", "create")
_CREATE_SHEET_PHRASES = ("sheet baru", "new sheet", "new tab", "tab baru")
_SHEET_WORDS = ("sheet", "tab")
# Data-insertion verbs only (excludes ambiguous "tambah", which also means
# "tambah sheet" = create, not write).
_WRITE_VERBS = (
    "masuk",
    "input",
    "catat",
    "isi",
    "record",
    "insert",
    "simpan",
    "entri",
    "entry",
)


def _has_create_sheet_intent(text: str) -> bool:
    t = text.lower()
    if any(p in t for p in _CREATE_SHEET_PHRASES):
        return True
    return any(v in t for v in _CREATE_SHEET_VERBS) and any(
        w in t for w in _SHEET_WORDS
    )


def _has_write_intent(text: str) -> bool:
    t = text.lower()
    return any(v in t for v in _WRITE_VERBS)


def _latest_user_text(messages: list) -> str:
    """The triggering user instruction: the most recent human turn that is
    neither a worker reply nor the injected [Extraction Result] block."""
    for m in reversed(messages):
        if getattr(m, "name", None) in MEMBERS:
            continue
        if is_system_message(m):
            continue
        role = m.get("role") if isinstance(m, dict) else getattr(m, "type", None)
        if role not in ("user", "human"):
            continue
        content = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
        text = coerce_to_text(content)
        if text.startswith("[Extraction Result]"):
            continue
        return text
    return ""


def _normalize_route(raw: str) -> str:
    cleaned = raw.strip()
    for member in MEMBERS:
        if cleaned.startswith(member):
            return member
    if "FINISH" in cleaned.upper():
        return "FINISH"
    logger.warning("Unrecognized route %r, defaulting to FINISH", raw)
    return "FINISH"


def _is_terminal_marker(content: str) -> bool:
    return any(marker in content for marker in TERMINAL_MARKERS)


def _count_tool_messages(messages: list) -> int:
    return sum(1 for m in messages if isinstance(m, ToolMessage))


def _ground_marker_against_tool_calls(
    agent_name: str, messages: list, fallback_question: str
) -> str:
    """Guard against hallucinated *_DONE markers with no actual tool calls."""
    final_text = coerce_to_text(messages[-1].content)
    has_done_marker = any(m in final_text for m in WORK_DONE_MARKERS)
    if not has_done_marker:
        return final_text
    if _count_tool_messages(messages) == 0:
        logger.warning(
            "%s emitted a *_DONE marker without any tool calls — rewriting to [CLARIFY]. "
            "Original: %r",
            agent_name,
            final_text,
        )
        return f"[CLARIFY] {fallback_question}"
    return final_text


def make_data_entry_team(
    routing_llm: BaseChatModel,
    worker_llm: BaseChatModel,
    mcp_gsheets: MCPToolRegistry,
):
    """Build the data entry team subgraph.

    routing_llm: pre-bound with minimal thinking (team_supervisor routing call)
    worker_llm:  pre-bound with low thinking (create_react_agent workers)
    """
    read_agent = create_react_agent(
        worker_llm, tools=get_read_tools(mcp_gsheets), prompt=READ_AGENT_PROMPT
    )
    sheet_agent = create_react_agent(
        worker_llm, tools=get_sheet_tools(mcp_gsheets), prompt=SHEET_AGENT_PROMPT
    )
    write_agent = create_react_agent(
        worker_llm, tools=get_write_tools(mcp_gsheets), prompt=WRITE_AGENT_PROMPT
    )

    async def read_node(state: SupervisorState) -> Command[Literal["supervisor"]]:
        result = await read_agent.ainvoke(state)
        text = _ground_marker_against_tool_calls(
            "read_agent",
            result["messages"],
            "Saya kesulitan membaca sheet yang Anda maksud. Bisakah Anda menjelaskan ulang?",
        )
        return Command(
            update={"messages": [HumanMessage(content=text, name="read_agent")]},
            goto="supervisor",
        )

    async def sheet_node(state: SupervisorState) -> Command[Literal["supervisor"]]:
        result = await sheet_agent.ainvoke(state)
        text = _ground_marker_against_tool_calls(
            "sheet_agent",
            result["messages"],
            "Saya gagal mengeksekusi perubahan struktur sheet. Bisakah Anda menjelaskan ulang?",
        )
        return Command(
            update={"messages": [HumanMessage(content=text, name="sheet_agent")]},
            goto="supervisor",
        )

    async def write_node(state: SupervisorState) -> Command[Literal["supervisor"]]:
        result = await write_agent.ainvoke(state)
        text = _ground_marker_against_tool_calls(
            "write_agent",
            result["messages"],
            "Saya tidak berhasil mengeksekusi operasi tulis. Bisakah Anda menjelaskan ulang?",
        )
        return Command(
            update={"messages": [HumanMessage(content=text, name="write_agent")]},
            goto="supervisor",
        )

    async def team_supervisor(
        state: SupervisorState,
    ) -> Command[Literal["read_agent", "sheet_agent", "write_agent", "__end__"]]:
        msgs = state.get("messages") or []
        pending = state.get("pending_worker")

        # 1. A worker just reported back.
        if msgs:
            last = msgs[-1]
            last_name = getattr(last, "name", None)
            last_content = coerce_to_text(getattr(last, "content", ""))
            if last_name in MEMBERS and _is_terminal_marker(last_content):
                # Compound sequencer: the structural step of a create-then-write
                # just landed. Run the parked worker instead of FINISHing, so the
                # data actually gets written into the sheet we just created.
                if pending in MEMBERS and "[SHEET_DONE]" in last_content:
                    logger.info(
                        "Team supervisor: [SHEET_DONE] received, routing parked %s",
                        pending,
                    )
                    return Command(
                        goto=pending, update={"next": pending, "pending_worker": None}
                    )
                logger.info(
                    "Team supervisor: deterministic FINISH (terminal marker from %s)",
                    last_name,
                )
                return Command(goto=END, update={"next": "FINISH"})

        # 2. First dispatch this invocation (no worker has run yet).
        no_worker_ran = not any(getattr(m, "name", None) in MEMBERS for m in msgs)
        if no_worker_ran:
            user_text = _latest_user_text(msgs)
            # Deterministic compound: "buatkan sheet X, masukkan ini" -> the sheet
            # must exist before the write. Force sheet_agent first and park the
            # write. Ordering only; the workers resolve the actual sheet name.
            if _has_create_sheet_intent(user_text) and _has_write_intent(user_text):
                logger.info(
                    "Team supervisor: compound create+write detected -> sheet_agent "
                    "first, parking write_agent"
                )
                return Command(
                    goto="sheet_agent",
                    update={"next": "sheet_agent", "pending_worker": "write_agent"},
                )

        # 3. LLM classification. Strip the parent persona (it primes the sub-router
        # to echo the parent namespace) but ADD the live sheet list, so the
        # classifier knows which sheets exist and can order create-then-write for
        # implicit cases the deterministic step above does not catch.
        convo = [m for m in msgs if not is_system_message(m)]
        classifier_prompt = build_team_classifier_context(
            DATA_ENTRY_SUPERVISOR_PROMPT, state.get("sheets_context", "")
        )
        messages = [{"role": "system", "content": classifier_prompt}] + convo
        # routing_llm is pre-bound with minimal thinking — classification task only.
        response = await ainvoke_route(
            with_structured(routing_llm, TeamRouter), messages
        )
        if response is None:
            # No parseable route (malformed tool-call JSON) even after retry.
            # End the sub-graph cleanly so the parent can summarize, rather than
            # crashing on response["next"].
            logger.warning(
                "Team supervisor: no valid structured route; FINISH fallback"
            )
            return Command(goto=END, update={"next": "FINISH"})
        goto = _normalize_route(response["next"])
        if goto == "FINISH":
            goto = END
        return Command(goto=goto, update={"next": goto})

    builder = StateGraph(SupervisorState)
    builder.add_node("supervisor", team_supervisor)
    builder.add_node("read_agent", read_node)
    builder.add_node("sheet_agent", sheet_node)
    builder.add_node("write_agent", write_node)
    builder.add_edge(START, "supervisor")

    return builder.compile()


def make_data_entry_team_node(
    routing_llm: BaseChatModel,
    worker_llm: BaseChatModel,
    mcp_gsheets: MCPToolRegistry,
    on_sheet_mutation: Optional[Callable[[], None]] = None,
):
    """Create the data entry team node for the top-level supervisor.

    on_sheet_mutation: optional zero-arg callback fired when the team reports
    [SHEET_DONE]. Used by SupervisorAgent to invalidate the sheet list cache.
    """
    team_graph = make_data_entry_team(routing_llm, worker_llm, mcp_gsheets)

    async def data_entry_team_node(
        state: SupervisorState,
    ) -> Command[Literal["supervisor"]]:
        # Replace the parent persona with a lean worker context (voice card +
        # sheet list + date). Workers no longer inherit the 200-line persona,
        # routing reference, or session-file context they never use.
        worker_system = build_worker_system(state)
        team_messages = swap_system(state["messages"], worker_system)
        response = await team_graph.ainvoke(
            {
                "messages": team_messages,
                "sheets_context": state.get("sheets_context", ""),
                "date_context": state.get("date_context", ""),
                "session_id": state.get("session_id", 0),
                "pending_worker": None,
            }
        )
        last_msg = response["messages"][-1]
        last_name = getattr(last_msg, "name", None)
        last_content = coerce_to_text(getattr(last_msg, "content", ""))

        # Safety guard: team_supervisor must have dispatched a worker before
        # returning. If last_name is not from a MEMBER the team graph exited
        # without running any agent (last message is the original user turn).
        # Returning that as a "data_entry_team" message causes _emit_final_reply
        # to hallucinate success — emit [CLARIFY] instead.
        if last_name not in MEMBERS:
            logger.warning(
                "data_entry_team: team_supervisor exited without dispatching a "
                "worker (last_name=%r, snippet=%r). Emitting [CLARIFY].",
                last_name,
                last_content[:120],
            )
            last_content = (
                "[CLARIFY] Saya tidak dapat menyelesaikan operasi ini secara otomatis. "
                "Mohon jelaskan lebih detail apa yang ingin dicatat dan ke sheet mana."
            )

        # Cache invalidation: structural sheet change detected anywhere in the
        # run. Scan ALL messages, not just the last: in a compound create-then-
        # write the final message is [WRITE_DONE] and the [SHEET_DONE] sits
        # earlier, but the new sheet still must show up in the next turn's list.
        if on_sheet_mutation is not None and any(
            "[SHEET_DONE]" in coerce_to_text(getattr(m, "content", ""))
            for m in response["messages"]
        ):
            logger.info("Sheet mutation detected — invalidating sheet list cache")
            on_sheet_mutation()

        return Command(
            update={
                "messages": [HumanMessage(content=last_content, name="data_entry_team")]
            },
            goto="supervisor",
        )

    return data_entry_team_node
