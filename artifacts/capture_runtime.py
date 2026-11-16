"""Record versions and input/code hashes without recording credentials."""
import os
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.day7.data import digest, write_json
from src.day7.runtime import load_environment

load_environment(sys.argv[1] if len(sys.argv) > 1 else None)
import psycopg
with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=5) as conn:
    postgres, pgvector = conn.execute("SELECT current_setting('server_version'), (SELECT extversion FROM pg_extension WHERE extname='vector')").fetchone()
manifest = {
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'python': platform.python_version(), 'postgresql': postgres, 'pgvector': pgvector,
    'packages': {p: version(p) for p in ['sentence-transformers', 'torch', 'numpy', 'psycopg', 'python-dotenv']},
    'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2', 'dimensions': 384,
    'strategy': os.getenv('DAY6_STRATEGY', 'B'), 'chat_model': os.getenv('CHAT_MODEL', 'openai/gpt-4o-mini'),
    'inputs': {p: digest(ROOT / p) for p in ['data/benchmark.json', 'data/day06/pages.jsonl', 'configs/experiments.json']},
    'code': {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in (ROOT / 'src/day7').glob('*.py')},
    'provider': 'OpenRouter', 'key_or_database_url_recorded': False,
    'embedding_revision_limit': 'Original cache/model provenance reused; Day06 table does not store embedding model revision.'
}
write_json(ROOT / 'results/final/runtime.json', manifest)
print('Runtime versions and hashes recorded; credentials omitted.')
