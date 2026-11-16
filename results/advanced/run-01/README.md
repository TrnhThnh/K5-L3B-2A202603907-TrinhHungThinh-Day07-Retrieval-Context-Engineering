# Exploratory dev run interrupted by API-key daily cap

No test was run in this folder. Catalog extraction and a few dev calls consumed
the configured OpenRouter key's USD 0.50 daily allowance; the provider then
returned HTTP 403 (USD 0.51 used). This is a real external limit, not an answer
quality result or a successful bonus benchmark.

Dev also exposed a provider protocol variation: multiple `inspect_pages` calls
were returned despite `parallel_tool_calls=false`. The adapter was subsequently
updated to merge read-only page inspections under the same cap. Original-image
catalog QA corrected legend/label/bbox errors. These changes require a fresh dev
run before selection; no test results were used to tune them.

Preserve these errors for diagnosis. Do not use this partial run to claim the
90% bonus threshold or combine its results with a later complete test.
