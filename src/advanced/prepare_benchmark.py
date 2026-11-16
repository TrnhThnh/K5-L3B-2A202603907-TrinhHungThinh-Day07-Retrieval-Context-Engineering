"""Prospective multimodal benchmark, authored from original page inspection.

Gold is stored here and in benchmark.json ONLY; retrieval/agent never imports it.
"""
from collections import Counter
from .common import DATA, ROOT, SOURCE_ID
from src.day7.data import digest, write_json


def evidence(page, bbox, label, detail):
    return {'source_id':SOURCE_ID,'page':page,'bbox':bbox,'label':label,'detail':detail,
            'original_image':f'data/advanced/pages/p{page:03}.jpg',
            'gold_verification':'Codex inspected original rendered PDF; student confirmation pending'}


def prepare():
    cases=[]
    def add(cid,split,group,question,answer,ev,**extra):
        cases.append({'id':cid,'split':split,'group':group,'question':question,'answerable':True,
            'expected_answer':answer,'evidence':ev,'required_pages':sorted({e['page'] for e in ev}),
            'grading':'Binary: correct and complete answer, units/conditions/calculation and supporting page/region citations required.',**extra})
    def e(page,label,detail,bbox=None):
        return evidence(page,bbox or [0.10,0.07,0.91,0.92],label,detail)

    # Dev: 3 positive cases per required modality, plus 3 absence cases.
    add('ad01','dev','table','In Table 2, give the high-income respondent count and percentage.',
        '48 respondents; 44.04%.',[e(75,'Table 2, High-income row','Number=48, Percentage=44.04%.',[.11,.52,.90,.74])])
    add('ad02','dev','table','In Table 1, Enforcement & oversight, what does the Singapore Cybersecurity Act impose?',
        'Penalties for breaches or general non-compliance.',[e(32,'Table 1 continuation, Enforcement & oversight','Singapore row imposes penalties for breaches/general non-compliance.',[.11,.08,.90,.36])])
    add('ad03','dev','table','According to Table 3, how can GPS spoofing and AIS manipulation affect vessels?',
        'Counterfeit satellite signals override GPS causing navigation errors; AIS injects false vessel identity/position, masking movements or creating phantom ships.',
        [e(87,'Table 3, GPS Spoofing & AIS Manipulation','GPS errors; false identity/position, masked movements/phantom ships.',[.11,.77,.90,.87])])
    add('ad04','dev','diagram','In the impact-ripple diagram under Why Does This Report Matter, what event is at the innermost labeled level?',
        'Cyber Incident.',[e(12,'Impact ripple diagram, innermost label','Cyber Incident nearest center.',[.05,.52,.95,.99])])
    add('ad05','dev','diagram','In the Cyber Resilient Ports infographic, list the three actions under Strengthen Policy in The Way Forward panel.',
        'Binding cyber rules; clear responsibilities; mandatory incident reporting.',[e(17,'The Way Forward, Strengthen Policy','Three bullets in central blue panel.',[.33,.48,.68,.88])])
    add('ad06','dev','diagram','In Figure 6, what three branches follow Triage in the reactive approach?',
        'Fix and restoration of operations; external escalation and compliance paperwork; minimal lessons learned.',
        [e(42,'Figure 6, upper reactive flowchart','Three outgoing arrows from Triage.',[.10,.10,.90,.34])])
    add('ad07','dev','chart','In A Global Port Resilience Gap, compare incident-reporting percentages for high-income versus low- and middle-income ports and calculate the gap.',
        '83% versus 56%; gap 27 percentage points.',[e(14,'Reporting Incidents panel','83 and 56 labels; 83-56=27 pp.',[.07,.37,.93,.55])],calculation='83-56=27 percentage points')
    add('ad08','dev','chart','In Figure 16, which region has the smallest response share, and what is its percentage?',
        'South Asia, 2.8%.',[e(76,'Figure 16, donut and legend','Gray South Asia slice=2.8%.',[.11,.21,.90,.52])])
    add('ad09','dev','chart','In Figure 17, what percentage of respondents are ministries?',
        '7.3%.',[e(77,'Figure 17, ministry slice and legend','Dark-blue Ministry slice=7.3%.',[.11,.07,.90,.36])])
    add('ad10','dev','multi_hop','Combine Figure 4 and Table 2: what is the share with a formal cybersecurity policy, and how many low-income respondents were surveyed?',
        '64% have a formal policy; 8 low-income respondents.',[e(35,'Figure 4','Yes=64%.',[.11,.45,.90,.76]),e(75,'Table 2','Low-income count=8.',[.11,.52,.90,.74])])
    add('ad11','dev','multi_hop','Combine Box 6 with Table 3: what does network segmentation do, and what entry point can spread laterally when third-party networks are unsegmented?',
        'Segmentation divides networks into isolated zones by function/criticality/protection; third-party and supply-chain compromise can spread laterally from vendors/contractors/partners.',
        [e(46,'Box 6','Isolated zones grouped by function, criticality, protection.'),e(87,'Table 3, Third-Party & Supply Chain Compromise','Unsegmented networks allow third-party breach to spread laterally.')])
    add('ad12','dev','multi_hop','Using the financial barriers discussion and Box 10, why can ROSI support cybersecurity investment even when cybersecurity creates no direct revenue?',
        'Cybersecurity prevents revenue losses; ROSI estimates avoided losses relative to the control cost to assess cost-effectiveness.',
        [e(60,'3.2 Financial Barriers','No direct revenue; prevents revenue losses.'),e(61,'Box 10, ROSI definition','Avoided losses relative to control cost.')])
    add('ad13','dev','text','What two automated solutions does the report name for aggregating/correlating IT/OT information and coordinating responses, respectively?',
        'SIEM aggregates/correlates real-time IT/OT information; SOAR coordinates responses.',[e(46,'2.1.4 Embracing Automated Cybersecurity Solutions','SIEM and SOAR functions in paragraph after Box 6.')])
    add('ad14','dev','text','What is ChainPORT, when was it established, and what was its original focus?',
        'A global network of leading ports established in 2015 to share port digitalization, innovation and operational-efficiency practices.',
        [e(67,'Box 12, ChainPORT','2015; digitalization, innovation, operational efficiency.')])
    add('ad15','dev','text','When precise cyber-loss prediction is uncertain, which time-based measures does the report suggest CISOs can directly control?',
        'Time needed to detect incidents and respond to them.',[e(62,'Paragraph before 3.3 Economic Barriers','Minimize detection and response time as operational-efficiency indicators.')])

    # Test: exactly 24 positive cases with exclusive primary groups 6/5/5/4/4.
    add('at01','test','table','In Table 2, give the low-income respondent count and exact percentage.',
        '8 respondents; 7.34%.',[e(75,'Table 2, Low-income row','8 and 7.34%.',[.11,.52,.90,.74])])
    add('at02','test','table','Using Table 2, how many more respondents are lower-middle-income than upper-middle-income? Show both counts and the difference.',
        '30 lower-middle versus 23 upper-middle; 7 more respondents.',[e(75,'Table 2, middle-income rows','30-23=7 respondents.',[.11,.52,.90,.74])],calculation='30-23=7 respondents')
    add('at03','test','table','In Table 1, Reporting & information-sharing, which new body does Japan\'s Active Cyber Defense Law establish, and what coordination is it intended to improve?',
        'A Cyber Council to enhance information sharing and incident response between government agencies and key private-sector partners.',
        [e(31,'Table 1, Reporting & information-sharing, Japan example','New Cyber Council and government/private-sector coordination.',[.11,.58,.90,.84])])
    add('at04','test','table','In Table 3, identify the three mechanisms described under Insider Threats.',
        'Employees/contractors can expose credentials, introduce malware via personal devices, or be recruited by criminals to facilitate cyber and physical intrusions.',
        [e(88,'Table 3 continuation, Insider Threats','Credentials; malware through personal devices; recruitment for cyber/physical intrusions.',[.11,.09,.90,.24])])
    add('at05','test','table','According to the Phishing & Spear-Phishing row in Table 3, what do fraudulent messages trick staff into doing, and whom does spear-phishing target?',
        'Surrendering credentials or downloading malware; individuals with privileged system access.',
        [e(87,'Table 3, Phishing & Spear-Phishing','Credentials/malware; privileged system access.',[.11,.38,.90,.46])])
    add('at06','test','table','In Table 4, name the two publications listed under Technical Standards, including their years.',
        'ISA/IEC 62443 OT cybersecurity for industrial control systems series (ISA 2026); ISO 27001 Information security management systems (2022).',
        [e(88,'Table 4, Technical Standards','Two listed standards and dates.',[.11,.84,.90,.92])])
    add('at07','test','diagram','In the impact-ripple diagram, list the three impact levels outward from Cyber Incident, in order.',
        'Local Port Impact → National Economic Impact → Cross-Border Spillover Effects.',
        [e(12,'Impact ripple diagram, expanding arcs','Order of the three outer labeled arcs.',[.05,.52,.95,.99])])
    add('at08','test','diagram','In the vulnerable-versus-cyber-resilient port infographic, list the four callout labels on the vulnerable side and the four on the resilient side.',
        'Vulnerable: Legacy OT Systems; Weak Cyber Governance; Fragmented Systems; Operational Delays. Resilient: Clear Cyber Governance; Coordinated Port Ecosystem; Secure IT and OT Systems; Reliable, Efficient Operations.',
        [e(17,'Cyber Resilient Ports, left/right comparison','Eight printed callouts around the two port drawings.',[.01,.20,.99,.96])])
    add('at09','test','diagram','In Figure 5, list the four port governance models top-to-bottom and explain how public and private responsibility change from the top model to the bottom.',
        'Public Service Port → Tool Port → Landlord Port → Private Port. Public responsibility decreases from primary to limited; private responsibility increases from limited to primary.',
        [e(36,'Figure 5, model rows and opposing triangles','Four model labels; opposite public/private responsibility gradients.',[.11,.48,.90,.71])])
    add('at10','test','diagram','In the continuous/proactive panel of Figure 6, give the six activities clockwise starting at Asset inventory.',
        'Asset inventory → Living risk assessment → Vulnerability identification and prioritization → Mitigation measures and inclusion in BCPs → Testing and Audit → Improvement and lessons learned.',
        [e(42,'Figure 6, lower circular proactive diagram','Six clockwise labeled activities.',[.11,.35,.90,.72])])
    add('at11','test','diagram','In Figure 13, what generic training artifact is shown on the left, and which three job roles are explicitly labeled in the personalized-training panel on the right?',
        'A Cybersecurity training checklist; Security guard, Crane operator, Operations supervisor.',
        [e(58,'Figure 13, both panels','Left checklist label and three right-panel role labels.',[.11,.44,.90,.73])])
    add('at12','test','chart','From Figure 4, give the percentages for No and Don\'t know, then their combined share.',
        'No=25%; Don\'t know=11%; combined 36%.',[e(35,'Figure 4, donut labels and legend','25+11=36%.',[.11,.45,.90,.76])],calculation='25+11=36 percent')
    add('at13','test','chart','In Figure 16, compare Europe & Central Asia with Latin America & Caribbean: give both shares and the percentage-point difference.',
        '25.7% versus 23.9%; Europe & Central Asia higher by 1.8 percentage points.',
        [e(76,'Figure 16, gold and dark-blue slices with legend','25.7-23.9=1.8 pp.',[.11,.21,.90,.52])],calculation='25.7-23.9=1.8 percentage points')
    add('at14','test','chart','From Figure 17, give the shares of port authorities and terminal operators and calculate their gap in percentage points.',
        'Port authority=56%; terminal operator=17.4%; gap=38.6 percentage points.',
        [e(77,'Figure 17, light-blue and gold slices','56-17.4=38.6 pp.',[.11,.07,.90,.36])],calculation='56-17.4=38.6 percentage points')
    add('at15','test','chart','Read Figure 12 using its legend: which income group has the longest dark-blue annual-training segment, and which has the shortest? What does dark blue mean?',
        'High income longest; upper-middle income shortest. Dark blue means Yes, at least once a year.',
        [e(56,'Figure 12, stacked bars and legend','Compare dark-blue segment widths; annual-training legend.',[.11,.08,.90,.43])])
    add('at16','test','chart','In A Global Port Resilience Gap, give both regular-training percentages in Building Capacity and their percentage-point gap.',
        'High-income=84%; low- and middle-income=49%; gap=35 percentage points.',
        [e(14,'Building Capacity panel','84-49=35 pp; regular cybersecurity training.',[.06,.78,.94,.97])],calculation='84-49=35 percentage points')
    add('at17','test','multi_hop','Combine Table 2 with Figure 17: compare the high-income share of respondents with the terminal-operator share. Give both percentages, their difference in percentage points, and distinguish the two classifications.',
        'High-income share=44.04%; terminal-operator share=17.4%; difference=26.64 percentage points. Income level and organizational type are different classifications.',
        [e(75,'Table 2, High-income row','44.04%, income classification.',[.11,.52,.90,.74]),e(77,'Figure 17, Terminal operator','17.4%, organizational classification.',[.11,.07,.90,.36])],calculation='44.04-17.4=26.64 percentage points')
    add('at18','test','multi_hop','Combine Table 1\'s NIS2 reporting example with the Italian circular case study: what reporting timeframe and recipient does the table state, and which Italian facilities are exempt from the circular\'s additional requirements?',
        'Within 24 hours to Computer Security Incident Response Teams; facilities already covered by NIS2 are exempt from additional circular requirements to avoid duplication.',
        [e(31,'Table 1, NIS2 reporting row','24 hours; CSIRTs.',[.11,.58,.90,.84]),e(28,'Box 4, Italian circular','Already covered by NIS2 → exempt from additional requirements.')])
    add('at19','test','multi_hop','Combine Figure 13 and the Cyber-SHIP Lab case study: name the three roles labeled in personalized training, and identify what physical environment the Lab replicates for realistic IT/OT incident training.',
        'Security guard, Crane operator, Operations supervisor; the Lab physically replicates a ship\'s bridge.',
        [e(58,'Figure 13, personalized-training panel','Three role labels.',[.51,.44,.90,.73]),e(59,'Box 9, Cyber-SHIP Lab','Physically replicates a ship bridge for IT/OT scenarios.')])
    add('at20','test','multi_hop','Use the financial-barriers explanation and Box 10\'s formula for this hypothetical scenario: SLE=$100,000, ARO=2/year, mitigation=50%, annual control cost=$25,000. Calculate ALE, avoided annual losses and ROSI, and explain whether the benefit is new revenue or avoided loss.',
        'ALE=$200,000/year; avoided losses=$100,000/year; ROSI=(100000-25000)/25000=3=300%. This is avoided loss, not direct new revenue; inputs are hypothetical.',
        [e(60,'3.2 Financial Barriers','Cybersecurity prevents revenue losses rather than direct revenue.'),e(61,'Box 10, inputs and core formula','ALE=SLE×ARO; ROSI=[ALE×mitigation-cost]/cost.')],
        calculation='100000*2=200000;200000*0.5=100000;(100000-25000)/25000=3=300%',units='USD per year; ROSI dimensionless or percent; hypothetical inputs')
    add('at21','test','text','In Appendix 2, how many expert interviews were conducted, over what period, and how were interviewees split between practitioners and academia?',
        'Eight interviews, early December 2025 through end of January 2026; seven cybersecurity practitioners and one academic researcher.',
        [e(83,'Appendix 2, Expert Interviews: Approach and Coverage','8; early Dec 2025-end Jan 2026; seven practitioners/one academic.')])
    add('at22','test','text','According to the survey Limitations section, give the three reasons results are indicative rather than statistically generalizable.',
        'Self-reporting/social-desirability bias; limited response count/representativeness; uneven reach despite three offered languages.',
        [e(77,'Limitations','Three numbered-in-prose limitations after Figure 17.',[.11,.41,.90,.62])])
    add('at23','test','text','What five safeguards does the appendix recommend for third-party remote access to vulnerable OT-enabled systems?',
        'Multi-factor authentication; time-bound credentials; monitored jump servers; session logging; clear contractual cybersecurity obligations for suppliers.',
        [e(90,'Paragraph on OT-enabled remotely operated systems','Five measures in Recommended measures include clause.')])
    add('at24','test','text','What software and named thematic-analysis procedure were used to analyze the expert interview transcripts?',
        'ATLAS.ti; Braun and Clarke\'s (2006) thematic analysis procedure.',
        [e(83,'Appendix 2, analysis paragraph','ATLAS.ti software and Braun and Clarke (2006).')])

    negatives=[
        ('ad16','dev','What exact annual dollar cost does the report give for the Gambia Ports Authority\'s weekly warning-email program?','No exact program cost is reported.',['Gambia','cost']),
        ('ad17','dev','What exact number of Cyber-SHIP Lab incidents will be prevented in 2029 according to the report?','No observed/predicted exact 2029 prevention count is provided.',['2029','Cyber-SHIP']),
        ('ad18','dev','What 95% confidence interval does Figure 4 give for its formal-policy percentage?','The donut provides percentages, not a 95% confidence interval.',['confidence interval','Figure 4']),
        ('at25','test','What exact per-student tuition fee in US dollars does the report give for training at the Cyber-SHIP Lab?','The lab description gives no tuition price.',['Cyber-SHIP','tuition','fee']),
        ('at26','test','Which laptop manufacturer is named on the personalized-training illustration in Figure 13?','No laptop manufacturer/brand is identified in the illustration.',['Figure 13','manufacturer']),
        ('at27','test','What exact annual cybersecurity budget in dollars does the report give for the Port of Singapore in 2025?','No exact annual named-port budget for Singapore in 2025 is supplied.',['Singapore','budget']),
        ('at28','test','What was the Port of Rotterdam\'s individual response to survey question 14, according to the report?','Individual named-port survey responses are not published; only aggregated data/questionnaire.',['Rotterdam','Individual responses']),
        ('at29','test','Using the report\'s observed 2025 control cost and mitigation rate for the Port of Los Angeles, calculate that port\'s actual ROSI.','ROSI formula is provided but those port-specific observed inputs are not.',['Los Angeles','ROSI']),
        ('at30','test','What 95% confidence interval is printed for the terminal-operator share in Figure 17?','The chart reports a share, not a confidence interval.',['confidence interval','Figure 17'])
    ]
    pages=__import__('json').loads((DATA/'pages.json').read_text(encoding='utf-8'))
    audit=[]
    for cid,split,question,reason,terms in negatives:
        cases.append({'id':cid,'split':split,'group':'unanswerable','question':question,'answerable':False,
            'expected_answer':'Explicitly state insufficient evidence; do not invent the requested fact.',
            'absence_reason':reason,'evidence':[],'required_pages':[]})
        audit.append({'query_id':cid,'reason':reason,'method':'Full-corpus term scan plus inspection of relevant original pages/figures; absence limited to this document.',
            'term_pages':{term:[r['page'] for r in pages if term.casefold() in r['text'].casefold()] for term in terms}})
    assert len(cases)==48 and len({q['id'] for q in cases})==48
    for split in ['dev','test']:
        counts=Counter(q['group'] for q in cases if q['split']==split)
        assert counts==({'table':3,'diagram':3,'chart':3,'multi_hop':3,'text':3,'unanswerable':3} if split=='dev' else
                       {'table':6,'diagram':5,'chart':5,'multi_hop':4,'text':4,'unanswerable':6})
    write_json(DATA/'benchmark.json',cases)
    write_json(DATA/'absence_audit.json',audit)
    write_json(DATA/'benchmark_manifest.json',{'cases':48,'dev':18,'test':30,
        'test_groups':dict(Counter(q['group'] for q in cases if q['split']=='test')),
        'benchmark_sha256':digest(DATA/'benchmark.json'),'split_note':'Authored from original pages before dev experiments; no test answers/results used for tuning. AI-authored prospective split, not externally blind.',
        'rule':'All 30 test cases count; system errors count as failures; need >=27/30, no rounding.'})
    print('Frozen prospective benchmark: 18 dev / 30 test, all five modalities + absence.',flush=True)


if __name__=='__main__':
    prepare()
