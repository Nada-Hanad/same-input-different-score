#!/usr/bin/env python3
"""Exact publication inventory and hash checks; runtime installs and Git are excluded."""
import argparse,hashlib,json,re,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IGNORED={'node_modules','__pycache__','.vite','.figure-env','generated','.git'}
def files(root):
 return [p for p in root.rglob('*') if p.is_file() and not IGNORED.intersection(p.relative_to(root).parts) and not str(p.relative_to(root)).startswith('research_companion/dist/')]
def verify(root=ROOT,scope='all'):
 records=json.loads((root/'PUBLICATION_MANIFEST.json').read_text());allow=set(json.loads((root/'PUBLICATION_ALLOWLIST.json').read_text()));paths=set()
 for r in records:
  path=r['path'];assert path in allow and path not in paths;paths.add(path);p=root/path
  assert p.resolve().is_relative_to(root.resolve()) and p.is_file() and not p.is_symlink(),path
  assert p.stat().st_size==r['bytes'],path
  if scope=='source' and (path.startswith('site/') or path in ['index.html','SITE_MANIFEST.json']):continue
  if scope=='site' and not (path.startswith('site/') or path in ['index.html','SITE_MANIFEST.json']):continue
  assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],path
 actual={str(p.relative_to(root)) for p in files(root)}-{'PUBLICATION_MANIFEST.json'}
 assert actual==paths,sorted(actual^paths)
 assert allow==paths,sorted(allow^paths)
 import sys
 sys.path.insert(0,str(root/'reproducibility_artifact/scripts'))
 from scientific_integrity import verify_scientific
 verify_scientific(root)
 assert all(not IGNORED.intersection(Path(p).parts) for p in paths)
 assert all(Path(p).suffix not in ['.map','.log','.pyc'] for p in paths)
 if scope!='source':
  html=(root/'site/index.html').read_text();assert 'type="module"' not in html and 'crossorigin' not in html
  assert 'src="./app.js"' in html and 'content="./"' in html
  js=(root/'site/app.js').read_text();assert 'localhost' not in js and '127.0.0.1' not in js and '.github.io' not in js
  assert not re.search(r'(?:/Users/|/home/)[A-Za-z0-9_.-]+',js)
  for name,key in [('research-core','core'),('population','population')]:
   script=(root/'site/data'/f'{name}.js').read_text();prefix=f'window.__artifactData=window.__artifactData||{{}};window.__artifactData.{key}='
   assert script.startswith(prefix)
   assert json.loads(script[len(prefix):].rstrip().removesuffix(';'))==json.loads((root/'research_companion/public/data'/f'{name}.json').read_text())
  static=json.loads((root/'SITE_MANIFEST.json').read_text())
  assert {r['path'] for r in static}=={str(p.relative_to(root/'site')) for p in (root/'site').rglob('*') if p.is_file()}
  for r in static:assert hashlib.sha256((root/'site'/r['path']).read_bytes()).hexdigest()==r['sha256']
 from download_integrity import verify_downloads
 verify_downloads(root)
 from curated_release import verify_curated,verify_links
 verify_curated(root);verify_links(root)
 catalogue=json.loads((root/'docs/figure-references.json').read_text())
 assert [f['number'] for f in catalogue['figures']]==[1,2,3]
 assert [f['figure_values_key'] for f in catalogue['figures'] if f['kind']=='numerical result']==['fig_cascade','fig_remediation_plan_failures']
 assert (root/'research_companion/public/data/figure-references.json').read_bytes()==(root/'docs/figure-references.json').read_bytes()
 if scope!='source':assert (root/'site/data/figure-references.json').read_bytes()==(root/'docs/figure-references.json').read_bytes()
 # Check the deferred projection against the full, protected research dataset.
 full=json.loads((root/'reproducibility_artifact/data/research.json').read_text())
 core=json.loads((root/'research_companion/public/data/research-core.json').read_text())
 extra=json.loads((root/'research_companion/public/data/population.json').read_text())
 assert {**core,**extra}==full
 assert (root/'research_companion/public/data/release-pair-baseline.csv').read_bytes()==(root/'reproducibility_artifact/data/release-pair-baseline.csv').read_bytes()
 if scope!='source':assert (root/'site/data/release-pair-baseline.csv').read_bytes()==(root/'reproducibility_artifact/data/release-pair-baseline.csv').read_bytes()
 # The standalone scientific archive has exact content and its own checked inventory.
 from verify_bundle import verify as verify_bundle
 import tempfile
 with tempfile.TemporaryDirectory() as directory:
  with zipfile.ZipFile(root/'downloads/scientific-artifact.zip') as archive:
   for member in archive.infolist():
    name=Path(member.filename);assert not name.is_absolute() and '..' not in name.parts
    assert name.parts[0]=='same_input_artifact' and not member.filename.endswith('.zip')
   archive.extractall(directory)
  extracted=Path(directory)/'same_input_artifact';verify_bundle(extracted)
  for path in extracted.rglob('*'):
   if path.is_file() and path.name not in ['BUNDLE_MANIFEST.json','README.md']:
    assert path.read_bytes()==(root/path.relative_to(extracted)).read_bytes(),str(path)
 if scope!='source':assert (root/'site/downloads/scientific-artifact.zip').read_bytes()==(root/'downloads/scientific-artifact.zip').read_bytes()
 links=json.loads((root/'review-links.json').read_text())
 from urllib.parse import urlsplit
 assert set(links)=={'anonymous_repository_url','anonymous_website_url'}
 for value in links.values():
  if value:assert urlsplit(value).scheme=='https' and urlsplit(value).hostname=='anonymous.4open.science' and not urlsplit(value).username and not urlsplit(value).password
 return {'status':'passed','scope':scope,'files':len(records),'largest_file_bytes':max((root/p).stat().st_size for p in paths),'under_conservative_8MB':all((root/p).stat().st_size<8_000_000 for p in paths)}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',action='store_true');ap.add_argument('--site',action='store_true');a=ap.parse_args();print(json.dumps(verify(scope='source' if a.source else 'site' if a.site else 'all'),indent=2))
