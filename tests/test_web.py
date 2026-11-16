"""HTTP boundary tests; no database or paid provider calls."""
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from src.web.server import Handler, options


class WebTests(unittest.TestCase):
    def test_top_k_five_and_methods(self):
        for method in ('tfidf', 'dense', 'hybrid'):
            self.assertEqual(options({'method': method, 'top_k': 5}), (method, 5))
        for bad in (0, 31, True, '5'):
            with self.assertRaises(ValueError):
                options({'top_k': bad})
        with self.assertRaises(ValueError):
            options({'method': 'unknown'})

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_replay_has_real_citations_and_no_paid_call(self):
        with urllib.request.urlopen(self.base + '/api/replay') as response:
            body = json.load(response)
        self.assertTrue(body['replay'])
        self.assertTrue(body['trace']['citations'])
        self.assertTrue(body['events'])

    def test_no_repo_or_secret_file_serving(self):
        for path in ['/.env', '/src/advanced/common.py', '/pages/../../.env']:
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(self.base + path)
            self.assertEqual(ctx.exception.code, 404)

    def test_post_requires_session_token(self):
        request = urllib.request.Request(self.base + '/api/ask', data=b'{"question":"test"}', method='POST')
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(request)
        self.assertEqual(ctx.exception.code, 403)

    def test_rebinding_host_rejected(self):
        request = urllib.request.Request(self.base + '/api/state', headers={'Host': 'attacker.example'})
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(request)
        self.assertEqual(ctx.exception.code, 403)
