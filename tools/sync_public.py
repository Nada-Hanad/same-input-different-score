"""Generate hosting assets from canonical scientific files and four documents."""
import hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reproducibility_artifact/scripts'))
from public_docs import DOCS,refresh_public_docs

def document_for_host(text):
 return text.replace('../reproducibility_artifact/data/','../data/')

def sync(root=ROOT):
 root=Path(root);artifact=root/'reproducibility_artifact';public=root/'research_companion/public'
 if public.exists():shutil.rmtree(public)
 public.mkdir(parents=True)
 refresh_public_docs(root)
 for name in DOCS:
  (public/'docs'/name).write_text(document_for_host((root/'docs'/name).read_text()))
 (public/'data').mkdir()
 for path in (artifact/'data').glob('*'):
  if path.is_file() and path.name!='download-manifest.json':shutil.copyfile(path,public/'data'/path.name)
 research=json.loads((artifact/'data/research.json').read_text())
 core={**research,'population':{'sites':research['population']['sites'],'note':research['population']['note'],'levels':{},'changes':{}},'grade_distributions':{}}
 extra={'population':research['population'],'grade_distributions':research['grade_distributions']}
 for name,data in [('research-core',core),('population',extra),('synthetic-replay',research['synthetic_replay']),('synthetic-flooring',research['synthetic_flooring'])]:
  (public/'data'/f'{name}.json').write_text(json.dumps(data,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
 for key,name,data in [('core','research-core',core),('population','population',extra)]:
  (public/'data'/f'{name}.js').write_text('window.__artifactData=window.__artifactData||{};window.__artifactData.'+key+'='+json.dumps(data,ensure_ascii=True,separators=(',',':'))+';\n')
 shutil.copyfile(root/'docs/figure-references.json',public/'data/figure-references.json')
 shutil.copytree(artifact/'figures',public/'figures')
 shutil.copytree(artifact/'source/observatory_replay',public/'files/source/observatory_replay')
 (public/'files/scripts').mkdir(parents=True)
 shutil.copyfile(artifact/'scripts/figures_public.py',public/'files/scripts/figures_public.py')
 (public/'examples').mkdir()
 for name in ['flooring-input.json','flooring-expected.json','run.mjs','worker.mjs','action-definitions.json']:shutil.copyfile(artifact/'examples'/name,public/'examples'/name)
 shutil.copyfile(artifact/'THIRD_PARTY_NOTICES.txt',public/'THIRD_PARTY_NOTICES.txt')
 records=[{'path':str(p.relative_to(public)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(public.rglob('*')) if p.is_file()]
 payload=json.dumps(records,indent=2)+'\n'
 (artifact/'data/download-manifest.json').write_text(payload)
 (public/'data/download-manifest.json').write_text(payload)
 return records
if __name__=='__main__':print(json.dumps({'public_resources':len(sync())}))
