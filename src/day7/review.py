"""Aggregate explicit content reviews, refusing ungraded successful responses."""
import argparse
import json
from pathlib import Path
from starter.agent_metrics import aggregate
from .benchmark import fraction
from .data import ROOT, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True, help='Configuration output folder')
    parser.add_argument('--split', choices=['dev', 'test'], required=True)
    args = parser.parse_args()
    load = lambda p: json.loads(p.read_text(encoding='utf-8'))
    cases = [q for q in load(ROOT / 'data/benchmark.json') if q['split'] == args.split]
    traces, reviews = load(args.run / 'agent.json'), load(args.run / 'reviews.json')
    report = aggregate(cases, traces, reviews)
    successful = [t for t in traces if t['status'] != 'error']
    report['search_counts'] = {t['query_id']: sum(e['event'] == 'search' for e in t['events']) for t in successful}
    report['latency_ms'] = {t['query_id']: t['elapsed_ms'] for t in traces}
    costs = [t.get('service_cost_usd') for t in traces]
    report['service_cost_usd'] = sum(costs) if costs and all(c is not None for c in costs) else None
    report['known_service_cost_usd'] = sum(c for c in costs if c is not None)
    report['reviewers'] = sorted({r.get('reviewer', 'unspecified') for r in reviews})
    report['review_limit'] = 'AI-assisted labels require student confirmation; citation existence is not semantic support.'
    write_json(args.run / 'agent_summary.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
