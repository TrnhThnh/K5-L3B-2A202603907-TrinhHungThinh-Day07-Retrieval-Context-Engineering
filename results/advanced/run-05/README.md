# Flash Lite experiment — preserve each trial separately

Model: `google/gemini-2.5-flash-lite`. Daily user ceiling: USD 0.70, checked
before each paid call with headroom for concurrent requests. No re-extraction.

- `dev/vision-lite`: 17/18, known API cost USD 0.02151038.
- `dev/vision-lite-wide`: 17/18, known API cost USD 0.02691638.
- `selection.json`: selects vision-lite by dev score, then lower cost. Frozen
  before final test; hashes cover source, catalog/index, questions, model config
  and answer/retrieval/citation-alignment code.
- `test/vision-lite`: complete first 30-case trial. 5/30 passed; 24 provider 429
  failures and one wrong table-row answer. Errors remain in denominator.
- `repeat-01/`: separate full-trial replication after provider throttling,
  sequential pacing and retries only for HTTP 429. Policy recorded before the
  replication; never retries a wrong answer/abstention. Keep every attempt and
  do not replace the first trial or combine best answers between trials.

Original model citations are in `traces.model-output.json`. `traces.json` adds
query-independent catalog/PDF-layout region alignment; `model_bbox` remains
available. This locates the selected source but does not certify correctness.

All content reviews are Codex-assisted checks against original rendered PDF
pages, with student confirmation pending. A valid citation is not automatically
a correct answer. Read the individual advanced report for current replication
status and all-group binary scores; >=27/30 is required for the bonus threshold.
