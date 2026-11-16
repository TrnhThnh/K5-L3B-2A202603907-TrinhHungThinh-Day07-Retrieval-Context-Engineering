"""Apply explicit inspected labels to the full replication; never auto-pass by IDs."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.advanced.common import DATA,read_json
from src.advanced.benchmark import score
from src.day7.data import write_json
cases=[q for q in read_json(DATA/'benchmark.json') if q['split']=='test']
folder=ROOT/'results/advanced/run-05/repeat-01/test/vision-lite'
traces=read_json(folder/'traces.json')
assert len(traces)==30,'Do not score an incomplete replication'
labels=read_json(ROOT/'artifacts/advanced_repeat_review_labels.json')
reviews=[]
for q,t in zip(cases,traces):
    assert q['id']==t['query_id']
    explicit=False
    if t['status']=='error':
        passed=False;reason='Final provider/system error after bounded retry; counts as failure in 30-case denominator.';support=False
    else:
        if q['id'] not in labels:raise ValueError('Unreviewed answer: '+q['id'])
        label=labels[q['id']]
        passed,reason=label[:2]
        support=label[2] if len(label)>2 else bool(passed)
        explicit=bool(label[3]) if len(label)>3 else False
    reviews.append({'query_id':q['id'],'passed':passed,'reason':reason,
        'source_pages_checked':q['required_pages'] if t['status']!='error' else [],
        'citations_support_all_claims':support if q['answerable'] else None,
        'original_page_verified':t['status']!='error',
        'explicit_insufficient_evidence':explicit if not q['answerable'] else None,
        'reviewer':'Codex original-PDF visual/content review; student/teacher confirmation pending',
        'student_confirmed':False})
write_json(folder/'reviews.json',reviews)
summary=score(cases,traces,reviews)
write_json(folder/'summary.json',summary)
print('Replication:',summary['passed'],'/',summary['total'],'errors',summary['system_errors'])
