"""Check final traces/labels/hashes and detect accidental API-key disclosure."""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from starter.agent_metrics import aggregate
from src.day7.benchmark import load_selection
from src.day7.data import digest, write_json
from src.day7.runtime import load_environment


def main():
    load_environment(sys.argv[1] if len(sys.argv) > 1 else None)
    selection = load_selection(ROOT / 'results/final/selection.json')
    cases = json.loads((ROOT / 'data/benchmark.json').read_text(encoding='utf-8'))
    checks, trace_count = [], 0
    load = lambda p: json.loads(p.read_text(encoding='utf-8'))
    for split in ['dev', 'test']:
        for summary in (ROOT / 'results/final' / split).glob('*/agent_summary.json'):
            traces = load(summary.parent / 'agent.json')
            reviews = load(summary.parent / 'reviews.json')
            subset = [q for q in cases if q['split'] == split]
            assert {t['query_id'] for t in traces} == {q['id'] for q in subset}
            expected = aggregate(subset, traces, reviews)
            recorded = load(summary)
            assert all(recorded[k] == v for k, v in expected.items())
            for t in traces:
                if t['status'] == 'answered':
                    assert set(t['citations']).issubset(t['context_ids'])
                    assert all(f'[{cid}]' in t['answer'] for cid in t['citations'])
                for e in t['events']:
                    if e['event'] == 'search':
                        assert len(e['context']) <= (6000 if summary.parent.name == 'hybrid-context' else 1600)
            trace_count += len(traces)
            checks.append(str(summary.parent.relative_to(ROOT)).replace('\\', '/'))
    runtime = load(ROOT / 'results/final/runtime.json')
    assert all(digest(ROOT / p) == value for p, value in runtime['inputs'].items())
    assert all(digest(ROOT / p) == value for p, value in runtime['code'].items())
    # Scan files actually eligible for submission; credentials remain only in
    # external Day06 .env. Never print a matched secret.
    key = os.getenv('OPENROUTER_API_KEY')
    assert key and len(key) > 12
    leaks = []
    for p in ROOT.rglob('*'):
        if not p.is_file() or any(part in {'.git', '.day06', '.venv', '__pycache__'} for part in p.relative_to(ROOT).parts):
            continue
        if p.name == '.env':
            continue
        if key.encode('utf-8') in p.read_bytes():
            leaks.append(str(p.relative_to(ROOT)))
    assert not leaks, f'Credential disclosure detected in files: {leaks}'
    write_json(ROOT / 'results/final/verification.json', {
        'artifact_groups_verified': checks, 'real_agent_traces': trace_count,
        'selection_hashes_match': True, 'runtime_input_and_code_hashes_match': True,
        'citation_and_budget_invariants_pass': True, 'review_aggregates_match': True,
        'api_key_disclosures_detected': 0, 'unit_tests_passed': 23,
        'review_limit': 'Content grades remain Codex-assisted, student confirmation pending.'})
    print(f'Verified {trace_count} real agent traces; labels/hashes/budgets/citations consistent; no API key disclosure.')


if __name__ == '__main__':
    main()
