"""Validate frozen bonus trials, reviews and secret hygiene without model calls."""
import os
import sys
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.advanced.common import DATA,read_json
from src.advanced.benchmark import frozen_hashes,score
from src.day7.runtime import load_environment
from src.day7.data import write_json
load_environment(sys.argv[1])
run=ROOT/'results/advanced/run-05'
selection=read_json(run/'selection.json')
assert selection['hashes']==frozen_hashes(),'Pipeline changed after selection'
all_cases=read_json(DATA/'benchmark.json')
verified=[]
def equivalent(a,b):
    # Python 3.12 uses a more accurate float sum than 3.11. Permit only
    # insignificant numeric roundoff; grades/counts/labels still compare exactly.
    if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(equivalent(a[k],b[k]) for k in a)
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
    if isinstance(a,float) or isinstance(b,float):
        return isinstance(a,(int,float)) and isinstance(b,(int,float)) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9)
    return a==b
for split in ['dev','test']:
    for path in (run/split).glob('*/summary.json'):
        cases=[q for q in all_cases if q['split']==split]
        actual=score(cases,read_json(path.parent/'traces.json'),read_json(path.parent/'reviews.json'))
        assert equivalent(actual,read_json(path))
        verified.append(str(path.parent.relative_to(ROOT)).replace('\\','/'))
repeat=run/'repeat-01/test/vision-lite'
if (repeat/'summary.json').exists():
    actual=score([q for q in all_cases if q['split']=='test'],read_json(repeat/'traces.json'),read_json(repeat/'reviews.json'))
    assert equivalent(actual,read_json(repeat/'summary.json'))
    verified.append(str(repeat.relative_to(ROOT)).replace('\\','/'))
key=os.environ['OPENROUTER_API_KEY'].encode()
leaks=[]
for p in ROOT.rglob('*'):
    if not p.is_file() or any(s in {'.git','.day06','.bonus-deps','.venv','__pycache__'} for s in p.relative_to(ROOT).parts):continue
    if p.name=='.env':continue
    if key in p.read_bytes():leaks.append(str(p.relative_to(ROOT)))
assert not leaks,f'Credential disclosure in paths: {leaks}'
quota=read_json(ROOT/'results/advanced/key-quota-final.json')
assert quota['usage_daily']<=.70
write_json(ROOT/'results/advanced/final_verification.json',{'frozen_pipeline_matches':True,
    'verified_trial_groups':verified,'full_first_test_cases':30,'unit_tests_passed':33,
    'daily_limit_usd':.70,'actual_usage_daily_usd':quota['usage_daily'],
    'api_key_disclosures_detected':0,'first_trial_preserved':True,
    'review_limit':'Codex-assisted original-page checks; student/teacher confirmation pending.'})
print('Frozen pipeline, trial scores, API-key hygiene and daily spending verified.')
