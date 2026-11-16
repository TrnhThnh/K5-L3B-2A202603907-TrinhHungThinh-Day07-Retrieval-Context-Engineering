# Final Day07 experiment

- `runtime.json`: actual package/database versions and input/code hashes; no secrets.
- `selection.json`: configuration selected only from original-query dev retrieval,
  before final test, with frozen benchmark/config hashes.
- `dev/<config>/retrieval.json`: original query ranking, context and latency.
- `dev/<config>/agent.json`: real OpenRouter tool calls, rewritten queries, answers,
  citations, usage, errors. Four configurations, 34 cases each.
- `test/<config>/`: baseline and frozen selected configuration, seven cases each.
- `*/<config>/reviews.json`: explicit Codex-assisted content labels, **student
  confirmation pending**. Not independent human grading.
- `*/<config>/agent_summary.json`: aggregation of those labels, errors separated.
- `test/context_reviews.json`: all five answerable test contexts read for each method,
  with 0/1/2 labels and reasons; distinct from simple quote-hit matching.

Final test IDs: q31–q35, u05/u06. Old test was demoted to dev after exploratory
citation-protocol debugging; old snapshots retained in `../run-01/`.
Do not combine metrics from the two runs or claim an externally blind test.

All vectors/model calls in the experiment are real. Unit-test mocks are unrelated
to these results. One dense-dev model/provider/protocol failure (q20) remains in
the trace and is excluded from quality denominators. No retry/cherry-picking.

For final tables, source permissions, limitations and exact commands, read
`report/individual/2A202603907_TrinhHungThinh.md` and `docs/DAY07_RUNBOOK.md`.
