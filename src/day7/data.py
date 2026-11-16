"""Day06 import with original IDs, source pages and paragraph boundaries."""
import hashlib
import json
import unicodedata
from pathlib import Path
from vendor.day06.models import DocumentPage
from vendor.day06.chunking import by_paragraph

ROOT = Path(__file__).resolve().parents[2]


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(text):
    return ' '.join(unicodedata.normalize('NFKC', text).casefold().split())


def load_chunks(path=ROOT / 'data/day06/pages.jsonl'):
    chunks = []
    for row in read_jsonl(path):
        text = unicodedata.normalize('NFKC', row['text']).replace('\u00ad', '')
        text = '\n'.join(' '.join(line.split()) for line in text.splitlines()).strip()
        page = DocumentPage(row['document_id'], row['source'], int(row['page']), text,
                            {k: v for k, v in row.items() if k not in {'document_id', 'source', 'page', 'text', 'char_count'}})
        for c in by_paragraph(page, 1000):
            chunks.append({'id': c.chunk_id, 'source_id': c.document_id, 'source': c.source,
                           'page': c.page, 'text': c.text, 'metadata': c.metadata})
    return chunks


def evidence_hit(chunk, gold):
    return any(chunk['source_id'] == g['source_id'] and chunk['page'] == g['page']
               and norm(g['evidence']) in norm(chunk['text']) for g in gold)


def validate_cases(cases, chunks):
    if len({q['id'] for q in cases}) != len(cases):
        raise ValueError('Duplicate query IDs')
    for split, minimum in [('dev', 15), ('test', 5)]:
        subset = [q for q in cases if q['split'] == split]
        if sum(q['answerable'] for q in subset) < minimum or sum(not q['answerable'] for q in subset) < 2:
            raise ValueError(f'Insufficient {split} benchmark')
    for q in cases:
        if q['split'] not in {'dev', 'test'} or not q['question'].strip():
            raise ValueError('Invalid query')
        if q['answerable']:
            if not q.get('gold') or not any(evidence_hit(c, q['gold']) for c in chunks):
                raise ValueError(f"Evidence missing from paragraph chunks: {q['id']}")
        elif not q.get('absence_reason'):
            raise ValueError(f"Missing absence audit: {q['id']}")


def pack_context(candidates, budget):
    """Re-rank all accumulated candidates, deduplicate; preserve whole chunks."""
    unique = {}
    for c in candidates:
        old = unique.get(c['id'])
        if old is None or c['score'] > old['score']:
            unique[c['id']] = c
    blocks, ids = [], []
    for c in sorted(unique.values(), key=lambda c: (-c['score'], c['id'])):
        block = f"[{c['id']} | {c['source']} | page {c['page']}]\n{c['text']}"
        if len('\n\n'.join(blocks + [block])) <= budget:
            blocks.append(block)
            ids.append(c['id'])
    return '\n\n'.join(blocks), ids
