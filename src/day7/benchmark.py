"""Split-explicit experiments, immutable selection and trace/review artifacts."""
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from .agent import run_agent
from .data import ROOT, digest, evidence_hit, pack_context, write_json

CONFIG_PATH = ROOT / 'configs/experiments.json'
DATA_PATH = ROOT / 'data/benchmark.json'


def fraction(n, total):
    return {'n': n, 'N': total, 'rate': n / total if total else None}


def summarize_retrieval(traces):
    valid = [t for t in traces if t['status'] == 'ok' and t['answerable']]
    return {'n': len(traces), 'successful_answerable': len(valid),
        'errors': sum(t['status'] == 'error' for t in traces),
        'hit1': fraction(sum(t['hit1'] for t in valid), len(valid)),
        'hit3': fraction(sum(t['hit3'] for t in valid), len(valid)),
        'context_evidence_rate': fraction(sum(t['context_hit'] for t in valid), len(valid)),
        'median_ms': statistics.median(t['elapsed_ms'] for t in traces) if traces else None,
        'service_cost_usd': 0, 'cost_scope': 'Local retrieval only; excludes LLM agent'}


def run_retrieval(cases, config, retriever):
    traces = []
    for q in cases:
        started = time.perf_counter()
        base = {'query_id': q['id'], 'split': q['split'], 'answerable': q['answerable'],
                'question': q['question'], 'config': config, 'filters': q.get('filter', {})}
        try:
            # Always request top-3 even when the context top-k is different.
            rows = retriever.search(q['question'], filters=q.get('filter'), top_k=max(3, config['top_k']))
            context, ids = pack_context(rows[:config['top_k']], config['budget'])
            traces.append({**base, 'status': 'ok', 'results': rows, 'context': context, 'context_ids': ids,
                'hit1': bool(rows and evidence_hit(rows[0], q['gold'])) if q['answerable'] else None,
                'hit3': any(evidence_hit(r, q['gold']) for r in rows[:3]) if q['answerable'] else None,
                'context_hit': any(evidence_hit(r, q['gold']) for r in rows if r['id'] in ids) if q['answerable'] else None,
                'elapsed_ms': (time.perf_counter() - started) * 1000})
        except Exception as exc:
            traces.append({**base, 'status': 'error', 'error_type': type(exc).__name__,
                           'elapsed_ms': (time.perf_counter() - started) * 1000})
    return traces


def run_agent_cases(cases, config, client, retriever, output):
    traces = {}
    def execute(q):
        trace = run_agent(q['question'], client, retriever, top_k=config['top_k'],
            budget=config['budget'], max_searches=config['max_searches'], filters=q.get('filter'))
        return {'query_id': q['id'], 'question': q['question'], **trace}
    # Independent cases; API concurrency is bounded and writes happen in one thread.
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(execute, q) for q in cases]
        for future in as_completed(futures):
            trace = future.result()
            traces[trace['query_id']] = trace
            write_json(output, [traces[q['id']] for q in cases if q['id'] in traces])
            print(f"  {config['id']} {trace['query_id']}: {trace['status']}", flush=True)
    return [traces[q['id']] for q in cases]


def review_template(cases, traces, retrieval):
    by_id = {q['id']: q for q in cases}
    ret = {t['query_id']: t for t in retrieval}
    return [{'query_id': t['query_id'], 'reviewer': '', 'reason': '',
             'context_grade': None, 'answer_grade': None,
             'citation_support': [None for _ in t['citations']],
             'abstention_correct': None,
             'retrieval_context': ret.get(t['query_id'], {}).get('context', ''),
             'agent_context': t['context'], 'question': by_id[t['query_id']]['question'],
             'expected_answer': by_id[t['query_id']].get('expected_answer'),
             'answer': t['answer']} for t in traces if t['status'] != 'error']


def freeze_selection(output, configs, summaries):
    """Predeclared retrieval-first rule; no test results enter selection."""
    eligible = [c for c in configs if c['id'] in summaries and summaries[c['id']]['errors'] == 0
                and summaries[c['id']]['successful_answerable'] > 0]
    if not eligible:
        raise RuntimeError('No successful dev configuration to select')
    def key(c):
        s = summaries[c['id']]
        return (-s['context_evidence_rate']['rate'], -s['hit3']['rate'], -s['hit1']['rate'],
                c['budget'], c['max_searches'], c['id'])
    best = sorted(eligible, key=key)[0]
    write_json(output, {'config': best, 'baseline': configs[0],
        'selected_at_utc': datetime.now(timezone.utc).isoformat(),
        'rule': 'dev context evidence rate, then Hit@3, then Hit@1; ties use smaller budget/search count and config id. Agent quality is reported separately; selection is retrieval-first.',
        'benchmark_sha256': digest(DATA_PATH), 'configs_sha256': digest(CONFIG_PATH),
        'dev_summaries': summaries})


def load_selection(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if value['benchmark_sha256'] != digest(DATA_PATH) or value['configs_sha256'] != digest(CONFIG_PATH):
        raise RuntimeError('Benchmark/configs changed after selection; rerun dev before test')
    return value
