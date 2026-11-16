"""One tiny provider probe, preserving sanitized error diagnosis; not a benchmark."""
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.day7.runtime import load_environment
from src.day7.data import write_json
from src.advanced.common import reserve_budget,image_part
load_environment(sys.argv[1])
key=os.environ['OPENROUTER_API_KEY']
quota=reserve_budget(key,'google/gemini-2.5-flash-lite')
content='Say OK.'
if len(sys.argv)>2:
    content=[{'type':'text','text':'Return only OK if this report page is readable.'},image_part(ROOT/sys.argv[2])]
request=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
    data=json.dumps({'model':'google/gemini-2.5-flash-lite','messages':[{'role':'user','content':content}],'max_tokens':10}).encode(),
    headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(request,timeout=45) as r:data=json.load(r)
    out={'status':'ok','usage':data.get('usage',{}),'quota':quota}
except urllib.error.HTTPError as exc:
    text=exc.read().decode(errors='replace').replace(key,'[REDACTED]')
    text=re.sub(r'https://openrouter\.ai/workspaces/\S+','[key settings]',text)
    text=re.sub(r'user_[A-Za-z0-9]+','[USER]',text)
    out={'status':'error','http':exc.code,'response':text[:3000],'quota':quota}
write_json(ROOT/('results/advanced/provider-probe-image.json' if len(sys.argv)>2 else 'results/advanced/provider-probe.json'),out)
print(json.dumps(out,indent=2))
