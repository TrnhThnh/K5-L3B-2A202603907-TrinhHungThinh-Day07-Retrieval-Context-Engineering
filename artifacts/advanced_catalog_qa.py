"""Question-independent corrections checked against original rendered PDF pages.

No query IDs, benchmark questions, gold answers, or expected evidence enter this
catalog. Preserve raw machine output and document the observed extraction errors.
"""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.day7.data import write_json

DATA=ROOT/'data/advanced'
catalog=json.loads((DATA/'visual_catalog.json').read_text(encoding='utf-8'))
raw=DATA/'visual_catalog.machine.json'
if not raw.exists():write_json(raw,catalog)
by_page={r['page']:r for r in catalog}
audit=[]


def fix(n,reason,regions=None,summary=None):
    r=by_page[n]
    if regions is not None:r['regions']=regions
    if summary is not None:r['page_summary']=summary
    r['verification_status']='Codex original-page extraction QA; student confirmation pending'
    audit.append({'page':n,'issue':reason,'action':'Corrected retrieval catalog using original page; raw machine output preserved.',
        'original_image':f'data/advanced/pages/p{n:03}.jpg','reviewer':'Codex visual inspection, student confirmation pending'})


def region(kind,label,bbox,description):return {'kind':kind,'label':label,'bbox':bbox,'description':description}

fix(12,'Machine invented Figure 1 label for an unnumbered diagram and cropped away outer/bottom content.',[
    region('diagram','Impact-ripple infographic (unnumbered)',[.05,.52,.95,.99],
        'Concentric impact arcs expand outward: Cyber Incident, Local Port Impact, National Economic Impact, Cross-Border Spillover Effects. Icons link a port cyber incident to operations, national economic activity and international spillovers.')])
fix(14,'Machine labeled the whole infographic Figure 1 and gave a bbox covering the introduction rather than charts.',[
    region('chart','A Global Port Resilience Gap — Reporting Incidents',[.05,.37,.95,.55],
        'High-Income 83%; Low- & Middle-Income 56%. Report incidents to a national or sectoral response team.'),
    region('chart','A Global Port Resilience Gap — Assessing Risks',[.05,.58,.95,.76],
        'High-Income 79%; Low- & Middle-Income 56%. Conducted a cybersecurity risk assessment in the past 24 months.'),
    region('chart','A Global Port Resilience Gap — Building Capacity',[.05,.78,.95,.98],
        'High-Income 84%; Low- & Middle-Income 49%. Provide regular cybersecurity training.')])
fix(35,'Machine crop excluded part of legend; values themselves checked correct.',[
    region('chart','Figure 4 — Formal cybersecurity policy',[.11,.45,.90,.76],
        "Donut: Yes 64% (dark blue), No 25% (red), Don't know 11% (gold). Percentage of respondents with a formal cybersecurity policy.")])
fix(56,'Machine bbox excluded chart heading/upper bars and included unrelated text/photo.',[
    region('chart','Figure 12 — Regular cybersecurity awareness training',[.11,.08,.90,.43],
        'Horizontal stacked percentage-of-responses bars for low, lower-middle, upper-middle and high income. Dark blue: Yes at least once a year; light blue: Yes but less than once a year; red: No formal training; gold: Prefer not to say. Values not printed inside bars; exact estimates must not be invented.')])
fix(58,'Machine bbox clipped the bottom Operations supervisor label.',[
    region('diagram','Figure 13 — Types of training provided for port employees',[.11,.44,.90,.73],
        'Left: One size fits all, Cybersecurity training checklist. Right: Personalized cybersecurity training, with labeled Security guard, Crane operator and Operations supervisor.')])
fix(76,'Machine misidentified decorative port photograph as Figure 17; actual Figure 17 is on next page.',[
    region('chart','Figure 16 — Regional representation of survey respondents',[.11,.21,.90,.56],
        'Donut and legend: South Asia gray 2.8%; North America red 4.6%; Middle East, North Africa, Afghanistan & Pakistan yellow 7.3%; Sub-Saharan Africa light blue 16.5%; East Asia & Pacific green 19.3%; Latin America & Caribbean dark blue 23.9%; Europe & Central Asia gold 25.7%.')])
fix(77,'Machine swapped Port association and Port authority in caption and summary; original legend checked.',[
    region('chart','Figure 17 — Survey respondents by organizational type',[.11,.07,.90,.36],
        'Donut legend: Port association green 4.6%; Ministry dark blue 7.3%; Other yellow 14.7%; Terminal operator gold 17.4%; Port authority light blue 56%.')],
    'Figure 17 shows organizational shares: port authority 56%, terminal operator 17.4%, other 14.7%, ministry 7.3%, port association 4.6%. Survey limitations include self-report/social-desirability bias, limited sample representativeness and uneven language reach; results are indicative, not statistically generalizable. Individual survey responses are confidential and not published.')
write_json(DATA/'visual_catalog.json',[by_page[n] for n in sorted(by_page)])
write_json(DATA/'extraction_audit.json',{'method':'Compare original rendered full pages, numerical legends, region boundaries and captions; no benchmark fed to extractor.',
    'corrections':audit,'remaining_limit':'Other machine captions remain provisional. Answer agent must inspect original page images before citing; not all catalog descriptions independently verified.'})
print('Original-page QA corrections saved for',len(audit),'pages; raw machine catalog preserved.')
