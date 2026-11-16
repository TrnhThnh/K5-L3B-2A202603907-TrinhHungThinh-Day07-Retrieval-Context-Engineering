"""Validate declared corpus/split/run completeness; create citation evidence crops."""
import argparse
from collections import Counter
from pathlib import Path
from .agent import valid_citations
from .common import DATA, ROOT, read_json
from src.day7.data import digest, write_json


def corpus_audit():
    pages=read_json(DATA/'pages.json');catalog=read_json(DATA/'visual_catalog.json')
    rows=read_json(DATA/'index_rows.json');cases=read_json(DATA/'benchmark.json')
    assert len(pages)>=100 and len(pages)==len(catalog)
    assert all(r['status']=='ok' for r in catalog)
    assert all((ROOT/r['image']).is_file() and digest(ROOT/r['image'])==r['page_sha256'] for r in pages)
    assert len({r['id'] for r in rows})==len(rows)
    assert len({q['id'] for q in cases})==len(cases)
    groups=Counter(q['group'] for q in cases if q['split']=='test')
    assert all(groups[g]>=n for g,n in {'table':6,'diagram':5,'chart':5,'multi_hop':4,'text':4,'unanswerable':6}.items())
    indexed={r['page'] for r in rows}
    empty=[p['page'] for p in pages if p['page'] not in indexed]
    assert all(not p['text'].strip() for p in pages if p['page'] in empty)
    write_json(DATA/'corpus_audit.json',{'physical_pages':len(pages),'rendered_pages':len(pages),
        'vision_catalog_ok':len(catalog),'indexed_pages':len(indexed),'index_rows':len(rows),
        'unindexed_pages':empty,'reason_unindexed':'Physically blank page; no useful native text or visual content.',
        'test_groups':dict(groups),'source_sha256':digest(DATA/'source.pdf'),
        'warning':'Structural audit does not certify machine extraction or answer correctness; original-page content reviews required.'})


def crop_citations(folder):
    from PIL import Image
    traces=read_json(folder/'traces.json')
    output=folder/'evidence'
    output.mkdir(exist_ok=True)
    for t in traces:
        if t['status']=='answered':
            assert valid_citations(t['citations'],t['opened_pages'])
        for index,c in enumerate(t['citations']):
            image=Image.open(ROOT/c['image']);box=c['bbox']
            rect=(int(box[0]*image.width),int(box[1]*image.height),
                  int(box[2]*image.width),int(box[3]*image.height))
            path=output/f"{t['query_id']}-c{index+1}-p{c['page']:03}.jpg"
            image.crop(rect).save(path,quality=90)
    print('Citation crops saved for original-page review:',folder,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path)
    args=parser.parse_args()
    corpus_audit()
    if args.run:crop_citations(args.run)
