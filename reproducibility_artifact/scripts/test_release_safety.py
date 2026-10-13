import hashlib,json,unittest,sys
from pathlib import Path
from validate import ART
from packaging_allowlist import allowed
class PublicReleaseTests(unittest.TestCase):
 def test_default_deny_unknown_or_restricted_paths(self):
  for p in ['raw_data/response.json','reproducibility_artifact/private-response.json','reproducibility_artifact/data/private.json','research_companion/public/raw.html','research_companion/dist/assets/index-test.map','research_companion/.git/config','reproducibility_artifact/examples/environments/1.5.2/node_modules/package.json','reproducibility_artifact/scripts/privacy_review.py']:self.assertFalse(allowed(p),p)
 def test_approved_paths(self):
  for p in ['reproducibility_artifact/data/research.json','reproducibility_artifact/examples/expected.json','research_companion/public/data/scientific-verification.json','docs/REPRODUCIBILITY.md']:self.assertTrue(allowed(p),p)
 def test_public_downloads_match_hashes(self):
  public=ART.parent/'research_companion/public'
  if (ART.parent/'PUBLICATION_MANIFEST.json').exists():
   sys.path.insert(0,str(ART.parent/'tools'))
   from download_integrity import verify_downloads
   self.assertEqual(verify_downloads(ART.parent)['status'],'passed')
  else:
   for x in json.loads((ART/'data/download-manifest.json').read_text()):self.assertEqual(hashlib.sha256((public/x['path']).read_bytes()).hexdigest(),x['sha256'],x['path'])
 def test_copied_source_hashes(self):
  for x in json.loads((ART/'data/source-code-manifest.json').read_text()):self.assertEqual(hashlib.sha256((ART/x['included']).read_bytes()).hexdigest(),x['sha256'])
 def test_fixture_lock_integrities_and_no_contact_metadata(self):
  for p in (ART/'examples/environments').glob('*/package-lock.json'):
   d=json.loads(p.read_text());r=d['packages']['node_modules/@mdn/mdn-http-observatory'];self.assertEqual(r['version'],p.parent.name);self.assertEqual(r['license'],'MPL-2.0');self.assertTrue(r['integrity'])
   for x in d['packages'].values():self.assertFalse({'funding','author','maintainers','deprecated'}.intersection(x))
if __name__=='__main__':unittest.main()
