"""Explicit content assessments for the selected dev configuration."""
import json
from pathlib import Path

p = Path(__file__).with_name('review_labels.json')
labels = json.loads(p.read_text(encoding='utf-8'))
labels['dev/hybrid-context'] = {
    'q01': [2,[True,True,True,True,True],'Collective responsibility/cascading risk plus governance and committee context supported across cited passages.'],
    'q02': [1,[True,True,True],'Diverse sources and interviews supported, but survey size 109 and desk-based regulatory mapping missing.'],
    'q03': [2,[True],'Table 2 gives 48 and 44.04%; valid alternative evidence.'],
    'q04': [2,[True,True],'Non-binding global framework and national implementation supported.'],
    'q05': [1,[True,True],'Live OT/IT inventories supported, but explicit regular vulnerability scans omitted.'],
    'q06': [1,[False,True,False],'Core linkage supported but some extra efficiency/severity claims and evolving-risk-management attribution exceed their specific cited fragments.'],
    'q07': [2,[True],'All four governance benefits supported.'],
    'q08': [2,[True],'Security assessment and plan requirements supported.'],
    'q09': [0,[],'False abstention despite corpus containing national-governance evidence.'],
    'q10': [2,[True],'65-percent figure explicitly supported.'],
    'q11': [2,[True,True,True,True,True],'Central governance role, national framework and port-level responsibilities supported across passages.'],
    'q12': [1,[True,True],'Operational resilience and information sharing supported, but prevent/respond/recover definition missing.'],
    'q13': [2,[True,True,True],'Scan purpose and examples supported; complementary scan-frequency and OT-vulnerability passages relevant.'],
    'q14': [2,[True,True],'Exercises/40 participants and additional Singapore SOC background both supported.'],
    'q15': [2,[True],'Inventory/risk-rating is a valid progress indicator.'],
    'q16': [1,[True,False],'Difference between plans and missing fallback risks supported, but actual under-practiced readiness finding omitted; regulatory passage does not establish gap.'],
    'q17': [2,[True,False],'All employee-training response options correct; other citation concerns a different specialized-training question.'],
    'q18': [0,[],'False abstention on answerable ROSI definition.'],
    'q19': [2,[True,False],'CRC date and purpose correct; NORMA continuation is not evidence for Los Angeles.'],
    'q20': [1,[True,True,True],'Public/private good and incentive recommendations supported, but specific cross-border societal-benefit rationale is not established by these selected citations.'],
    'q21': [2,[True,True,True,False,True],'Committee functions explicitly supported by committee/oversight passages; generic page 35 has no committee-function detail.'],
    'q22': [2,[True],'Significant system changes trigger scans; explanation consistent with scan purpose.'],
    'q23': [2,[True,False],'Escape Room/shows supported; Barcelona training-evaluation passage does not establish Antwerp activities.'],
    'q24': [2,[True,True],'All four integration areas and reuse of existing port capabilities supported.'],
    'q25': [2,[True,False],'Dates and languages supported on page 75; regional-representation page does not support them.'],
    'q26': [1,[False],'Core SOC monitoring/detection/response right, but extra claim that SOC establishes reporting protocols is stronger than retained paragraph.'],
    'q27': [2,[True,False],'Ship bridge and IT/OT scenarios supported; generic workforce-development citation does not support Cyber-SHIP specifics.'],
    'q28': [2,[True,True,False],'Ownership rules, standardized protocols and controlled file transfer supported; national/international sharing continuation does not establish named safeguards.'],
    'q29': [2,[True],'Ownership/confidentiality/need-to-know rules explicitly supported.'],
    'q30': [1,[False],'Correct DoS targets but adds communications interception as DoS capability; source distinguishes separate vector.']
}
p.write_text(json.dumps(labels, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
