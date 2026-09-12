# Shared runtime comparison after append procedure v2

Run: 12 September 2026, 05:37 UTC. Source: `204c51f275103a6680773bfda5472bb82bd31035`,
clean working tree. Model: `deepseek-flash`, provider `deepseek`, temperature 0.5,
thinking disabled. Three independent trials per runtime and scenario.

| Scenario | Legacy passed | Main passed | Legacy median | Main median |
|---|---:|---:|---:|---:|
| Sum 1,000 rows | 0/3 | 3/3 | 8.663 s | 4.646 s |
| Append one record | 0/3 | 3/3 | 9.722 s | 6.062 s |

All twelve scheduled trials completed, with no setup errors or unrun entries.
Pytest reported two failed scenario assertions because the legacy trials failed;
this was not a runner crash. All six main-agent trials passed.

## What changed from the baseline

The [baseline](comparison-2026-09-12.md) recorded main append at 2/3, with one
shortened merchant value. This rerun recorded 3/3. All main append trials loaded
`table-append` version `2`. Their captured preparation arguments retained
`Merchant: "Taxi vendor"` and numeric `Amount: 185000`; the final workbook state
matched the expected record. Each trial returned a committed receipt, and no
append-input diagnostics were omitted.

The sum and append fixture fingerprints match the baseline. Prompts, initial
records and expected outcomes did not change. Model settings and runtime limits
also stayed the same; source revision and diagnostic fields changed.

Main sum trials retained the exact total 249842000 and unchanged workbook state.
They loaded no procedural skills; their passing sums therefore do not demonstrate
skill use. Legacy verifier logs showed totals 246527000, 249878000 and 250100000,
all incorrect. Legacy appended the requested text fields but stored `"185000"`
as a string in every trial, so the exact-state checks failed again.

The original merchant-shortening failure did not recur in this sample. Three
trials cannot establish a reliable failure rate or prove the procedure caused the
improvement. The backend still validates submitted operations, not the model's
interpretation of arbitrary prose.

## Environment and limits

- PostgreSQL used the isolated sandbox on port 5433; memory was off.
- Redis and MinIO were again unavailable. The container used database dedup
  fallback, and uploads were unavailable. This was a text-only comparison.
- Read-only cleanup checks found no records for the twelve fixture identities
  in user, session, conversation, pending_approval, ledger_spreadsheet or
  ledger_table_operation.
- Main's deadline was 120 seconds; the outer deadline was 180 seconds. Neither
  triggered. Timing excludes fixture setup and scope checks.
- Runtime order alternated by repeat. Provider caching and nondeterminism were
  uncontrolled. No token/cost measurement exists, and p95 is just the maximum
  of three observations.
- Tool paths, prompts and guardrails differ between runtimes. This does not
  isolate orchestration or establish full-service production readiness.
- Historical reports remain unchanged. Production still uses the legacy runtime.

## Next work

Expand field-preservation cases beyond one merchant: punctuation, multiword
values, text identifiers and explicit conversions. Keep this fixture as a
regression. Restore sandbox services for full-service tests, then proceed with
opt-in chat integration without removing legacy components or bypassing approval
and task-recovery requirements.

## Raw reports

- [Sum trials](comparison-sum_1000-20260912T053719Z-9ec0d7801dda4f8783b6dcd8aa8ab842.json)
- [Append trials](comparison-append-20260912T053719Z-7d14400550764c50b798e0394828d6b7.json)
