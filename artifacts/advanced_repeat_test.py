"""Predeclared full test replication after transient provider 429.

Same frozen model/prompt/retrieval/config. Sequential cases, 15s pacing and up to
two whole-question retries ONLY for HTTP 429. All attempts retained; never retry
wrong answers or abstentions. First run remains separately scored in run-05/test.
"""
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.day7.runtime import load_environment
from src.day7.data import write_json
from src.advanced.common import DATA,read_json,cost
from src.advanced.benchmark import frozen_hashes
from src.advanced.agent import run
from src.advanced.store import Retriever
from src.advanced.citation_alignment import align_folder

load_environment(sys.argv[1])
selection=read_json(ROOT/'results/advanced/run-05/selection.json')
assert selection['hashes']==frozen_hashes(),'Frozen pipeline changed'
config=selection['config']
folder=ROOT/'results/advanced/run-05/repeat-01/test'/config['id']
if (folder/'traces.json').exists():raise RuntimeError('Replication exists; do not overwrite')
cases=[q for q in read_json(DATA/'benchmark.json') if q['split']=='test']
write_json(folder/'replication_policy.json',{'declared_at_utc':datetime.now(timezone.utc).isoformat(),
    'reason':'Transient provider HTTP 429; first trial retained and scored separately.',
    'same_frozen_selection':selection,'pacing_seconds_between_cases':15,
    'retry_only':'HTTP 429', 'max_retries':2,'retry_wait_seconds':45,
    'no_retry_on_wrong_answer_or_abstention':True,'all_30_cases':True})
retriever=Retriever();traces=[]
for index,q in enumerate(cases):
    if index:time.sleep(15)
    attempts=[]
    for attempt in range(3):
        result=run(q['question'],retriever,config)
        attempts.append(result)
        rate_limited=result['status']=='error' and any('HTTP 429' in e.get('detail','') for e in result['events'])
        if not rate_limited or attempt==2:break
        print(q['id'],'429; backoff 45s',flush=True)
        time.sleep(45)
    t={'query_id':q['id'],**result,'attempts':attempts}
    t['usage']=[u for a in attempts for u in a['usage']]
    t['service_cost']=cost(t['usage'])
    t['elapsed_ms']=sum(a['elapsed_ms'] for a in attempts)
    traces.append(t)
    write_json(folder/'traces.json',traces)
    print(q['id'],t['status'],'attempts',len(attempts),flush=True)
align_folder(folder)
write_json(folder/'run_manifest.json',{'config':config,'hashes':frozen_hashes(),
    'completed_at_utc':datetime.now(timezone.utc).isoformat(),'service_cost':cost([u for t in traces for u in t['usage']]),
    'cases':[q['id'] for q in cases],'replication':True,
    'first_trial_not_replaced':True,'transport_attempts':sum(len(t['attempts']) for t in traces)})
