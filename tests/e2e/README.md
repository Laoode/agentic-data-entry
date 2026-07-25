# Klaudia Sandbox — agent evaluation suite

An isolated environment for measuring what the Klaudia agent actually does on
accounting work: which agent it routes to, which tools it calls with which
arguments, and whether the numbers it reports are right.

Two things make it a sandbox rather than a test folder:

1. **Its data stores are its own.** Separate Postgres (port 5433), separate
   Redis logical database, separate object-store bucket. A run cannot read or
   damage development data, and the whole store can be dropped and rebuilt.
2. **Its ground truth is computed, not written.** Every expected amount comes
   from a seeded generator that emits the data and its own totals together, both
   frozen by unit tests. Nobody hand-types an expected number, so the truth
   cannot drift away from the data it describes.

By default a behavioral miss is **recorded, not failed** — a run produces a full
results table rather than stopping at the first problem. `E2E_STRICT=1` turns
misses into failures when you want a gate.

## Quick start

```bash
docker compose --profile sandbox up -d postgres-sandbox   # once
MOCK_KIE=true SHEETS_BACKEND=ledger uv run pytest tests/e2e -q
```

Every run prints which stores it used, as its first line:

```
e2e sandbox ON — DATABASE_URL=postgresql://...:5433/klaudia_sandbox, REDIS_URL=...
```

If that line says `sandbox OFF`, the results came from the development stores.

## The sandbox boundary

`sandbox.py` rebinds the datastore environment variables at import time, before
anything reads settings, because the settings object is cached on first build
and the MCP servers are spawned with a copy of this environment.

| Store | Development | Sandbox | Override |
|---|---|---|---|
| Postgres | `localhost:5432/klaudia` | `localhost:5433/klaudia_sandbox` | `E2E_DATABASE_URL` |
| Redis | `redis://localhost:6379/0` | `redis://localhost:6379/9` | `E2E_REDIS_URL` |
| Object store | `klaudia-blobs` | `klaudia-sandbox-blobs` | `E2E_MINIO_BUCKET` |

If any target resolves to the value it is supposed to replace, the run **raises
`SandboxNotIsolated` instead of starting**. A half-isolated run that still
claimed to be sandboxed would be worse than no isolation, because its results
would be trusted. Set `E2E_SANDBOX=0` to run against development on purpose.

Schemas need no migration step: the app and ledger tables are
`CREATE TABLE IF NOT EXISTS` statements run on first connect, so a fresh
database populates itself. `scripts/sandbox_init.sql` adds only the `vector`
extension, which the application role cannot create for itself.

```bash
docker compose --profile sandbox down -v    # wipe the sandbox entirely
docker compose --profile sandbox up -d      # rebuild it empty
```

## Layout

```
tests/e2e/
  dataset/
    SCHEMA.md               # the case/turn/expect schema — read this to add cases
    cases/*.yaml            # the dataset (source of truth)
    fixtures/               # small support files
  sandbox.py                # datastore isolation + the not-isolated guard
  schema.py                 # pydantic models for the dataset
  loader.py                 # load + validate YAML, resolve attachments
  checks.py                 # ResponseView + evaluate() — shared scoring
  spy.py                    # in-process MCP tool-call spy
  report.py                 # results table, JSON, per-model markdown
  engine_inprocess.py       # runs a case against the orchestrator
  ledger_seeder.py          # deterministic grid writer (no LLM in the seed path)
  synthetic.py              # generators: expense ledgers, scale, branches
  synthetic_finance.py      # generators: P&L, tax, receivables, budget, journal
  synthetic_cases.py        # category -> scratch user + builder registry
  sheet_guard.py            # snapshot/restore for the docs/TABLE.md baseline
  conftest.py               # fixtures (container, orchestrator, spy, guard)
  test_e2e_dataset.py       # behavior suite runner
  test_synthetic_bench_e2e.py  # hard bench runner
  test_memory_e2e.py        # cross-session memory runner
  runner_http.py            # black-box POST /v1/chat layer
  gen_postman.py            # Postman collection generator
  outputs/                  # tables + JSON
```

## Three runners, one dataset

The dataset is one pile of YAML; which runner picks up a case is decided by its
`category`, so a case is never run twice or dropped between runners.

| Runner | Cases | Fixtures | Report |
|---|---|---|---|
| `test_e2e_dataset.py` | behavior suite | `docs/TABLE.md` baseline on the test user | `outputs/table-<model>.md` |
| `test_synthetic_bench_e2e.py` | hard bench | generated ledgers under scratch users 90100+ | `outputs/table-hard-bench.md` |
| `test_memory_e2e.py` | cross-session memory | isolated mem0 collection | asserts inline |

`synthetic_cases.py` holds the category registry that splits them. The behavior
suite skips exactly the categories that registry claims, so adding a hard-bench
category cannot leave it half-registered in one runner and missing from the
other.

### Behavior suite

Guardrails, routing, reads and writes, sheet operations, receipt extraction
(cache hit/miss), HITL clarification, multi-turn recall, attachment rejection,
answer-from-context. Content expectations come from the `docs/TABLE.md`
baseline, which `sheet_guard.py` seeds into the test user's spreadsheet and
restores after every mutating case.

