import json
import unittest
from unittest.mock import patch
from src.web.summary import summarize, wants_summary


class SummaryTests(unittest.TestCase):
    def test_routes_vietnamese_and_english(self):
        for question in ('Tóm tắt tài liệu giúp tôi', 'Cho tôi tổng quan báo cáo', 'Summarize this report'):
            self.assertTrue(wants_summary(question))
        self.assertFalse(wants_summary('How many respondents were surveyed?'))

    def test_reads_all_pages_and_synthesizes_with_verified_quotes(self):
        pages = [{'page': n, 'text': 'Ports need cyber resilience and incident response.',
                  'image': f'p{n}.jpg'} for n in range(1, 17)]
        responses = [
            {'points': [{'page': 1, 'quote': 'Ports need cyber resilience', 'text': 'Cảng cần khả năng chống chịu.'}]},
            {'points': [{'page': 16, 'quote': 'incident response.', 'text': 'Cần ứng phó sự cố.'}]},
            {'sections': [{'text': 'Cảng cần khả năng chống chịu.', 'pages': [1]},
                          {'text': 'Cần ứng phó sự cố.', 'pages': [16]}]}]
        def complete(*args, **kwargs):
            return {'content': json.dumps(responses.pop(0))}, {'cost': .001}
        with patch('src.web.summary.read_json', return_value=pages):
            trace = summarize('Tóm tắt', {'model': 'test'}, complete, lambda e: None)
        self.assertEqual(trace['status'], 'answered')
        self.assertEqual(trace['summary_coverage']['native_pages_read'], list(range(1, 17)))
        self.assertEqual([c['page'] for c in trace['citations']], [1, 16])

    def test_rejects_fabricated_quote_and_keeps_provider_errors(self):
        pages = [{'page': 1, 'text': 'Original evidence.', 'image': 'p1.jpg'}]
        def complete(*args, **kwargs):
            return {'content': json.dumps({'points': [{'page': 1, 'quote': 'Invented evidence not in source', 'text': 'Fake'}]})}, {'cost': 0}
        with patch('src.web.summary.read_json', return_value=pages):
            self.assertEqual(summarize('Tóm tắt', {'model': 'test'}, complete, lambda e: None)['status'], 'abstain')
            def fail(*args, **kwargs):
                raise RuntimeError('OpenRouter HTTP 429')
            trace = summarize('Tóm tắt', {'model': 'test'}, fail, lambda e: None)
            self.assertEqual(trace['status'], 'error')
            self.assertIn('429', trace['events'][-1]['detail'])
