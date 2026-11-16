# Exploratory run — not the final evaluation

This folder preserves the first 34-case experiment and protocol failure traces.
`benchmark_snapshot.json` records the original labels and split at that time.
The dev agent run was interrupted after observing invalid citation formatting.
Some later configurations contain connection failures from an earlier sandbox
network attempt; these are not successful model-quality measurements.

The old test (q26–q30 and u03/u04) was inspected while debugging. It was demoted
to dev. Final evaluation uses new prospective test q31–q35/u05/u06 and the fixed
citation renderer. Use `results/final` for the final reported numbers.

Do not aggregate this folder against the current `data/benchmark.json`; hashes
are intentionally different. No scores from this folder are independent final
test scores. No mock adapters were used for these actual-run traces.
