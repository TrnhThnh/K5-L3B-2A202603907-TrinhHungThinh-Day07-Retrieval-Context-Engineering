"""Read only numerical quota fields; never display API key or key identifier."""
import json
import os
import sys
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.day7.runtime import load_environment
load_environment(sys.argv[1] if len(sys.argv)>1 else None)
req=urllib.request.Request('https://openrouter.ai/api/v1/key',headers={'Authorization':'Bearer '+os.environ['OPENROUTER_API_KEY']})
with urllib.request.urlopen(req,timeout=30) as response:data=json.load(response)['data']
safe={k:data.get(k) for k in ['limit','limit_remaining','limit_reset','usage','usage_daily','usage_weekly','usage_monthly','is_free_tier']}
print(json.dumps(safe,indent=2))
if len(sys.argv)>2:
    from src.day7.data import write_json
    write_json(Path(sys.argv[2]),safe)
