"""Run with python -m src.day7.cli --help from the repository root."""
import argparse
import json
import os
from pathlib import Path
from .agent import OpenRouter, run_agent
from .benchmark import CONFIG_PATH, DATA_PATH, freeze_selection, load_selection, review_template, run_agent_cases, run_retrieval, summarize_retrieval
from .data import ROOT, load_chunks, validate_cases, write_json
from .retrieval import build_retriever


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('prepare')
    sub.add_parser('check')
    sub.add_parser('init-index')
    bench = sub.add_parser('benchmark')
    bench.add_argument('--split', required=True, choices=['dev', 'test'])
    bench.add_argument('--output', type=Path, default=ROOT / 'results/live')
    bench.add_argument('--methods', nargs='+', choices=['tfidf', 'dense', 'hybrid'], default=['tfidf', 'dense', 'hybrid'])
    bench.add_argument('--agent', action='store_true')
    agent_bench = sub.add_parser('agent-benchmark', help='Run model against an already frozen experiment, preserving retrieval metrics')
    agent_bench.add_argument('--split', required=True, choices=['dev', 'test'])
    agent_bench.add_argument('--output', type=Path, default=ROOT / 'results/live')
    ask = sub.add_parser('ask')
    ask.add_argument('question')
    ask.add_argument('--method', choices=['tfidf', 'dense', 'hybrid'], default='hybrid')
    ask.add_argument('--trace', type=Path, default=ROOT / 'results/demo_trace.json')
    ask.add_argument('--category', choices=['executive_summary', 'introduction', 'policy', 'practice', 'barriers', 'conclusions', 'appendices'])
    args = parser.parse_args()
    if args.command == 'agent-benchmark':
        args.methods, args.agent = ['tfidf', 'dense', 'hybrid'], True
    if args.command == 'prepare':
        from .prepare import prepare
        print(prepare())
        return
    chunks = load_chunks()
    if args.command == 'check':
        cases = json.loads(DATA_PATH.read_text(encoding='utf-8'))
        validate_cases(cases, chunks)
        print(json.dumps({'chunks': len(chunks), 'cases': len(cases), 'benchmark_valid': True}))
        return
    # TF-IDF-only benchmark uses only the Python standard library.
    offline = args.command == 'benchmark' and args.methods == ['tfidf'] and not args.agent
    if not offline:
        from .runtime import load_environment
        load_environment(args.env_file)
    if args.command == 'init-index':
        from .runtime import initialize_index
        initialize_index()
        print('Rebuilt isolated DAY7_B. Set DAY6_STRATEGY=DAY7_B to use it.')
        return
    store = embedder = None
    strategy = os.getenv('DAY6_STRATEGY', 'B')
    methods = [args.method] if args.command == 'ask' else args.methods
    if any(m in {'dense', 'hybrid'} for m in methods):
        from .runtime import connect_dense
        store, embedder, strategy = connect_dense(chunks)
    client = None
    if args.command == 'ask' or args.agent:
        client = OpenRouter(os.getenv('OPENROUTER_API_KEY'), os.getenv('CHAT_MODEL', 'openai/gpt-4o-mini'))
    if args.command == 'ask':
        retriever = build_retriever(args.method, chunks, store, embedder, strategy)
        result = run_agent(args.question, client, retriever, top_k=6, budget=6000,
                           filters={'category': args.category} if args.category else {})
        write_json(args.trace, result)
        print(result['answer'] or result['reason'])
        if result['status'] == 'error':
            raise SystemExit(1)
        return
    cases = json.loads(DATA_PATH.read_text(encoding='utf-8'))
    validate_cases(cases, chunks)
    selected_cases = [q for q in cases if q['split'] == args.split]
    configs = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    if args.split == 'test':
        selected = load_selection(args.output / 'selection.json')
        configs = list({c['id']: c for c in [selected['baseline'], selected['config']]}.values())
        if any(c['method'] not in args.methods for c in configs):
            raise RuntimeError('Test requires baseline and selected method; do not omit either')
    else:
        configs = [c for c in configs if c['method'] in args.methods]
    if args.command == 'agent-benchmark':
        load_selection(args.output / 'selection.json')
        for config in configs:
            target = args.output / args.split / config['id']
            retrieval = json.loads((target / 'retrieval.json').read_text(encoding='utf-8'))
            retriever = build_retriever(config['method'], chunks, store, embedder, strategy, config.get('candidates', 20))
            trace_path = target / 'agent.json'
            if trace_path.exists():
                old = json.loads(trace_path.read_text(encoding='utf-8'))
                if any(t['status'] != 'error' for t in old):
                    raise RuntimeError('Successful agent run already exists; use a new experiment output')
                write_json(target / 'agent.connection-errors.json', old)
            traces = run_agent_cases(selected_cases, config, client, retriever, trace_path)
            write_json(target / 'reviews.json', review_template(selected_cases, traces, retrieval))
        return
    if args.split == 'dev' and (args.output / 'selection.json').exists():
        raise RuntimeError('Selection already frozen; use a new output directory')
    summaries = {}
    for config in configs:
        target = args.output / args.split / config['id']
        retriever = build_retriever(config['method'], chunks, store, embedder, strategy, config.get('candidates', 20))
        traces = run_retrieval(selected_cases, config, retriever)
        write_json(target / 'retrieval.json', traces)
        summary = summarize_retrieval(traces)
        summaries[config['id']] = summary
        write_json(target / 'summary.json', summary)
        print(json.dumps({'config': config['id'], **summary}, ensure_ascii=False), flush=True)
        if client:
            agent_traces = run_agent_cases(selected_cases, config, client, retriever, target / 'agent.json')
            # Never overwrite a completed human review.
            review_path = target / 'reviews.json'
            if not review_path.exists():
                write_json(review_path, review_template(selected_cases, agent_traces, traces))
    write_json(args.output / args.split / 'summaries.json', summaries)
    if args.split == 'dev':
        selection_path = args.output / 'selection.json'
        if selection_path.exists():
            raise RuntimeError('Selection already frozen; use a new output directory for a new experiment')
        freeze_selection(selection_path, configs, summaries)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError) as exc:
        # Database connection exceptions can contain credentials. Type only at CLI.
        print(f'Run failed ({type(exc).__name__}). Check environment, database, model and trace. No fake fallback.')
        raise SystemExit(1)
