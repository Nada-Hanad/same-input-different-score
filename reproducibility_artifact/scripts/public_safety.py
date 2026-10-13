#!/usr/bin/env python3
"""Generic public allowlist checks without identifying privacy-denylist literals."""
import json,re
from pathlib import Path
ART=Path(__file__).resolve().parents[1]
def validate_public_files():
 for p in ART.rglob('*'):
  if not p.is_file() or any(k in p.parts for k in ['node_modules','__pycache__','.figure-env','generated']):continue
  assert p.suffix not in ['.map','.log','.pyc']
  if p.suffix in ['.json','.md','.mjs','.py','.sh'] and p.name not in ['privacy_review.py','public_safety.py']:
   t=p.read_text();assert not re.search(r'(?:/Users/|/home/)[A-Za-z0-9_.-]+',t)
 for name in ['rule-input.json','parser-input.json']:
  d=json.loads((ART/'examples'/name).read_text());assert d['site']['hostname']=='fixture.invalid';assert d['session']['jar']['cookies']==[]
 return {'status':'passed','scope':'Public file exclusions and approved synthetic inputs'}
if __name__=='__main__':print(json.dumps(validate_public_files(),indent=2))
