"""Apply explicitly inspected Codex labels; never infer semantic support from IDs.

This is an audit convenience, not an automated judge. Labels are provisional
AI-assisted assessments and require the student's confirmation before submission.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.day7.data import write_json


def main():
    labels = json.loads((ROOT / 'artifacts/review_labels.json').read_text(encoding='utf-8'))
    cases = {q['id']: q for q in json.loads((ROOT / 'data/benchmark.json').read_text(encoding='utf-8'))}
    for key, mapping in labels.items():
        target = ROOT / 'results/final' / key
        traces = json.loads((target / 'agent.json').read_text(encoding='utf-8'))
        reviews = []
        for t in traces:
            if t['status'] == 'error':
                continue
            q = cases[t['query_id']]
            review = {'query_id': q['id'], 'reviewer': 'Codex AI-assisted content review; student confirmation pending',
                      'student_confirmed': False}
            if q['answerable']:
                if q['id'] not in mapping:
                    raise ValueError(f'Uninspected answer: {key}/{q["id"]}')
                grade, support, reason = mapping[q['id']]
                if len(support) != len(t['citations']):
                    raise ValueError(f'Citation count changed: {key}/{q["id"]}')
                review.update(answer_grade=grade, citation_support=support, reason=reason)
            else:
                # Explicit benchmark negatives were inspected corpus-wide in the
                # absence audit. Actual trace must abstain and carry no citations.
                if t['status'] != 'abstain' or t['citations']:
                    raise ValueError(f'Negative needs manual content review: {key}/{q["id"]}')
                review.update(abstention_correct=True, citation_support=[],
                              reason='Actual trace abstains without unsupported assertions; corpus absence audit checked for the requested fact.')
            reviews.append(review)
        write_json(target / 'reviews.json', reviews)


if __name__ == '__main__':
    main()
