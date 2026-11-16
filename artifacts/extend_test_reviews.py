"""Content labels for all final test answers, inspected after selection was frozen."""
import json
from pathlib import Path

p = Path(__file__).with_name('review_labels.json')
labels = json.loads(p.read_text(encoding='utf-8'))
labels['test/tfidf-base'] = {
    'q31': [0,[],'False abstention; exemption exists in corpus but agent context was insufficient.'],
    'q32': [2,[True],'Cited table explicitly gives within 24 hours and CSIRTs.'],
    'q33': [2,[True],'Figure text explicitly lists Asset inventory in proactive approach.'],
    'q34': [2,[True],'More than 50 percent across all income groups explicitly supported.'],
    'q35': [2,[True,True],'No-blame/shared-responsibility reporting and collective-defense interpretation supported.']
}
labels['test/hybrid-context'] = {
    'q31': [2,[True],'NIS2-covered facilities exemption supported; neighboring paragraph in context establishes Italian circular antecedent.'],
    'q32': [2,[True],'24-hour report and recipient CSIRTs explicitly supported by table.'],
    'q33': [2,[True],'Asset inventory explicitly supported by extracted Figure 6 text.'],
    'q34': [2,[True],'More than 50 percent across income groups supported.'],
    'q35': [2,[True,True],'No-blame culture/shared responsibility and collective defense supported by both passages.']
}
p.write_text(json.dumps(labels, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
