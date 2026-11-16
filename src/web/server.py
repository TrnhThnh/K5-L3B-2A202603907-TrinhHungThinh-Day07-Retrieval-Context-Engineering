"""Loopback-only web UI. Run: python -m src.web.server --env-file PATH."""
import argparse
import copy
import json
import mimetypes
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
STATIC = ROOT / 'src/web/static'
RUN = ROOT / 'results/advanced/run-05'
JOBS = {}
LOCK = threading.Lock()
TOKEN = secrets.token_urlsafe(32)
VIETNAMESE_RESPONSE = '''User-facing language: Vietnamese (tiếng Việt).
Write finish.answer in natural Vietnamese, including abstention explanations, regardless
of the question language. Write citation.support in Vietnamese. Preserve exact numbers,
units, proper names and acronyms; optionally explain technical terms in Vietnamese.
Keep citation.label as the original printed English heading/Figure/Table/Box so evidence
can be located. Continue using English search queries for this English source document.
Do not translate tool names, JSON keys, source IDs or evidence text.'''


def vietnamese_messages(messages):
    """Apply the web language preference without changing the frozen benchmark agent."""
    localized = copy.deepcopy(messages)
    localized.insert(0, {'role': 'system', 'content': VIETNAMESE_RESPONSE})
    return localized


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def options(body):
    method = body.get('method', 'hybrid')
    top_k = body.get('top_k', 10)
    if method not in {'tfidf', 'dense', 'hybrid'} or type(top_k) is not int or not 1 <= top_k <= 30:
        raise ValueError('Invalid retrieval options')
    return method, top_k


def execute(job, question, method='hybrid', top_k=10, compare=False):
    # Serialize access to the shared model adapter and embedding model.
    from src.advanced import agent
    original = agent.complete
    def emit(event):
        job['events'].append(event)
    def complete(messages, *args, **kwargs):
        message, usage = original(vietnamese_messages(messages), *args, **kwargs)
        emit({'event': 'model', 'message': message, 'usage': usage})
        return message, usage
    try:
        from src.advanced.store import Retriever
        from src.advanced.citation_alignment import align_folder
        from src.web.summary import wants_summary, summarize
        is_summary = not compare and wants_summary(question)
        config = {**read(RUN / 'selection.json')['config'], 'top_k': top_k, 'method': method,
                  'id': f'web-vi-{method}-k{top_k}', 'response_language': 'vi'}
        if is_summary:
            job['phase'] = 'Đang đọc các phần của báo cáo và tổng hợp tiếng Việt'
            trace = summarize(question, config, complete, emit)
            folder = ROOT / 'results/web' / job['id']
            folder.mkdir(parents=True, exist_ok=True)
            (folder / 'traces.json').write_text(json.dumps([trace], ensure_ascii=False, indent=2), encoding='utf-8')
            align_folder(folder)
            trace = read(folder / 'traces.json')[0]
            job.update(trace=trace, events=trace['events'], phase='Hoàn tất', done=True)
            return
        job['phase'] = 'Đang nạp embedding và kết nối pgvector'
        retriever = Retriever()
        from src.day7.retrieval import build_retriever
        from src.advanced.store import STRATEGY
        methods = {name: build_retriever(name, retriever.rows, retriever.store, retriever.embedder,
                   STRATEGY, candidates=40) for name in ('tfidf', 'dense', 'hybrid')}
        if compare:
            comparisons = []
            for name, engine in methods.items():
                started = time.perf_counter()
                rows = engine.search(question, top_k=top_k)
                comparisons.append({'method': name, 'top_k': top_k, 'results': rows,
                    'elapsed_ms': (time.perf_counter()-started)*1000})
            output = {'question': question, 'comparisons': comparisons,
                'note': 'Same original query, corpus and top-k; retrieval only, no LLM/API cost. Scores have different scales; no gold accuracy inferred.'}
            folder = ROOT / 'results/web' / job['id']
            folder.mkdir(parents=True, exist_ok=True)
            (folder / 'comparison.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
            job.update(comparison=output, done=True, phase='So sánh hoàn tất')
            return
        def traced_search(query, top_k=12):
            rows = methods[method].search(query, top_k=top_k)
            emit({'event': 'search', 'query': query, 'results': rows})
            return rows
        retriever.search = traced_search
        agent.complete = complete
        job['phase'] = 'Agent đang tìm và đọc bằng chứng'
        config = {**read(RUN / 'selection.json')['config'], 'top_k': top_k, 'method': method,
                  'id': f'web-vi-{method}-k{top_k}', 'response_language': 'vi'}
        trace = agent.run(question, retriever, config)
        folder = ROOT / 'results/web' / job['id']
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'traces.json').write_text(json.dumps([trace], ensure_ascii=False, indent=2), encoding='utf-8')
        align_folder(folder)
        trace = read(folder / 'traces.json')[0]
        job.update(trace=trace, events=trace['events'], phase='Hoàn tất', done=True)
    except Exception as exc:
        # Never expose environment values or arbitrary dependency exceptions.
        job.update(done=True, phase='Không thể hoàn tất', error=type(exc).__name__ + ': Kiểm tra PostgreSQL, môi trường và kết nối provider.')
    finally:
        agent.complete = original
        LOCK.release()


