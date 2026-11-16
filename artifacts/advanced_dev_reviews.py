"""Explicit original-page reviews of run-05 dev; not an automated LLM judge."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.advanced.common import DATA,read_json
from src.day7.data import write_json

notes={
'ad01':'Original Table 2 shows 48 and 44.04%; complete and cited table region contains the row.',
'ad02':'Original page 32 Table 1 continuation states penalties for breaches/general non-compliance; aligned region includes the statement.',
'ad03':'Original Table 3 GPS/AIS row supports navigation errors, masked movements and phantom ships; local PDF layout alignment locates the row.',
'ad04':'Original ripple infographic labels innermost level Cyber Incident; aligned diagram contains it.',
'ad05':'Original page 17 central panel lists binding cyber rules, clear responsibilities and mandatory incident reporting.',
'ad06':'Original Figure 6 has the three Triage branches returned; aligned figure includes all branches.',
'ad07':'Original infographic reporting panel shows 83% and 56%; difference 27 percentage points is correct.',
'ad08':'Original Figure 16 gray South Asia slice is 2.8%, the smallest; compare all legend/slice labels.',
'ad09':'Original Figure 17 ministry dark-blue slice is 7.3%; matches answer.',
'ad10':'Original Figure 4 Yes=64%; original Table 2 low-income count=8; both pages cited.',
'ad11':'Original Box 6 describes isolated zones by function/criticality/protection; original Table 3 third-party row describes lateral spread; both pages cited.',
'ad12':'Original page 60 explains loss prevention rather than new revenue; Box 10 page 61 defines avoided losses relative to control cost; requires both pages.',
'ad13':'Original 2.1.4 paragraph assigns aggregation/correlation to SIEM and coordination to SOAR; PDF text-block alignment includes both.',
'ad14':'Original Box 12 states 2015 and original focus on smart-port development/port community systems. This source-supported wording is accepted even though draft expected answer used the broader founding topics.',
'ad15':'Original page 62 first paragraph explicitly gives time to detect and respond; aligned text block contains both.',
'ad16':'Actual response states missing exact Gambia email-program cost; original relevant case study gives weekly emails but no dollar cost. No guessed cost.',
'ad17':'Actual response explicitly declines exact future Cyber-SHIP incident-prevention count; original lab case study contains no such projection.',
'ad18':'Actual response states Figure 4 provides no 95% confidence interval; original chart labels only percentages.'}
cases={q['id']:q for q in read_json(DATA/'benchmark.json') if q['split']=='dev'}
for name in ['vision-lite','vision-lite-wide']:
    folder=ROOT/'results/advanced/run-05/dev'/name
    traces=read_json(folder/'traces.json');reviews=[]
    for t in traces:
        cid=t['query_id'];passed=True;reason=notes[cid]
        if name=='vision-lite' and cid=='ad12':
            passed=False;reason='Answer is broadly right but cites only page 61. Required multi-hop page 60 loss-prevention evidence is not cited; incomplete evidence set fails strict bonus scoring.'
        if name=='vision-lite-wide' and cid=='ad08':
            passed=False;reason='Incorrectly selects North America 4.6%; original Figure 16 clearly shows smaller South Asia 2.8%. Valid figure citation does not rescue wrong reading.'
        reviews.append({'query_id':cid,'passed':passed,'reason':reason,
            'source_pages_checked':cases[cid]['required_pages'] if cases[cid]['answerable'] else [],
            'citations_support_all_claims':passed if cases[cid]['answerable'] else None,
            'original_page_verified':True,'reviewer':'Codex original-PDF visual/content review; student confirmation pending',
            'student_confirmed':False})
    write_json(folder/'reviews.json',reviews)
