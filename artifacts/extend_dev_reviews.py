"""Explicit labels from reading dense and RRF answers plus their cited passages."""
import json
from pathlib import Path

p = Path(__file__).with_name('review_labels.json')
labels = json.loads(p.read_text(encoding='utf-8'))

labels['dev/dense-base'] = {
    'q01': [1,[True],'Governance-allocation explanation supported, but omits collective responsibility and cascading risks.'],
    'q02': [0,[True],'Supported incident-analysis description does not answer evidence sources of the report.'],
    'q03': [2,[True],'Alternative Table 2 explicitly gives 48 and 44.04%.'],
    'q04': [2,[True],'No binding global framework explicitly supported.'],
    'q05': [0,[True],'Protective controls and entry points do not answer what inventory ports should maintain.'],
    'q06': [1,[False,False],'Core IT/OT link correct; extra safety/severity conclusion extends the truncated paragraph, second citation is only a fragment.'],
    'q07': [2,[True],'Buy-in, accountability, coordination and minimum levels all explicitly supported.'],
    'q08': [2,[True],'Assessment and approved security plan obligations supported.'],
    'q09': [1,[True],'General governance benefits supported, but missing translation to enforceable obligations.'],
    'q10': [0,[],'False abstention on answerable 65-percent question.'],
    'q11': [2,[False,True],'Essential governance role supported by page 35; title-only page is not evidence.'],
    'q12': [1,[True],'Operational-resilience linkage supported but does not define prevent/respond/recover.'],
    'q13': [2,[True],'Scan purpose and examples explicitly supported.'],
    'q14': [2,[True],'April 2024, 40 participants and cross-region exercise supported.'],
    'q15': [0,[],'False abstention; several legitimate progress indicators exist.'],
    'q16': [1,[True,False],'Practice/testing recommendation supported, but not the full observed readiness gap; regulatory continuity passage does not establish the claim.'],
    'q17': [2,[True,True],'All four response options supported; second passage also supports annual/no formal training frequencies.'],
    'q18': [1,[False,True],'Interpretation/net savings supported, but core definition of avoided loss relative to control cost omitted; title adds no evidence.'],
    'q19': [2,[True],'CRC launch date and sharing/collective-defense purpose supported.'],
    'q21': [2,[True],'Multiple explicit steering committee functions supplied.'],
    'q22': [2,[True],'Significant system changes explicitly trigger scans.'],
    'q23': [2,[True],'Escape Room and shows supported in training case study.'],
    'q24': [1,[True],'Reusing governance supported but specific four integration areas missing.'],
    'q25': [1,[True],'Languages present in alternative source; survey dates omitted.'],
    'q26': [0,[],'False abstention: SOC definition exists in corpus.'],
    'q27': [2,[True],'Ship bridge replication and realistic IT/OT scenarios supported.'],
    'q28': [2,[False,True],'Valid alternative safeguards in ownership/confidentiality/access passage; challenges passage alone is not a recommendation.'],
    'q29': [2,[True],'Ownership, confidentiality and need-to-know access supported.'],
    'q30': [1,[False],'Three correct DoS targets, but incorrectly treats communication interception as another DoS function.']
}

labels['dev/hybrid-rrf'] = {
    'q01': [1,[True],'Governance allocation supported but collective responsibility and cascade explanation missing.'],
    'q02': [0,[True],'Incident analysis supported, but does not identify report survey/interviews/regulatory mapping.'],
    'q03': [2,[True],'Alternative Table 2 gives correct 48 and 44.04%.'],
    'q04': [2,[True],'No binding global framework explicitly supported.'],
    'q05': [1,[True],'Live IT/OT inventories correct; does not explicitly include regular vulnerability scans.'],
    'q06': [1,[False],'Main IT/OT connection supported, but additional severity claim extends beyond retained truncated source.'],
    'q07': [2,[True],'All four governance benefits explicitly supported.'],
    'q08': [2,[True],'Assessment and security plan obligations supported.'],
    'q09': [1,[True],'General governance role supported but enforceable-obligation mechanism missing.'],
    'q10': [2,[True],'65-percent mandatory notification figure supported.'],
    'q11': [2,[True,False],'Governance centrality supported; extra title citation has no factual support.'],
    'q12': [0,[],'False abstention on answerable resilience definition.'],
    'q13': [2,[True],'Vulnerability scan purpose and examples explicitly supported.'],
    'q14': [2,[True],'Tabletop exercise, April 2024, 40 participants and cross-border coordination supported.'],
    'q15': [0,[],'False abstention on answerable indicator question.'],
    'q16': [1,[False],'Recommendation to practice does not directly establish observed lack of integration/readiness.'],
    'q17': [1,[True],'Reports frequency findings rather than all requested survey response options.'],
    'q18': [1,[False,True],'Net savings interpretation correct but core avoided-loss/control-cost definition missing; title unsupported.'],
    'q19': [2,[True],'Launch date and CRC purpose supported.'],
    'q20': [1,[True],'Collective benefits relevant, but cross-border societal-economic rationale omitted.'],
    'q21': [2,[True],'Several valid committee functions explicitly supported.'],
    'q22': [2,[True],'System changes trigger scans, explicitly stated.'],
    'q23': [2,[True],'Escape Room and shows supported.'],
    'q24': [1,[True],'Existing governance framework supported but specific integration areas missing.'],
    'q25': [1,[True],'Languages supported; dates missing.'],
    'q26': [2,[True],'Monitoring/detection/response in real time and escalation channels explicitly supported.'],
    'q27': [2,[True],'Physical ship bridge and realistic IT/OT incidents supported.'],
    'q28': [2,[True,False],'Ownership/confidentiality/access rules valid alternative safeguards; challenges passage does not provide the recommendation.'],
    'q29': [2,[True],'All requested governance rules supported.'],
    'q30': [1,[False],'Correct DoS targets, but conflates separate communication-interception vector.']
}
p.write_text(json.dumps(labels, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
