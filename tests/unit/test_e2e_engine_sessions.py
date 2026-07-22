"""Hermetic tests for the e2e engine's session / user / drain logic.

Proves the memory-harness behavior (new_session resets the session, as_user
switches user and also resets, background writes are drained before a fresh
session) without the real orchestrator, LLM, or infra.
"""

from tests.e2e.engine_inprocess import run_case_inprocess
from tests.e2e.schema import Case, Turn


class _Capture:
    def __enter__(self):
        return []

    def __exit__(self, *args):
        return False


class _Spy:
    def capture(self):
        return _Capture()


class _Msg:
    def __init__(self, content):
        self.content = content


class _Resp:
    def __init__(self, session_id):
        self.session_id = session_id
        self.message = _Msg("ok")
        self.tools_used: list = []
        self.processing_time_ms = 1
        self.pending_approvals: list = []


class _Orch:
    """Records the (session_id_in, user_id) of each process call and drains."""

    def __init__(self):
        self.seen: list[tuple] = []
        self.drains = 0
        self._n = 0

    async def process(self, *, messages, session_id, user_id, user_name):
        self.seen.append((session_id, user_id))
        if session_id is None:
            self._n += 1
            session_id = 1000 + self._n
        return _Resp(session_id)

    async def drain_background(self):
        self.drains += 1


async def test_new_session_and_user_switch_reset_and_drain():
    case = Case(
        id="U1",
        category="memory",
        title="session/user routing",
        turns=[
            Turn(user="a"),  # 0: first turn -> new session
            Turn(user="b"),  # 1: reuse the session
            Turn(user="c", new_session=True),  # 2: fresh session + drain
            Turn(user="d", as_user=2),  # 3: user switch -> fresh session + drain
        ],
    )
    orch = _Orch()
    await run_case_inprocess(orch, _Spy(), _Spy(), case, None, None)

    # (session_id passed in, user_id) per turn.
    assert orch.seen[0] == (None, 1)  # cold start
    assert orch.seen[1] == (1001, 1)  # session reused
    assert orch.seen[2] == (None, 1)  # new_session dropped the id
    assert orch.seen[3] == (None, 2)  # user switch dropped the id, ran as user 2
    # Drained before the two memory-cold turns (2 and 3), not the reused one.
    assert orch.drains == 2


async def test_plain_case_reuses_one_session_and_never_drains():
    case = Case(
        id="U2",
        category="routing",
        title="no memory features",
        turns=[Turn(user="a"), Turn(user="b"), Turn(user="c")],
    )
    orch = _Orch()
    await run_case_inprocess(orch, _Spy(), _Spy(), case, None, None)

    assert orch.drains == 0
    assert orch.seen[0] == (None, 1)
    assert orch.seen[1] == (1001, 1)
    assert orch.seen[2] == (1001, 1)


async def test_missing_drain_method_is_tolerated():
    # An orchestrator without drain_background (e.g. a minimal fake) must still
    # honor new_session without raising.
    class _NoDrain(_Orch):
        drain_background = None

    case = Case(
        id="U3",
        category="memory",
        title="no drain attr",
        turns=[Turn(user="a"), Turn(user="b", new_session=True)],
    )
    orch = _NoDrain()
    await run_case_inprocess(orch, _Spy(), _Spy(), case, None, None)
    assert orch.seen[1] == (None, 1)
