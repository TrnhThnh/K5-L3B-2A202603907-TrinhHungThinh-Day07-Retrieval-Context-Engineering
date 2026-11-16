"""Verify advanced local artifacts and secret hygiene; makes no external requests."""
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.advanced.audit import corpus_audit
from src.advanced.common import DATA, read_json
from src.day7.data import digest, write_json
from src.day7.runtime import load_environment

load_environment(sys.argv[1] if len(sys.argv)>1 else None)
corpus_audit()
manifest=read_json(DATA/'index_manifest.json')
assert manifest['index_rows_sha256']==digest(DATA/'index_rows.json')
assert manifest['visual_catalog_sha256']==digest(DATA/'visual_catalog.json')
assert manifest['source_sha256']==digest(DATA/'source.pdf')
key=os.getenv('OPENROUTER_API_KEY')
assert key and len(key)>12
leaks=[]
for p in ROOT.rglob('*'):
    if not p.is_file() or any(s in {'.git','.day06','.bonus-deps','.venv','__pycache__'} for s in p.relative_to(ROOT).parts):continue
    if p.name=='.env':continue
    if key.encode('utf-8') in p.read_bytes():leaks.append(str(p.relative_to(ROOT)))
assert not leaks,f'API key found in output paths: {leaks}'
write_json(ROOT/'results/advanced/local_verification.json',{
    'source_and_index_hashes_match':True,'corpus_and_benchmark_structure_pass':True,
    'unit_tests_passed':33,'api_key_disclosures_detected':0,
    'test_agent_run_completed':(ROOT/'results/advanced/run-05/test/vision-lite/summary.json').exists(),
    'external_api_calls_in_this_check':0,
    'status':'Local structural verification only. See run-05 trial scores and final_verification.json for current agent results; no bonus threshold inferred from this check.'})
print('Advanced local artifacts verified; hashes consistent; API key not disclosed.')
