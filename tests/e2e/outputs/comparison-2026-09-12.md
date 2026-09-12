# Shared financial runtime comparison: 12 September 2026

Source revision: `152bc5e8b8d8e39256dc2b6265fce42a9a48b5db`, clean working tree.
Model: `deepseek-flash`, provider `deepseek`, temperature 0.5, thinking disabled.
Fixture seed: 1013. Three independent trials per runtime and scenario.

| Scenario | Legacy passed | Main passed | Legacy median | Main median |
|---|---:|---:|---:|---:|
| Sum 1,000 rows | 0/3 | 3/3 | 8.673 s | 4.967 s |
| Append one record | 0/3 | 2/3 | 8.815 s | 6.800 s |

All twelve trials completed without setup errors or missing observations.
Pytest exited with two failed scenario assertions because neither scenario passed
every trial across both runtimes. This is a measured failure, not a runner crash.

## Findings

The correct Amount sum is 249842000. All main-agent sum trials passed the exact
labelled answer and unchanged-workbook checks, using the calculation capability.
Legacy used sheet reads, not the deterministic calculation tool. Its verifier
logs reported incorrect totals of 246680000, 245740000 and 248216000. All three
failed the required answer-line check; this was not only a formatting issue.

All legacy append trials wrote the requested text fields but stored the amount
as the string `"185000"`, not the number `185000`. The full-state check correctly
failed these writes. This score does not mean legacy failed to append a row.

Main append trial 1 stored `Taxi` instead of the requested `Taxi vendor`. The
amount remained numeric and the operation returned a committed receipt. Trials
2 and 3 preserved the full record and passed. A receipt proves the submitted
operation committed; it does not prove the proposal preserved the user's intent.
Literal-value fidelity remains a cutover blocker.

## Limits and environment

- This compares different runtime, tool, prompt and guardrail paths using the
  same configured model, not orchestration alone.
- Each scenario used one common fixture fingerprint across all six trials.
  Owners and workbook IDs differed. Runtime order alternated by repeat.
- Redis at localhost:6379 and MinIO at 127.0.0.1:9000 were unavailable. The
  container used its database fallback for dedup; uploads were unavailable.
  These text-only cases did not exercise extraction or object storage.
- Memory was off. PostgreSQL used the isolated sandbox on port 5433. Read-only
  post-run checks found zero remaining fixture-user records in the user, session,
  conversation, pending_approval, ledger_spreadsheet and ledger_table_operation
  tables for the twelve generated identities.
- Main's deadline was 120 seconds; the outer turn deadline was 180 seconds.
  Neither limit triggered. Latency excludes fixture setup and scope checks.
- Three samples do not establish reliability or stable tail latency. Provider
  caching and nondeterminism were uncontrolled. No token/cost measurement exists.
- Reports retain only a 240-character response snippet, not full final prose.
  The grader's check results and full workbook observations remain available.
- Historical benchmark scores remain unchanged. Do not switch production routing
  or remove legacy components based on this small comparison.

## Next work

Add a regression for preserving complete user-supplied field values through
proposal and execution. Inspect the append procedure and proposal evidence before
changing prompts or contracts. Do not weaken numeric-type or exact-state checks.
Then rerun the same fixtures against the changed revision, keeping this baseline.
Restore Redis and MinIO before claiming a full-service benchmark result.

## Raw reports

- [Sum trials](comparison-sum_1000-20260912T042958Z-6d5e913c6f344d3ea998f521a78ce3b4.json)
- [Append trials](comparison-append-20260912T042958Z-0f08a50dc6534971ad029005a51348db.json)
