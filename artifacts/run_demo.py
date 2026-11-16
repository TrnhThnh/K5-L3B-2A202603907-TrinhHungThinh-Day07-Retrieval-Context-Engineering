"""Two real Vietnamese demonstrations; uses the same frozen agent implementation."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.day7.agent import OpenRouter, run_agent
from src.day7.data import load_chunks, write_json
from src.day7.retrieval import build_retriever
from src.day7.runtime import connect_dense, load_environment

load_environment(sys.argv[1] if len(sys.argv) > 1 else None)
chunks = load_chunks()
store, embedder, strategy = connect_dense(chunks)
retriever = build_retriever('hybrid', chunks, store, embedder, strategy)
client = OpenRouter(os.getenv('OPENROUTER_API_KEY'), os.getenv('CHAT_MODEL', 'openai/gpt-4o-mini'))
for name, question in [
    ('answer', 'Trả lời bằng tiếng Việt: Ngoài lịch định kỳ, khi nào cảng cần quét lỗ hổng?'),
    ('abstain', 'Trả lời bằng tiếng Việt: Báo cáo nêu chính xác bao nhiêu vụ ransomware tại cảng Los Angeles trong năm 2035?')
]:
    result = run_agent(question, client, retriever, top_k=6, budget=6000)
    write_json(ROOT / f'results/demo-{name}.json', {'question': question, **result})
    print(name, result['status'], flush=True)
