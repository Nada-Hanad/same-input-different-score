#!/usr/bin/env python3
"""Refresh approved release hashes while independently retaining frozen science."""
import hashlib,json,sys
from verify_publication import ROOT,files
sys.path.insert(0,str(ROOT/'reproducibility_artifact/scripts'))
from scientific_integrity import verify_scientific
from curated_release import verify_curated
verify_scientific(ROOT);verify_curated(ROOT)
allow=set(json.loads((ROOT/'PUBLICATION_ALLOWLIST.json').read_text()));records=[]
for path in sorted(files(ROOT)):
 name=str(path.relative_to(ROOT))
 if name=='PUBLICATION_MANIFEST.json':continue
 assert name in allow,'Unapproved file: '+name
 records.append({'path':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size})
assert {r['path'] for r in records}==allow,'Allowlist does not match release files'
(ROOT/'PUBLICATION_MANIFEST.json').write_text(json.dumps(records,indent=2)+'\n')
print('Updated',len(records),'approved hashes; frozen scientific content unchanged')
