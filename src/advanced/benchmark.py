"""Split-isolated multimodal runs and strict all-case binary scoring."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from .agent import run
from .common import DATA, ROOT, RESULTS, complete, cost, read_json
from .store import Retriever
from src.day7.data import digest, write_json
from src.day7.runtime import load_environment

CONFIGS=ROOT/'configs/advanced.json'


def frozen_hashes():
    files=[DATA/'benchmark.json',DATA/'index_rows.json',DATA/'source.pdf',CONFIGS,
           DATA/'pages.json',DATA/'visual_catalog.json',
           ROOT/'src/advanced/agent.py',ROOT/'src/advanced/store.py',ROOT/'src/advanced/common.py',
           ROOT/'src/advanced/citation_alignment.py']
    return {str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in files}


def execute(cases,config,retriever,folder):
    if (folder/'traces.json').exists():
        raise RuntimeError('Existing run will not be overwritten; use a fresh run folder')
    traces={}
    def one(q):
        # Only question enters the pipeline: no group, answerable, gold pages/bboxes.
        return {'query_id':q['id'],**run(q['question'],retriever,config)}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(one,q) for q in cases]
        for future in as_completed(futures):
            t=future.result(); traces[t['query_id']]=t
            write_json(folder/'traces.json',[traces[q['id']] for q in cases if q['id'] in traces])
            print(config['id'],t['query_id'],t['status'],t['reason'],flush=True)
    ordered=[traces[q['id']] for q in cases]
    write_json(folder/'reviews.template.json',[{'query_id':q['id'],'passed':None,'reason':'',
        'source_pages_checked':[],'citations_support_all_claims':None,
        'original_page_verified':False,'reviewer':'','student_confirmed':False} for q in cases])
    write_json(folder/'run_manifest.json',{'config':config,'cases':[q['id'] for q in cases],
        'completed_at_utc':datetime.now(timezone.utc).isoformat(),'hashes':frozen_hashes(),
        'service_cost':cost([u for t in ordered for u in t['usage']]),
        'errors':[t['query_id'] for t in ordered if t['status']=='error']})
    from .citation_alignment import align_folder
    align_folder(folder)


def score(cases,traces,reviews):
    expected={q['id'] for q in cases}
    if len(traces)!=len(cases) or {t['query_id'] for t in traces}!=expected:
        raise ValueError('Every declared case must have exactly one trace')
    if len({r['query_id'] for r in reviews})!=len(reviews):
        raise ValueError('Duplicate review')
    ts={t['query_id']:t for t in traces}; rs={r['query_id']:r for r in reviews}
    groups={}; outcomes=[]
    for q in cases:
        t=ts[q['id']]
        if t['status']=='error':
            passed=False; reason='System error counts as failure in advanced benchmark.'
        else:
            r=rs.get(q['id'])
            if not r or type(r.get('passed')) is not bool or not r.get('reason') or not r.get('original_page_verified'):
                raise ValueError(f"Missing original-page content review: {q['id']}")
            passed=r['passed']; reason=r['reason']
            if passed and q['answerable']:
                if t['status']!='answered' or r.get('citations_support_all_claims') is not True:
                    raise ValueError('Answer pass inconsistent with status/support')
                if not set(q['required_pages']).issubset(c['page'] for c in t['citations']):
                    raise ValueError('Required evidence pages missing from passed answer')
            if passed and not q['answerable'] and t['status']!='abstain':
                # ADVANCED.md also accepts an explicit statement that evidence is
                # unavailable. Require a content-review label, never infer from ID.
                if t['status']!='answered' or r.get('explicit_insufficient_evidence') is not True:
                    raise ValueError('Unanswerable pass requires abstention or reviewed explicit lack-of-evidence statement')
        bucket=groups.setdefault(q['group'],{'passed':0,'total':0})
        bucket['passed']+=passed; bucket['total']+=1
        outcomes.append({'query_id':q['id'],'group':q['group'],'passed':passed,'reason':reason})
    total=len(cases); passed=sum(t['passed'] for t in outcomes)
    for bucket in groups.values():
        bucket['rate']=bucket['passed']/bucket['total']
    return {'passed':passed,'total':total,'rate':passed/total if total else None,
        'threshold_met':passed*10>=total*9 if total else False,
        'system_errors':sum(t['status']=='error' for t in traces),'groups':groups,'outcomes':outcomes,
        'grading_status':'Codex-assisted original-page reviews; student/teacher confirmation pending',
        'service_cost':cost([u for t in traces for u in t['usage']]),
        'elapsed_ms_total':sum(t['elapsed_ms'] for t in traces)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--env-file',type=Path)
    parser.add_argument('--output',type=Path,default=RESULTS/'run-01')
    sub=parser.add_subparsers(dest='command',required=True)
    b=sub.add_parser('run');b.add_argument('--split',choices=['dev','test'],required=True)
    sub.add_parser('select')
    s=sub.add_parser('score');s.add_argument('--split',choices=['dev','test'],required=True)
    args=parser.parse_args()
    cases=read_json(DATA/'benchmark.json');configs=read_json(CONFIGS)
    if args.command=='select':
        if (args.output/'selection.json').exists():
            raise RuntimeError('Selection already frozen')
        summaries={c['id']:read_json(args.output/'dev'/c['id']/'summary.json') for c in configs}
        selected=sorted(configs,key=lambda c:(-summaries[c['id']]['rate'],
            summaries[c['id']]['service_cost']['known_usd'],c['id']))[0]
        write_json(args.output/'selection.json',{'config':selected,'dev_summaries':summaries,
            'rule':'Highest fully reviewed dev binary pass rate; tie lower known API cost then ID.',
            'selected_at_utc':datetime.now(timezone.utc).isoformat(),'hashes':frozen_hashes()})
        print('Selected',selected['id'],flush=True)
        return
    subset=[q for q in cases if q['split']==args.split]
    if args.split=='test':
        selection=read_json(args.output/'selection.json')
        if selection['hashes']!=frozen_hashes():
            raise RuntimeError('Frozen inputs/code changed; cannot report independent test')
        configs=[selection['config']]
    if args.command=='run':
        load_environment(args.env_file)
        retriever=Retriever()
        for c in configs:
            # Fail fast on key/model/account problems before scheduling all cases.
            # This is a provider-only smoke request, no benchmark question or gold.
            _,usage=complete([{'role':'user','content':'Return JSON {"ready":true}.'}],c['model'],max_tokens=25)
            write_json(args.output/args.split/c['id']/'preflight.json',{'model':c['model'],'usage':usage})
            execute(subset,c,retriever,args.output/args.split/c['id'])
    else:
        for c in configs:
            folder=args.output/args.split/c['id']
            summary=score(subset,read_json(folder/'traces.json'),read_json(folder/'reviews.json'))
            write_json(folder/'summary.json',summary)
            print(c['id'],summary['passed'],'/',summary['total'],flush=True)


if __name__=='__main__':
    main()
