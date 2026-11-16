"""Create reproducible Day07 benchmark from Day06 labels without tuning on test."""
from .data import ROOT, load_chunks, read_jsonl, validate_cases, write_json, digest


def prepare():
    original = read_jsonl(ROOT / 'data/day06/questions_original.jsonl')
    cases = []
    for q in original:
        sources = q.get('acceptable_sources', [q['gold_source_id']])
        pages = q.get('acceptable_pages', [q['gold_page']])
        cases.append({'id': q['id'], 'split': 'dev', 'question': q['question'],
            'answerable': True, 'expected_answer': q['expected_answer'],
            'gold': [{'source_id': source, 'page': page, 'evidence': q['evidence_quote']}
                     for source in sources for page in pages],
            # Existing Day06 filters without explicit category in the question are
            # deliberately not used: no gold-derived filtering.
            'filter': {}, 'provenance': 'Day06 question; prior test now exploratory dev after protocol debugging'})
    # Frozen before final run; new passages, no ranking/agent results inspected.
    final_test = [
        ('q31', 28, 'According to the report, which Italian port facilities are exempt from the circular\'s additional requirements to avoid regulatory duplication?',
         'Port facilities already covered by the EU NIS2 Directive are exempt.',
         'the circular exempts port facilities already covered by'),
        ('q32', 31, 'In Table 1, how quickly does the EU NIS2 example say significant incidents should be reported, and to whom?',
         'Within 24 hours to Computer Security Incident Response Teams.',
         'report significant incidents within 24'),
        ('q33', 42, 'In Figure 6, what inventory activity is listed in the continuous and proactive cyber risk management approach?',
         'Asset inventory.', 'Asset inventory'),
        ('q34', 60, 'According to the financial barriers discussion, for what share of surveyed ports is funding cybersecurity an important barrier?',
         'More than 50 percent of ports across all income groups.',
         'important barrier for more than 50 percent of ports across all income groups.'),
        ('q35', 73, 'In the concluding barriers recommendations, which organizational culture is encouraged for raising concerns and reporting incidents?',
         'A cooperative, no-blame culture with shared responsibility for prompt and transparent reporting.',
         'a cooperative, no-blame culture where everyone shares responsibility')
    ]
    for cid, page, question, answer, quote in final_test:
        cases.append({'id': cid, 'split': 'test', 'question': question, 'answerable': True,
            'expected_answer': answer, 'gold': [{'source_id': 'world-bank-cybersecurity-ports-2026',
            'page': page, 'evidence': quote}], 'filter': {},
            'provenance': 'Prospective Day07 test after citation-format fix, frozen before final benchmark; AI-authored, not externally blind'})
    negative = [
        ('u01', 'dev', 'What is the PostgreSQL password used by the Port of Los Angeles Cyber Resilience Center?',
         'The corpus discusses the center but provides no production database credentials.', ['password', 'postgresql']),
        ('u02', 'dev', 'What is the exact 2030 cybersecurity budget in US dollars for the Port of Antwerp-Bruges?',
         'The report is dated 2026; it discusses training and financing but contains no exact 2030 budget for this port.', ['2030', 'antwerp', 'budget']),
        ('u03', 'dev', 'What is the private API key used by the Maritime and Port Authority of Singapore SOC?',
         'The corpus discusses Singapore exercises and SOCs but publishes no private API keys.', ['api key', 'private key', 'singapore']),
        ('u04', 'dev', 'What was the exact number of ransomware incidents at the Port of Los Angeles in calendar year 2035?',
         'The 2026 report has no observed incident count for future calendar year 2035.', ['2035', 'los angeles', 'ransomware']),
        ('u05', 'test', 'What exact cybersecurity insurance premium in US dollars did the Port of Barcelona pay in 2034?',
         'The 2026 report does not provide an observed 2034 insurance premium for Barcelona.', ['2034', 'barcelona', 'premium']),
        ('u06', 'test', 'What is the exact 2036 percentage reduction in cyber incidents achieved by the Cyber-SHIP Lab?',
         'The corpus describes the lab but contains no observed 2036 incident-reduction percentage.', ['2036', 'cyber-ship', 'reduction'])
    ]
    raw_pages = read_jsonl(ROOT / 'data/day06/pages.jsonl')
    audit = []
    for cid, split, question, reason, terms in negative:
        cases.append({'id': cid, 'split': split, 'question': question, 'answerable': False,
                      'expected_answer': 'Không đủ bằng chứng để trả lời.', 'gold': [],
                      'filter': {}, 'absence_reason': reason})
        audit.append({'query_id': cid, 'absence_reason': reason,
                      'scope': 'Corpus-wide term scan across all 80 pages; specific requested facts checked against matching passages and report date. Term hits alone are not proof of absence.',
                      'term_pages': {term: [p['page'] for p in raw_pages if term in p['text'].casefold()] for term in terms},
                      'limitation': 'Absence applies only to this corpus; not a claim about all external sources.'})
    chunks = load_chunks()
    validate_cases(cases, chunks)
    write_json(ROOT / 'data/benchmark.json', cases)
    write_json(ROOT / 'data/absence_audit.json', audit)
    write_json(ROOT / 'data/day06/provenance.json', {
        'repo': 'https://github.com/TrnhThnh/K5-L3B-Day06-2A202603907-DataIngestionEngineering',
        'commit': 'bf21bc0b5d7ab8a7ae4902c0905da5dfabd3469c',
        'pages_sha256': digest(ROOT / 'data/day06/pages.jsonl'),
        'chunks': len(chunks), 'chunking': 'Day06 B: by_paragraph(max_size=1000)',
        'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2', 'dimensions': 384,
        'split_note': 'q01-q30 and u01-u04 dev; q26-q30/u03-u04 demoted after exploratory run-01. q31-q35/u05-u06 prospective test frozen after citation-format fix and before final benchmark. Author knows corpus; not externally blind.',
        'dev': 34, 'test': 7})
    return {'chunks': len(chunks), 'cases': len(cases), 'dev': 34, 'test': 7}


if __name__ == '__main__':
    print(prepare())
