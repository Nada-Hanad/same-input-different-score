#!/usr/bin/env python3
"""Verify the extracted bundle's exact file inventory and SHA-256 entries."""
import hashlib,json,sys
from pathlib import Path
from packaging_allowlist import allowed

def verify(root):
 root=Path(root).resolve();records=json.loads((root/'BUNDLE_MANIFEST.json').read_text());paths=set()
 for row in records:
  p=root/row['path'];assert p.resolve().is_relative_to(root),'path escape';assert row['path'] not in paths;paths.add(row['path'])
  assert p.is_file(),row['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
  assert not any(x in p.relative_to(root).parts for x in ['.git','node_modules','raw_data','outputs','__pycache__'])
  assert p.suffix not in ['.map','.log','.pyc'];assert allowed(row['path']),row['path']
 # npm installations/test caches may be created after extraction; they are not released content.
 actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and not any(x in p.parts for x in ['node_modules','__pycache__','.vite','.figure-env','generated']) and p.name!='BUNDLE_MANIFEST.json'}
 assert actual==paths,sorted(actual^paths)
 if (root/'SCIENTIFIC_MANIFEST.json').exists():
  from scientific_integrity import verify_scientific
  verify_scientific(root)
 return {'status':'passed','files':len(records),'scope':'Exact standalone scientific bundle inventory and content integrity'}
if __name__=='__main__' and (Path(__file__).resolve().parents[2]/'PUBLICATION_MANIFEST.json').exists():
 import sys
 sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
 from verify_publication import verify as verify_publication
 print(json.dumps(verify_publication(),indent=2));raise SystemExit(0)
if __name__=='__main__':print(json.dumps(verify(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[2]),indent=2))