class Handler(BaseHTTPRequestHandler):
    def allowed_host(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def reply(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if not self.allowed_host():
            return self.reply({'error': 'Forbidden host'}, 403)
        path = urlparse(self.path).path
        if path == '/api/state':
            return self.reply({'token': TOKEN, 'config': read(RUN / 'selection.json')['config'],
                'index': read(ROOT / 'data/advanced/index_manifest.json'),
                'first': read(RUN / 'test/vision-lite/summary.json'),
                'repeat': read(RUN / 'repeat-01/test/vision-lite/summary.json'),
                'quota_snapshot': read(ROOT / 'results/advanced/key-quota-final.json')})
        if path == '/api/replay':
            traces = read(RUN / 'repeat-01/test/vision-lite/traces.json')
            trace = next(t for t in traces if t['status'] == 'answered')
            return self.reply({'trace': trace, 'events': trace['events'], 'done': True, 'replay': True})
        if path.startswith('/api/jobs/'):
            job = JOBS.get(path.rsplit('/', 1)[-1])
            return self.reply(copy.deepcopy(job) if job else {'error': 'Không tìm thấy lượt chạy'}, 200 if job else 404)
        if path.startswith('/pages/'):
            name = path.rsplit('/', 1)[-1]
            if len(name) != 8 or not name.startswith('p') or not name[1:4].isdigit() or not name.endswith('.jpg'):
                return self.reply({'error': 'Invalid page'}, 404)
            target = ROOT / 'data/advanced/pages' / name
        elif path == '/source.pdf':
            target = ROOT / 'data/advanced/source.pdf'
        elif path in {'/', '/app.js', '/style.css'}:
            target = STATIC / ('index.html' if path == '/' else path[1:])
        else:
            return self.reply({'error': 'Not found'}, 404)
        if not target.is_file():
            return self.reply({'error': 'Not found'}, 404)
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(str(target))[0] or 'application/octet-stream')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(target.read_bytes())

    def do_POST(self):
        if not self.allowed_host() or self.path not in {'/api/ask', '/api/compare'} or self.headers.get('X-Session-Token') != TOKEN:
            return self.reply({'error': 'Forbidden'}, 403)
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16000:
                raise ValueError()
            body = json.loads(self.rfile.read(size))
            question = body['question'].strip()
            method, top_k = options(body)
            if not question or len(question) > 3000:
                raise ValueError()
        except (ValueError, KeyError, TypeError, AttributeError):
            return self.reply({'error': 'Câu hỏi 1–3000 ký tự; top-k 1–30; method tfidf/dense/hybrid.'}, 400)
        if not LOCK.acquire(blocking=False):
            return self.reply({'error': 'Agent đang xử lý một câu hỏi. Hãy chờ hoàn tất.'}, 409)
        jid = secrets.token_hex(12)
        job = {'id': jid, 'events': [], 'done': False, 'phase': 'Đang khởi động', 'started': time.time()}
        # Keep memory bounded; raw traces are persisted separately on disk.
        for old in list(JOBS)[:-19]:
            if JOBS[old]['done']:
                del JOBS[old]
        JOBS[jid] = job
        threading.Thread(target=execute, args=(job, question, method, top_k, self.path == '/api/compare'), daemon=True).start()
        self.reply({'id': jid}, 202)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--port', type=int, default=8070)
    args = parser.parse_args()
    from src.day7.runtime import load_environment
    load_environment(args.env_file)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Agent UI: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
