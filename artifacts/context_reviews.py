"""Explicit inspection of original-query context for five test cases per method."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.day7.data import write_json

labels = {
    'tfidf-base': {
        'q31': (1, 'Exemption present, but Italian circular antecedent in preceding chunk is missing; source line also mentions Chile.'),
        'q32': (0, 'Only table introduction retained; neither 24-hour deadline nor CSIRT recipient appears.'),
        'q33': (2, 'Extracted Figure 6 text contains Asset inventory and the proactive-approach label with source/page.'),
        'q34': (2, 'More than 50 percent across all income groups explicitly present with source/page.'),
        'q35': (2, 'No-blame/shared responsibility and prompt transparent reporting present with source/page.')
    },
    'hybrid-context': {
        'q31': (2, 'Both Italian circular introduction and NIS2 exemption retained, so antecedent and condition complete.'),
        'q32': (2, 'Table row states 24 hours and Computer Security Incident Response Teams with source/page.'),
        'q33': (2, 'Asset inventory appears in extracted proactive approach figure text with source/page.'),
        'q34': (2, 'More than 50 percent across all income groups explicitly present with source/page.'),
        'q35': (2, 'No-blame/shared responsibility and prompt transparent reporting explicitly present with source/page.')
    }
}
rows = []
for name, mapping in labels.items():
    path = ROOT / 'results/final/test' / name / 'retrieval.json'
    traces = {t['query_id']: t for t in json.loads(path.read_text(encoding='utf-8'))}
    for cid, (grade, reason) in mapping.items():
        rows.append({'config': name, 'query_id': cid, 'context_grade': grade, 'reason': reason,
            'context_ids': traces[cid]['context_ids'], 'reviewer': 'Codex AI-assisted; student confirmation pending',
            'scope': 'Original-query retrieval context, not rewritten-query agent context'})
write_json(ROOT / 'results/final/test/context_reviews.json', rows)
