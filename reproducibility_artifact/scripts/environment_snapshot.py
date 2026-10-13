"""Allowlisted package/version/integrity projection from retained installation locks."""
import json,os
from pathlib import Path
import hashlib

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(versions):
 base=Path(os.environ.get('OBS_PKG_DIR',Path.home()/'.cache/sr_surrogate/observatory_pkgs'))
 out={'scope':'Retained installations inspected during companion preparation; not a fresh replay. Projections omit local root names and registry URLs.','releases':{},'reference':{}}
 for v in versions:
  p=base/v/'node_modules/@mdn/mdn-http-observatory/package.json';lock=base/v/'package-lock.json'
  if not p.exists() or not lock.exists():out['releases'][v]={'available':False};continue
  d=json.loads(p.read_text());l=json.loads(lock.read_text())
  deps={k:{x:r[x] for x in ['version','integrity','license'] if x in r} for k,r in l.get('packages',{}).items() if k.startswith('node_modules/')}
  out['releases'][v]={'available':True,'package':{k:d[k] for k in ['name','version','license','engines','dependencies'] if k in d},'original_lock_sha256':sha(lock),'resolved_packages':deps}
 for name in ['hsts-preload.json','tld-list.json','ca_intermediate_root_bundle_2026-09-27.pem']:
  p=base/'reference'/name
  if p.exists():out['reference'][name]={'sha256':sha(p),'bytes':p.stat().st_size}
 p=base/'reference/GENERATED_AT'
 if p.exists():out['reference_generated_at']=p.read_text().strip()
 return out
