"""Offline contract tests; never reported as real model benchmark quality."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src.day7.agent import run_agent
from src.day7.data import load_chunks, pack_context, ROOT, validate_cases
from src.day7.retrieval import HybridRetriever, LexicalRetriever
from src.day7.benchmark import load_selection


def chunk(cid, score=1, text='Evidence'):
    return {'id': cid, 'score': score, 'text': text, 'source_id': 's',
            'source': 's.pdf', 'page': 1, 'metadata': {'category': 'policy'}}


class FakeClient:
    model = 'offline-test-only'

    def __init__(self, calls):
        self.calls = iter(calls)

    def complete(self, messages):
        name, args = next(self.calls)
        return {'tool_calls': [{'id': 'test', 'function': {'name': name, 'arguments': json.dumps(args)}}]}, {}


class FixedRetriever:
    def __init__(self, rows):
        self.rows = rows

    def search(self, query, *, filters=None, top_k=3):
        return self.rows[:top_k]


class Day7Tests(unittest.TestCase):
    def test_real_corpus_and_benchmark_resolve(self):
        chunks = load_chunks()
        self.assertEqual(len(chunks), 212)
        cases = json.loads((ROOT / 'data/benchmark.json').read_text(encoding='utf-8'))
        validate_cases(cases, chunks)
        self.assertEqual(sum(q['split'] == 'test' for q in cases), 7)

    def test_rrf_rewards_agreement_and_applies_filter(self):
        dense = FixedRetriever([chunk('a'), chunk('b')])
        lexical = FixedRetriever([chunk('b'), chunk('c')])
        rows = HybridRetriever(dense, lexical).search('query', top_k=3)
        self.assertEqual(rows[0]['id'], 'b')
        self.assertEqual(rows[0]['component_ranks'], {'dense': 2, 'tfidf': 1})
        actual = LexicalRetriever([chunk('a')])
        self.assertEqual(actual.search('Evidence', filters={'category': 'practice'}), [])

    def test_context_reranks_old_evidence_and_keeps_budget(self):
        a, b = chunk('a', 0.1), chunk('b', 0.9)
        full, _ = pack_context([a], 200)
        context, ids = pack_context([a, b, b], len(full))
        self.assertEqual(ids, ['b'])
        self.assertLessEqual(len(context), len(full))

    def test_answer_requires_search_and_all_inline_citations(self):
        finish = ('finish', {'status': 'answered', 'answer': 'Evidence [a]', 'citations': ['a']})
        self.assertEqual(run_agent('q', FakeClient([finish]), FixedRetriever([chunk('a')]))['reason'], 'no_retrieval')
        search = ('search', {'query': 'evidence'})
        good = run_agent('q', FakeClient([search, finish]), FixedRetriever([chunk('a')]))
        self.assertEqual(good['status'], 'answered')
        bad_finish = ('finish', {'status': 'answered', 'answer': 'Evidence [a] [invented]', 'citations': ['a']})
        bad = run_agent('q', FakeClient([search, bad_finish]), FixedRetriever([chunk('a')]))
        self.assertEqual(bad['reason'], 'invalid_citations')

    def test_outage_is_error_not_abstention(self):
        class Outage:
            def search(self, *args, **kwargs):
                raise ConnectionError('secret postgres URL must not leak')
        trace = run_agent('q', FakeClient([('search', {'query': 'q'})]), Outage())
        self.assertEqual(trace['status'], 'error')
        self.assertNotIn('secret postgres', json.dumps(trace))

    def test_structured_citations_are_rendered_but_unknown_ids_rejected(self):
        search = ('search', {'query': 'evidence'})
        finish = ('finish', {'status': 'answered', 'answer': 'Evidence', 'citations': ['[a]']})
        trace = run_agent('q', FakeClient([search, finish]), FixedRetriever([chunk('a')]))
        self.assertEqual(trace['status'], 'answered')
        self.assertIn('[a]', trace['answer'])
        self.assertEqual(trace['citations'], ['a'])
        wrong = ('finish', {'status': 'answered', 'answer': 'Evidence', 'citations': ['unknown']})
        trace = run_agent('q', FakeClient([search, wrong]), FixedRetriever([chunk('a')]))
        self.assertEqual(trace['reason'], 'invalid_citations')

    def test_selection_rejects_modified_benchmark(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'selection.json'
            path.write_text(json.dumps({'benchmark_sha256': 'old', 'configs_sha256': 'old'}), encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'changed'):
                load_selection(path)

    def test_search_limit_and_real_abstention(self):
        search = ('search', {'query': 'q'})
        trace = run_agent('q', FakeClient([search, search]), FixedRetriever([]), max_searches=1)
        self.assertEqual(trace['reason'], 'search_limit')
        trace = run_agent('q', FakeClient([search, ('finish', {'status': 'abstain', 'answer': 'no', 'citations': []})]), FixedRetriever([]))
        self.assertEqual(trace['status'], 'abstain')


if __name__ == '__main__':
    unittest.main()
