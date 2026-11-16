"""Resolve model-selected page/labels to document regions; never reads benchmark gold.

Keep raw model coordinates for audit. Matching uses the query-independent visual
catalog or PDF text layout, not expected answers/evidence rectangles.
"""
import argparse
import re
import sys
import math
from collections import Counter
from pathlib import Path
from .common import DATA, ROOT, read_json
from src.day7.data import digest, write_json


def normalized(text):
    return ' '.join(re.findall(r'\w+',text.casefold()))


def align(citation,rows,doc):
    c=dict(citation)
    label=normalized(c['label'])
    candidates=[r for r in rows if r['page']==c['page'] and ':v' in r['id']]
    exact=[r for r in candidates if normalized(r['metadata']['label'])==label]
    number=re.search(r'\b(figure|table|box)\s+(\d+)\b',label)
    if not exact and number:
        pattern=rf'\b{number[1]}\s+{number[2]}\b'
        exact=[r for r in candidates if re.search(pattern,normalized(r['metadata']['label']))]
    if not exact:
        exact=[r for r in candidates if label and (label in normalized(r['metadata']['label']) or
               normalized(r['metadata']['label']) and normalized(r['metadata']['label']) in label)]
    if len(exact)==1:
        c.update(model_bbox=c['bbox'],bbox=exact[0]['metadata']['bbox'],
                 bbox_resolution='query_independent_catalog_label',region_id=exact[0]['id'])
        return c
    # Fine-grained row/heading labels can be found directly in the original PDF.
    page=doc[c['page']-1]
    generic=label in {'text','native page text','illustrative examples',''}
    rects=[] if generic else page.search_for(c['label'])
    if not rects:
        words=c['label'].split()
        if len(words)>2:rects=page.search_for(' '.join(words[:3]))
    blocks=[b for b in page.get_text('blocks') if len(b)>4 and isinstance(b[4],str) and b[4].strip()]
    query=set(normalized(c.get('support','')).split())-{'the','a','an','of','in','to','for','and','is','are','that','with','by','this','from','it','as','on'}
    words=[set(normalized(b[4]).split()) for b in blocks]
    df=Counter(w for values in words for w in values)
    weights={w:math.log((len(blocks)+1)/(df.get(w,0)+1))+1 for w in query}
    denom=sum(weights.values()) or 1
    ranked=sorted([(sum(weights[w] for w in query & ws)/denom,len(query & ws),b) for b,ws in zip(blocks,words)],reverse=True)
    semantic=[ranked[0][2]] if ranked and ranked[0][0]>=.20 and ranked[0][1]>=3 else []
    if rects or semantic:
        top=min([r.y0 for r in rects]+[b[1] for b in semantic]);bottom=max([r.y1 for r in rects]+[b[3] for b in semantic])
        overlap=[b for b in blocks if b[1]<bottom and b[3]>top and len(b)>4 and isinstance(b[4],str)]
        if overlap:
            top=min(b[1] for b in overlap);bottom=max(b[3] for b in overlap)
        # Include the whole row width, retaining adjacent table-cell explanation.
        box=[.05,max(0,top/page.rect.height-.01),.95,min(1,bottom/page.rect.height+.01)]
        c.update(model_bbox=c['bbox'],bbox=box,bbox_resolution='original_pdf_label_support_and_overlapping_text_blocks')
    return c


def align_folder(folder):
    try:import pymupdf
    except ImportError:
        sys.path.append(str(ROOT/'.bonus-deps'))
        import pymupdf
    path=folder/'traces.json'
    raw=folder/'traces.model-output.json'
    if not raw.exists():write_json(raw,read_json(path))
    traces=read_json(raw);rows=read_json(DATA/'index_rows.json')
    doc=pymupdf.open(DATA/'source.pdf')
    corrected=0
    for t in traces:
        t['citations']=[align(c,rows,doc) for c in t['citations']]
        changed=[c for c in t['citations'] if c.get('bbox_resolution')]
        corrected+=len(changed)
        if changed:t['events'].append({'event':'citation_alignment','citations':changed,
            'method':'Document catalog/printed-label geometry; no benchmark answers or gold regions read.'})
    write_json(path,traces)
    write_json(folder/'citation_alignment.json',{'resolved_citations':corrected,
        'raw_traces_sha256':digest(raw),'aligned_traces_sha256':digest(path),
        'catalog_sha256':digest(DATA/'index_rows.json'),
        'code_sha256':digest(Path(__file__)),'gold_used':False,
        'limit':'Geometry alignment locates a model-selected source; does not certify semantic support.'})
    print('Aligned',corrected,'citation regions in',folder,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    align_folder(parser.parse_args().run)
