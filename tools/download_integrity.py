"""Verify every hosting download against canonical content and recorded hashes."""
import hashlib,json
from pathlib import Path
def verify_downloads(root):
 root=Path(root);public=root/'research_companion/public'
 records=json.loads((root/'reproducibility_artifact/data/download-manifest.json').read_text())
 assert (public/'data/download-manifest.json').read_bytes()==(root/'reproducibility_artifact/data/download-manifest.json').read_bytes()
 paths=set()
 for row in records:
  path=public/row['path'];assert path.resolve().is_relative_to(public.resolve())
  assert row['path'] not in paths;paths.add(row['path'])
  assert path.is_file() and not path.is_symlink(),row['path']
  assert path.stat().st_size==row['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],row['path']
 assert paths=={str(p.relative_to(public)) for p in public.rglob('*') if p.is_file()}-{'data/download-manifest.json'}
 from sync_public import DOCS,document_for_host
 for name in DOCS:assert (public/'docs'/name).read_text()==document_for_host((root/'docs'/name).read_text()),name
 for path in (root/'reproducibility_artifact/data').glob('*'):
  if path.is_file():assert (public/'data'/path.name).read_bytes()==path.read_bytes(),path.name
 for directory,destination in [('figures','figures'),('source/observatory_replay','files/source/observatory_replay')]:
  for path in (root/'reproducibility_artifact'/directory).glob('*'):
   if path.is_file():assert path.read_bytes()==(public/destination/path.name).read_bytes(),path.name
 assert (public/'data/figure-references.json').read_bytes()==(root/'docs/figure-references.json').read_bytes()
 return {'status':'passed','public_downloads_checked':len(records)}
