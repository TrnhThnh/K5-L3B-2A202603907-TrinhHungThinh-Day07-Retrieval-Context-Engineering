"""Local-only original-query dev retrieval audit; not bonus answer accuracy."""
import argparse
import time
from collections import defaultdict
from pathlib import Path
from .common import DATA, RESULTS, read_json
from .store import Retriever
from src.day7.data import write_json
from src.day7.retrieval import DenseRetriever, LexicalRetriever
from src.day7.runtime import load_environment


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file',type=Path)
    args=parser.parse_args()
    load_environment(args.env_file)
    retriever=Retriever()
    methods={'tfidf':LexicalRetriever(retriever.rows),
             'dense':DenseRetriever(retriever.store,retriever.embedder,'ADVANCED_M1'),
             'hybrid':retriever.hybrid}
    cases=[q for q in read_json(DATA/'benchmark.json') if q['split']=='dev']
    traces=[]; summaries={}
    for name,method in methods.items():
        groups=defaultdict(lambda:{'all_required_pages_retrieved':0,'total':0})
        for q in cases:
            started=time.perf_counter()
            rows=method.search(q['question'],top_k=16)
            pages={r['page'] for r in rows}
            hit=set(q['required_pages']).issubset(pages) if q['answerable'] else None
            if q['answerable']:
                groups[q['group']]['total']+=1
                groups[q['group']]['all_required_pages_retrieved']+=hit
            traces.append({'query_id':q['id'],'method':name,'question':q['question'],'top_k':16,
                'results':rows,'all_required_pages_retrieved':hit,
                'elapsed_ms':(time.perf_counter()-started)*1000})
        summaries[name]={'split':'dev','answerable':15,
            'all_required_pages_retrieved':sum(g['all_required_pages_retrieved'] for g in groups.values()),
            'groups':dict(groups),'service_cost_usd':0,
            'scope':'Coarse page coverage in top-16 rows, not semantic evidence sufficiency, not generated answers, not the >=90% bonus metric.'}
    write_json(RESULTS/'local-dev/traces.json',traces)
    write_json(RESULTS/'local-dev/summary.json',summaries)
    print({name:s['all_required_pages_retrieved'] for name,s in summaries.items()},flush=True)


if __name__=='__main__':main()
