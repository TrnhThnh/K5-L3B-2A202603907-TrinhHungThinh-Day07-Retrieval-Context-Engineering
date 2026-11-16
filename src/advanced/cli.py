"""Interactive advanced question answering with original image-region citations."""
import argparse
from pathlib import Path
from .agent import run
from .common import DATA, ROOT, read_json
from .store import Retriever
from src.day7.data import write_json
from src.day7.runtime import load_environment


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file',type=Path)
    parser.add_argument('question')
    parser.add_argument('--trace',type=Path,default=ROOT/'results/advanced/demo.json')
    parser.add_argument('--selection',type=Path,default=ROOT/'results/advanced/run-05/selection.json')
    args=parser.parse_args()
    load_environment(args.env_file)
    if args.selection.exists():
        config=read_json(args.selection)['config']
    else:
        config=read_json(ROOT/'configs/advanced.json')[1]
    trace=run(args.question,Retriever(),config)
    write_json(args.trace,trace)
    print(trace['answer'] or f"Error: {trace['reason']}")
    for c in trace['citations']:
        print(f"PDF page {c['page']}, {c['label']}, bbox={c['bbox']}")
    if trace['status']=='error':
        raise SystemExit(1)


if __name__=='__main__':main()
