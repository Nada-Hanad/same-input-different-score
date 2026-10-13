#!/usr/bin/env python3
"""Build a standalone scientific archive without manuscripts or internal records."""
import hashlib,json,zipfile
from pathlib import Path
from packaging_allowlist import allowed
from scientific_integrity import verify_scientific
ROOT=Path(__file__).resolve().parents[2]

def selected(root):
 paths=[]
 for folder in ['reproducibility_artifact','research_companion/public','docs']:
  for path in (root/folder).rglob('*'):
   if path.is_file() and allowed(str(path.relative_to(root))):paths.append(path)
 for name in ['LICENSE.md','THIRD_PARTY_NOTICES.md','SCIENTIFIC_MANIFEST.json']:paths.append(root/name)
 return sorted(paths)

def package(root=ROOT):
 verify_scientific(root);out=root/'downloads/scientific-artifact.zip';out.parent.mkdir(exist_ok=True)
 paths=selected(root)
 readme='# Same Input, Different Score — scientific artifact\n\nRun make -C reproducibility_artifact reproduce for public verification, install-scorers replay for three genuine historical scorer fixtures, and figure-env figures for plots. See docs/REPRODUCIBILITY.md and docs/METHODS_AND_LIMITATIONS.md. Website source/build commands apply to the repository, not this scientific-only archive. Full empirical replay requires restricted inputs. No manuscript is bundled.\n'
 records=[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in paths]
 records.append({'path':'README.md','sha256':hashlib.sha256(readme.encode()).hexdigest(),'bytes':len(readme.encode())});records.sort(key=lambda r:r['path'])
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  contents={str(p.relative_to(root)):p.read_bytes() for p in paths}
  contents['README.md']=readme.encode()
  contents['BUNDLE_MANIFEST.json']=(json.dumps(records,indent=2)+'\n').encode()
  for name,data in sorted(contents.items()):
   info=zipfile.ZipInfo('same_input_artifact/'+name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,data)
 return {'archive':out.name,'files':len(records)+1,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
if __name__=='__main__':print(json.dumps(package(),indent=2))
