#!/usr/bin/env python3
"""Verify production files through the prefix/sandbox static test server."""
import argparse,hashlib,json
from urllib.parse import quote,urlsplit
from urllib.request import urlopen
from verify_publication import ROOT
MIMES={'.js':{'text/javascript','application/javascript'},'.css':{'text/css'},'.json':{'application/json'},'.csv':{'text/csv'},'.pdf':{'application/pdf'},'.zip':{'application/zip'}}
def verify(base):
 records=json.loads((ROOT/'SITE_MANIFEST.json').read_text());origin=urlsplit(base);total=0;types=set()
 for prefix in ['REPOSITORY/','sandbox-review/site/']:
  for r in records:
   url=base.rstrip('/')+'/'+prefix+quote(r['path'])
   with urlopen(url,timeout=15) as response:
    assert response.status==200;assert urlsplit(response.geturl()).netloc==origin.netloc
    data=response.read();assert hashlib.sha256(data).hexdigest()==r['sha256'],r['path']
    suffix='.'+r['path'].rsplit('.',1)[-1];mime=response.headers.get_content_type()
    if suffix in MIMES:assert mime in MIMES[suffix],(r['path'],mime);types.add(suffix)
    if prefix.startswith('sandbox'):assert 'sandbox allow-scripts' in response.headers.get('Content-Security-Policy','')
    total+=1
 with urlopen(base.rstrip('/')+'/sandbox-review/',timeout=15) as response:
  assert hashlib.sha256(response.read()).hexdigest()==hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest()
 return {'status':'passed','static_file_responses_checked':total,'root_bridge_checked':True,'mime_types_checked':sorted(types),'redirect_hosts_preserved':True,'scope':'Local production static serving; not the live anonymization service.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--base',default='http://127.0.0.1:5175');a=ap.parse_args();print(json.dumps(verify(a.base),indent=2))
