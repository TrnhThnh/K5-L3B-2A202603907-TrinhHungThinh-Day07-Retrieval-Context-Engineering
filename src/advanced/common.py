import base64
import json
import os
import re
import threading
import urllib.error
import urllib.request
from pathlib import Path
from src.day7.data import ROOT, digest, write_json

DATA = ROOT / 'data/advanced'
RESULTS = ROOT / 'results/advanced'
SOURCE_ID = 'world-bank-cybersecurity-ports-2026'
_budget_lock=threading.Lock()
_inflight=0


def reserve_budget(key,model):
    """Read current provider quota before every paid call; leave headroom for in-flight calls."""
    global _inflight
    reserve=0.008 if model=='google/gemini-2.5-flash-lite' else 0.025
    with _budget_lock:
        request=urllib.request.Request('https://openrouter.ai/api/v1/key',headers={'Authorization':f'Bearer {key}'})
        with urllib.request.urlopen(request,timeout=30) as response:
            status=json.load(response)['data']
        remaining=min(float(status['limit_remaining']),0.70-float(status['usage_daily']))
        if remaining-reserve*_inflight < reserve:
            raise RuntimeError('Budget guard: insufficient headroom below user daily ceiling USD 0.70')
        _inflight+=1
        return {'limit':status['limit'],'usage_daily':status['usage_daily'],'remaining':remaining,'reserved_usd':reserve}


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def image_part(path):
    encoded = base64.b64encode(Path(path).read_bytes()).decode('ascii')
    return {'type': 'image_url', 'image_url': {'url': 'data:image/jpeg;base64,' + encoded, 'detail': 'high'}}


def complete(messages, model, *, tools=None, tool_choice=None, max_tokens=3000):
    key = os.getenv('OPENROUTER_API_KEY')
    if not key:
        raise RuntimeError('Missing OPENROUTER_API_KEY')
    quota=reserve_budget(key,model)
    body = {'model': model, 'messages': messages, 'temperature': 0, 'max_tokens': max_tokens}
    if tools:
        body.update(tools=tools, tool_choice=tool_choice or 'required', parallel_tool_calls=False)
    else:
        body['response_format'] = {'type': 'json_object'}
    request = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
        data=json.dumps(body).encode('utf-8'),
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=150) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        # Preserve a short provider diagnosis, stripping the configured secret.
        detail=''
        try:
            error=json.loads(exc.read().decode('utf-8'))
            detail=str(error.get('error',{}).get('message','')).replace(key,'[REDACTED]')[:350]
            raw=error.get('error',{}).get('metadata',{}).get('raw')
            if exc.code==400 and raw:
                detail+=' '+str(raw).replace(key,'[REDACTED]')[:500]
            detail=re.sub(r'https://openrouter\.ai/workspaces/\S+', '[OpenRouter key settings]', detail)
        except Exception:
            pass
        raise RuntimeError(f'OpenRouter HTTP {exc.code}: {detail}') from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('OpenRouter network/timeout') from None
    finally:
        global _inflight
        with _budget_lock:
            _inflight-=1
    usage=payload.get('usage',{})
    usage['budget_before']=quota
    return payload['choices'][0]['message'],usage


def cost(usages):
    values = [u.get('cost') for u in usages]
    return {'known_usd': sum(v for v in values if isinstance(v, (int, float))),
            'complete': bool(values) and all(isinstance(v, (int, float)) for v in values)}
