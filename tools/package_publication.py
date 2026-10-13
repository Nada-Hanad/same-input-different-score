#!/usr/bin/env python3
"""One portable publication archive, outside its source folder; no recursive ZIP inclusion."""
import hashlib,json,zipfile
from verify_publication import ROOT,verify
verify();out=ROOT.parent/'www27_anonymous_release.zip'
records=json.loads((ROOT/'PUBLICATION_MANIFEST.json').read_text())
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for r in records:z.write(ROOT/r['path'],'www27_anonymous_release/'+r['path'])
 z.write(ROOT/'PUBLICATION_MANIFEST.json','www27_anonymous_release/PUBLICATION_MANIFEST.json')
print(json.dumps({'archive':out.name,'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2))
