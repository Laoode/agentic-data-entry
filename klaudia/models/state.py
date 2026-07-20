from typing import Any

from langgraph.graph import MessagesState


class KlaudiaState(MessagesState):
    """Extended state for the Klaudia supervisor graph.

    Context is carried as EXPLICIT structured fields, not baked into one prose
    system prompt shared by every layer. Each layer (top supervisor, team
    supervisor, workers, sql_agent) composes its own focused system prompt from
    these fields, so a worker never inherits the full parent persona or another
    agent's context. See router.py / agents.py / sql_agent for the composition.
    """

    next: str = ""
    session_id: int = 0
    user_id: int = 1
    extraction_data: dict[str, Any] | None = None
    session_files: list[dict[str, Any]] | None = None

    # Structured context slices (formatted strings), populated by the
    # orchestrator and threaded into the graph via process/stream_conversation.
    sheets_context: str = ""  # AVAILABLE SHEETS block (index -> title)
    files_context: str = ""  # SESSION FILES block (sql_agent only)
    date_context: str = ""  # CURRENT DATE/TIME line (write_agent needs it)

    # Deterministic compound sequencer: when a single user turn asks to CREATE a
    # sheet AND WRITE into it, the team supervisor forces sheet_agent first and
    # parks the follow-up worker here so write_agent runs after [SHEET_DONE].
    pending_worker: str | None = None
