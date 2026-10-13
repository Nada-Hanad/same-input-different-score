#!/usr/bin/env python3
"""Restricted streaming input-feature check, retains no bodies/cookie values in output."""
import gzip,json,re
from collections import Counter
from pathlib import Path
root=Path(__file__).resolve().parents[2];source=root/'outputs/observatory_tranco_2026-09-27'
features={}
for p in sorted((source/'shards').glob('*.jsonl.gz')):
 with gzip.open(p,'rt') as f:
  for line in f:
   if not line.strip():continue
   r=json.loads(line)
   if r['host'] in features or not r.get('roundtrip_ok') or not r.get('input'):continue
   x=r['input'];response=x['responses'].get(x['responses'].get('autoIs') or 'auto') or {};headers=response.get('headers') or {};policies=[]
   for k,v in headers.items():
    if k.lower()=='content-security-policy':policies.extend(v if isinstance(v,list) else [v])
   for k,v in response.get('httpEquiv') or []:
    if k.lower()=='content-security-policy':policies.extend(v if isinstance(v,list) else [v])
   def duplicate(values):
    for v in values:
     names=[d.strip().split()[0].lower() for d in str(v).split(';') if d.strip()]
     if names.count('report-uri')>1 or names.count('report-to')>1:return True
    return False
   features[r['host']]={'registered':duplicate([part for v in policies for part in str(v).split(',')]),'corrected':duplicate(policies),'stratum':r.get('stratum')}
scored=set()
for p in (source/'replay/1.3.8').glob('*.jsonl.gz'):
 with gzip.open(p,'rt') as f:
  for line in f:
   if not line.strip():continue
   r=json.loads(line)
   if r.get('status')=='ok':scored.add(r['host'])
counts={k:sum(features[h][k] for h in scored) for k in ['registered','corrected']}
assert counts=={'registered':0,'corrected':41},counts
out={'method':'Independent streaming CSP header predicate on stored inputs; no original analysis imports. Responses never exported.','counts':counts,'status':'passed'}
(root/'reproducibility_artifact/data/exposure-reference.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
