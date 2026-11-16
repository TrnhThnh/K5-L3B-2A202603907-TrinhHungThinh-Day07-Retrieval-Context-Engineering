"""First trial: explicit original-page content labels, all provider errors fail."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.advanced.common import DATA,read_json
from src.advanced.benchmark import score
from src.day7.data import write_json
folder=ROOT/'results/advanced/run-05/test/vision-lite'
cases=[q for q in read_json(DATA/'benchmark.json') if q['split']=='test']
traces=read_json(folder/'traces.json')
notes={
'at01':'Original Table 2 low-income row gives 8 and 7.34%; both values and table citation correct.',
'at02':'Original Table 2 middle-income rows give 30 and 23; difference 7 respondents correct.',
'at03':'Original Table 1 Japan reporting example establishes Cyber Council for government/private-sector information sharing and incident response.',
'at04':'Incorrect row/entity: answer lists other attack entry-point categories from page 87 instead of the Insider Threats mechanisms on page 88. Missing required page 88; fails.',
'at05':'Original Table 3 phishing row explicitly supports credentials/malware and privileged-access spear-phishing targets.',
'at06':'Original Table 4 Technical Standards row gives ISA/IEC 62443 (ISA 2026) and ISO 27001 (2022); names/years supported.'}
reviews=[]
for q,t in zip(cases,traces):
    error=t['status']=='error'
    reviews.append({'query_id':q['id'],'passed':not error and q['id']!='at04',
        'reason':'Provider HTTP 429; system failure counts as not passed, no answer generated.' if error else notes[q['id']],
        'source_pages_checked':[] if error else q['required_pages'],
        'citations_support_all_claims':not error and q['id']!='at04',
        'original_page_verified':not error,'reviewer':'Codex original-PDF content review; student confirmation pending',
        'student_confirmed':False})
write_json(folder/'reviews.json',reviews)
summary=score(cases,traces,reviews)
write_json(folder/'summary.json',summary)
print('First trial:',summary['passed'],'/',summary['total'],'provider errors:',summary['system_errors'])
