"""Explicit environment loading and read-only compatibility checks."""
import os
from pathlib import Path
from .data import ROOT, digest, load_chunks, write_json


def load_environment(path=None):
    from dotenv import load_dotenv
    load_dotenv(Path(path) if path else ROOT / '.env', override=False)


def connect_dense(chunks):
    import psycopg
    from vendor.day06.embeddings import MyEmbedder
    from vendor.day06.store import PgVectorStore
    database = os.getenv('DATABASE_URL')
    model = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    if not database:
        raise RuntimeError('Missing DATABASE_URL')
    if model != 'sentence-transformers/all-MiniLM-L6-v2':
        raise RuntimeError('Day06 provenance requires all-MiniLM-L6-v2; rebuild a new index explicitly for other models')
    embedder = MyEmbedder(model, local_files_only=os.getenv('EMBEDDING_LOCAL_ONLY', 'true').lower() in {'true', '1', 'yes'})
    if embedder.dimensions != 384:
        raise RuntimeError('Day06 expected 384-dimensional embeddings')
    store = PgVectorStore(database, embedder.dimensions)
    strategy = os.getenv('DAY6_STRATEGY', 'B')
    with psycopg.connect(database, connect_timeout=8) as conn:
        rows = conn.execute('SELECT chunk_id,document_id,source,page,content,metadata,vector_dims(embedding) FROM day6_chunks WHERE strategy=%s', (strategy,)).fetchall()
    expected = {c['id']: c for c in chunks}
    if len(rows) != len(expected) or {r[0] for r in rows} != set(expected):
        raise RuntimeError('Day06 B corpus mismatch or missing. Use init-index to rebuild isolated DAY7_B')
    for cid, doc, source, page, text, metadata, dimensions in rows:
        c = expected[cid]
        if (doc, source, page, text, metadata, dimensions) != (c['source_id'], c['source'], c['page'], c['text'], c['metadata'], 384):
            raise RuntimeError('Day06 index content/metadata/dimension mismatch')
    return store, embedder, strategy


def initialize_index():
    """Explicit rebuild, only the isolated DAY7_B strategy is ever replaced."""
    import psycopg
    from vendor.day06.embeddings import MyEmbedder
    from vendor.day06.models import Chunk
    from vendor.day06.store import PgVectorStore
    database = os.getenv('DATABASE_URL')
    if not database:
        raise RuntimeError('Missing DATABASE_URL')
    model = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
    if model != 'sentence-transformers/all-MiniLM-L6-v2':
        raise RuntimeError('Use original Day06 embedding model')
    embedder = MyEmbedder(model, local_files_only=os.getenv('EMBEDDING_LOCAL_ONLY', 'true').lower() in {'true', '1', 'yes'})
    chunks = load_chunks()
    store = PgVectorStore(database, embedder.dimensions)
    store.create_schema()
    rows = [Chunk(c['id'], c['source_id'], c['source'], c['page'], c['text'], c['metadata']) for c in chunks]
    store.upsert('DAY7_B', rows, embedder.embed_documents([c['text'] for c in chunks]))
    with psycopg.connect(database, connect_timeout=8) as conn:
        versions = conn.execute("SELECT current_setting('server_version'), (SELECT extversion FROM pg_extension WHERE extname='vector')").fetchone()
    write_json(ROOT / 'results/index_manifest.json', {'strategy': 'DAY7_B', 'chunks': len(chunks),
        'model': model, 'dimensions': embedder.dimensions, 'pages_sha256': digest(ROOT / 'data/day06/pages.jsonl'),
        'postgresql': versions[0], 'pgvector': versions[1]})