### Hard bench

Deterministic accounting work with exact-match grading and no judge. Two
generator modules feed it:

- `synthetic.py` — expense ledgers, dirty number formats, distractor columns,
  missing values, reconciliation, prompt injection in cell data, hostile
  receipt-style schemas, 160-row and 1000-row scale, multi-spreadsheet branches.
- `synthetic_finance.py` — profit and loss across three statement sheets,
  PPN 11% and PPh 23 withholding, receivables aging against a fixed reference
  date, budget vs actual joined by department name with the rows deliberately
  reordered, double-entry journals with one unbalanced entry, and a ten-turn
  month close.

Each category gets its own scratch user, so its data collides with nothing.
Mutating cases are bracketed by a full template restore before **and** after, so
a destructive failure cannot score later cases against a damaged fixture.

## Running

```bash
# Everything
MOCK_KIE=true SHEETS_BACKEND=ledger uv run pytest tests/e2e -q

# Hard bench only, as a gate (~20 min for 51 turns)
MOCK_KIE=true SHEETS_BACKEND=ledger E2E_STRICT=1 \
  uv run pytest tests/e2e/test_synthetic_bench_e2e.py -q

# Behavior suite, skipping cases that write
uv run pytest tests/e2e/test_e2e_dataset.py -v -s -m "not mutating"

# One case
uv run pytest tests/e2e -k AGG01 -v -s

# Black-box over HTTP (needs ./startup.sh)
python -m tests.e2e.runner_http --filter guardrails

# Postman collection
python -m tests.e2e.gen_postman
```

Memory cases need `MEMORY_MODE=write` and the embedding service up; they skip
otherwise.

## Adding a case

1. **Generate the data and its truth together.** Add a builder to
   `synthetic.py` or `synthetic_finance.py` that returns the grids *and* the
   computed answers. Never write an expected amount by hand.
2. **Freeze it.** Add a golden test in `tests/unit/test_synthetic_ledger.py` or
   `test_synthetic_finance.py` that pins the constants, recomputes the truth
   independently from the grids, and checks that no two asserted amounts collide
   as digit substrings — `contains_amount` strips separators, so a nested amount
   would let a wrong answer pass.
3. **Register the category** in `synthetic_cases.py` with its own scratch user.
4. **Write the YAML**, quoting the frozen amounts and naming the golden test that
   guards them.
5. **Mark it `mutating: true`** if it can write, or a destructive failure will
   poison later cases.

Ambiguity is the thing to avoid hardest. If a question has two defensible
readings that produce different numbers, it cannot be graded exactly — either
rephrase it until one reading survives, or drop it. Two cases have already been
rewritten for this: the receivables ranking question now says "totalled per
customer" because the largest single invoice is a different number.

## Assertions available

Declared per turn in `expect:` (full list in `dataset/SCHEMA.md`):

- **Routing** — `route`, `route_any_of`, `forbid_agents`
- **Content** — `content_any`, `content_all`, `content_none`,
  `contains_amount` (digit-normalized), `excludes_amount` (the negative: a
  figure the agent had no legitimate way to reach), `is_rejection`,
  `is_clarification`, `pending_approvals_min`
- **Tools** — `mcp_tools_any`, `mcp_tools_all`, `mcp_tools_none`,
  `mcp_args_contains` (in-process only; skipped, not failed, over HTTP)
- **Extraction** — `cache_hits`, `cache_misses`
- **Latency** — `latency_ms_max`, `latency_hard`

Turn-level controls: `as_user` (run as another tenant), `new_session` (force a
cold session), `spreadsheet` (bind a named workspace for multi-spreadsheet
cases; an unmapped name raises rather than falling back to the default, because
a silent fallback would score a leak case against the wrong workspace).

## Notes for maintainers

- **Fixtures share an event loop.** Fixtures and tests must both use
  `loop_scope="module"`. MCP stdio sessions bind to the loop that created them;
  a function-scoped test loop deadlocks every MCP call.
- **The MCP spy is best-effort.** If a langgraph version invokes tools through a
  path it does not wrap, `mcp_tools_*` degrades to skipped rather than
  false-failing.
- `tools_used` is sub-agent level by design; granular tool assertions come from
  the spy.
- **Borderline arithmetic cases are not deterministic.** Several flip between
  runs. A single run is a measurement, not a release gate.
- Do not run `tests/integration/database` during a bench. It truncates app
  tables. With the sandbox it now hits a different database, but only while the
  sandbox is actually on.

## What this suite does not yet do

- **No LLM judge.** Everything is exact-match, so qualitative properties
  (was the clarifying question the *right* one, is the explanation faithful)
  are not graded at all. Design in `docs/PLAN.md` Part 3, section 2.
- **No tiering.** Cases are flat; there is no difficulty ladder separating a
  one-sheet lookup from a multi-entity consolidation.
- **Coupled to agent names.** Cases assert `route: data_entry_team` directly, so
  renaming or removing an agent breaks the dataset rather than just the adapter.
