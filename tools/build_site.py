#!/usr/bin/env python3
"""Prepare committed static files. No owner, repository URL or server backend required."""
from pathlib import Path
import hashlib,json,shutil
from sync_public import sync
from package import package as package_scientific
ROOT=Path(__file__).resolve().parents[1]
def build():
 public=ROOT/'research_companion/public'
 sync(ROOT)
 package_scientific(ROOT)
 dist=ROOT/'research_companion/dist';site=ROOT/'site'
 if site.exists():shutil.rmtree(site)
 shutil.copytree(public,site)
 shutil.copyfile(dist/'app.js',site/'app.js')
 shutil.copytree(dist/'assets',site/'assets',dirs_exist_ok=True)
 for p in (ROOT/'downloads').glob('*'):
  if p.is_file():(site/'downloads').mkdir(exist_ok=True);shutil.copyfile(p,site/'downloads'/p.name)
 html='<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="artifact-root" content="./"><link rel="icon" href="data:,"><meta name="description" content="Anonymous fixed-input research companion"><title>Same Input, Different Score</title>'
 for p in sorted((site/'assets').glob('*.css')):html+='<link rel="stylesheet" href="./assets/'+p.name+'">'
 html+='</head><body><div id="root"></div><script defer src="./app.js"></script></body></html>\n'
 (site/'index.html').write_text(html);(site/'.nojekyll').write_text('')
 # Anonymous Pages reads committed repository files. Root serves the same application.
 bridge=html.replace('content="./"','content="./site/"').replace('href="./assets/','href="./site/assets/').replace('src="./app.js"','src="./site/app.js"')
 (ROOT/'index.html').write_text(bridge)
 records=[{'path':str(p.relative_to(site)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(site.rglob('*')) if p.is_file()]
 (ROOT/'SITE_MANIFEST.json').write_text(json.dumps(records,indent=2)+'\n')
 print(json.dumps({'site_files':len(records),'scope':'Relative classic-script build; committed site and root bridge'}))
if __name__=='__main__':build()
