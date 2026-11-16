"""Persist all useful page text and visual descriptions in an isolated pgvector strategy."""
import argparse
import os
from pathlib import Path
from .common import DATA, ROOT, SOURCE_ID, read_json
from src.day7.data import digest, write_json
from src.day7.retrieval import LexicalRetriever, HybridRetriever, DenseRetriever
from src.day7.runtime import load_environment

STRATEGY = 'ADVANCED_M1'


def build_rows():
    from PIL import Image
    rows, coverage = [], []
    catalog = {r['page']: r for r in read_json(DATA / 'visual_catalog.json')}
    crops = DATA / 'regions'
    crops.mkdir(exist_ok=True)
    for page in read_json(DATA / 'pages.json'):
        n = page['page']
        visual = catalog[n]
        if visual['status'] != 'ok':
            coverage.append({'page': n, 'status': 'vision_error_native_text_retained'})
        else:
            coverage.append({'page': n, 'status': visual.get('page_class', 'content'),
                             'visual_regions': len(visual['regions'])})
        base = {'source_id': SOURCE_ID, 'source': 'data/advanced/source.pdf', 'page': n}
        native = page['text']
        # Index every nonempty native page, including appendices/reference material.
        for start in range(0, len(native), 900):
            text = native[start:start + 1100].strip()
            if text:
                rows.append({**base, 'id': f'adv:p{n:03}:t{start//900:02}', 'text': text,
                    'metadata': {'kind': 'text', 'bbox': [0,0,1,1], 'label': 'Native page text',
                                 'image': page['image'], 'start_char': start, 'end_char': start+len(text)}})
        if visual['status'] != 'ok':
            continue
        summary = visual['page_summary'].strip()
        if summary and visual.get('page_class') not in {'blank', 'decorative'}:
            rows.append({**base, 'id': f'adv:p{n:03}:summary', 'text': summary,
                'metadata': {'kind': 'summary', 'bbox': [0,0,1,1], 'label': 'Machine page summary; verify original',
                             'image': page['image']}})
        image = Image.open(ROOT / page['image'])
        for index, region in enumerate(visual['regions']):
            rid = f'adv:p{n:03}:v{index:02}'
            box = region['bbox']
            crop = crops / f'p{n:03}-v{index:02}.jpg'
            image.crop((int(box[0]*image.width), int(box[1]*image.height),
                        int(box[2]*image.width), int(box[3]*image.height))).save(crop, quality=90)
            rows.append({**base, 'id': rid, 'text': f"{region.get('label','')}\n{region['description']}",
                'metadata': {'kind': region['kind'], 'bbox': box, 'label': region.get('label', ''),
                    'image': page['image'], 'crop': str(crop.relative_to(ROOT)).replace('\\','/'),
                    'extraction_status': 'machine_description_not_gold'}})
    write_json(DATA / 'index_rows.json', rows)
    write_json(DATA / 'coverage.json', coverage)
    return rows


def index():
    from vendor.day06.embeddings import MyEmbedder
    from vendor.day06.models import Chunk
    from vendor.day06.store import PgVectorStore
    rows = build_rows()
    model = 'sentence-transformers/all-MiniLM-L6-v2'
    embedder = MyEmbedder(model, local_files_only=True)
    store = PgVectorStore(os.environ['DATABASE_URL'], embedder.dimensions)
    store.create_schema()
    chunks = [Chunk(r['id'], r['source_id'], r['source'], r['page'], r['text'], r['metadata']) for r in rows]
    store.upsert(STRATEGY, chunks, embedder.embed_documents([r['text'] for r in rows]))
    write_json(DATA / 'index_manifest.json', {'strategy': STRATEGY, 'rows': len(rows),
        'pages': len({r['page'] for r in rows}), 'model': model, 'dimensions': embedder.dimensions,
        'source_sha256': digest(DATA / 'source.pdf'), 'index_rows_sha256': digest(DATA / 'index_rows.json'),
        'visual_catalog_sha256': digest(DATA / 'visual_catalog.json'), 'service_cost_usd': 0})
    print(f'Indexed {len(rows)} rows in isolated {STRATEGY}', flush=True)


class Retriever:
    def __init__(self):
        from vendor.day06.embeddings import MyEmbedder
        from vendor.day06.store import PgVectorStore
        self.rows = read_json(DATA / 'index_rows.json')
        self.by_id = {r['id']: r for r in self.rows}
        self.embedder = MyEmbedder('sentence-transformers/all-MiniLM-L6-v2', local_files_only=True)
        self.store = PgVectorStore(os.environ['DATABASE_URL'], self.embedder.dimensions)
        self.hybrid = HybridRetriever(DenseRetriever(self.store, self.embedder, STRATEGY), LexicalRetriever(self.rows), candidates=40)

    def search(self, query, top_k=12):
        return self.hybrid.search(query, top_k=top_k)

    def page_regions(self, pages):
        return [r for r in self.rows if r['page'] in pages and r['metadata']['kind'] not in {'text','summary'}]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--env-file', type=Path)
    args = parser.parse_args()
    load_environment(args.env_file)
    index()
