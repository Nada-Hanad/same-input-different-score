"""Check frozen scientific content independently of refreshed release hashes."""
import hashlib,json
from pathlib import Path

def verify_scientific(root):
 root=Path(root).resolve();records=json.loads((root/'SCIENTIFIC_MANIFEST.json').read_text());seen=set()
 assert records, 'Missing scientific inventory'
 for record in records:
  name=record['path'];path=root/name
  assert name not in seen and path.resolve().is_relative_to(root),name
  seen.add(name);assert path.is_file() and not path.is_symlink(),name
  assert path.stat().st_size==record['bytes'], 'Protected scientific file: '+name
  assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'],'Protected scientific file: '+name
 return {'status':'passed','scientific_files':len(records)}
