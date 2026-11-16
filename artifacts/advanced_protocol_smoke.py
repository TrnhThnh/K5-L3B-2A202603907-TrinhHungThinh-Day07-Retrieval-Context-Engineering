"""Small dev-only compatibility check, never final test evidence."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.day7.runtime import load_environment
from src.day7.data import write_json
from src.advanced.common import read_json,DATA
from src.advanced.agent import run
from src.advanced.store import Retriever
load_environment(sys.argv[1])
config=read_json(ROOT/'configs/advanced.json')[0]
retriever=Retriever()
traces=[]
for q in read_json(DATA/'benchmark.json'):
    if q['id'] in {'ad02','ad07'}:
        t={'query_id':q['id'],**run(q['question'],retriever,config)}
        traces.append(t)
        print(q['id'],t['status'],t['answer'],flush=True)
write_json(ROOT/'results/advanced/protocol-smoke.json',traces)
