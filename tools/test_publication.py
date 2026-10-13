"""Publication-level regressions, including negative integrity and hosting checks."""
import hashlib,json,re,shutil,tempfile,unittest
from pathlib import Path
from verify_publication import ROOT,verify,files
class PublicationTests(unittest.TestCase):
 def copy(self):
  temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);root=Path(temporary.name)/'release';root.mkdir()
  for p in files(ROOT):
   target=root/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
  return root
 def test_prepared_inventory(self):self.assertEqual(verify()['status'],'passed')
 def test_unknown_file_is_rejected(self):
  root=self.copy();(root/'unreviewed.txt').write_text('extra')
  with self.assertRaises(AssertionError):verify(root)
 def test_missing_file_is_rejected(self):
  root=self.copy();(root/'reproducibility_artifact/data/release-pair-baseline.csv').unlink()
  with self.assertRaises(AssertionError):verify(root)
 def test_altered_data_is_rejected(self):
  root=self.copy();p=root/'reproducibility_artifact/data/research.json';p.write_text('{}')
  with self.assertRaises(AssertionError):verify(root)
 def test_rehashed_scientific_edit_is_still_rejected(self):
  root=self.copy();name='reproducibility_artifact/data/research.json';(root/name).write_text('{}')
  manifest=json.loads((root/'PUBLICATION_MANIFEST.json').read_text())
  for r in manifest:
   if r['path']==name:r.update(sha256=hashlib.sha256(b'{}').hexdigest(),bytes=2)
  (root/'PUBLICATION_MANIFEST.json').write_text(json.dumps(manifest))
  with self.assertRaisesRegex(AssertionError,'Protected scientific'):verify(root)
 def test_escape_path_is_rejected(self):
  root=self.copy();manifest=json.loads((root/'PUBLICATION_MANIFEST.json').read_text());manifest[0]['path']='../escape.txt'
  (root/'PUBLICATION_MANIFEST.json').write_text(json.dumps(manifest));allow=json.loads((root/'PUBLICATION_ALLOWLIST.json').read_text());allow.append('../escape.txt');(root/'PUBLICATION_ALLOWLIST.json').write_text(json.dumps(allow))
  with self.assertRaises(AssertionError):verify(root)
 def test_only_anonymous_review_links_are_allowed(self):
  root=self.copy();name='review-links.json';(root/name).write_text(json.dumps({'anonymous_repository_url':'https://example.com/identity','anonymous_website_url':None}))
  manifest=json.loads((root/'PUBLICATION_MANIFEST.json').read_text())
  for r in manifest:
   if r['path']==name:r.update(sha256=hashlib.sha256((root/name).read_bytes()).hexdigest(),bytes=(root/name).stat().st_size)
  (root/'PUBLICATION_MANIFEST.json').write_text(json.dumps(manifest))
  with self.assertRaises(AssertionError):verify(root)
 def test_deployment_is_manual_and_actions_are_pinned(self):
  workflow=(ROOT/'.github/workflows/deploy-pages.yml').read_text();triggers=workflow.split('on:',1)[1].split('permissions:',1)[0]
  self.assertIn('workflow_dispatch:',triggers);self.assertNotIn('push:',triggers);self.assertNotIn('pull_request:',triggers)
  for p in (ROOT/'.github/workflows').glob('*.yml'):
   for action in re.findall(r'uses:\s*(\S+)',p.read_text()):self.assertRegex(action,r'^actions/[^@]+@[a-f0-9]{40}$')
  self.assertIn("node-version: '24.21.0'",workflow);self.assertIn('path: site',workflow)
  build=workflow.split('  deploy:',1)[0];self.assertNotIn('pages: write',build);self.assertNotIn('id-token: write',build)
 def test_root_bridge_and_static_entry_are_relative(self):
  self.assertIn('src="./app.js"',(ROOT/'site/index.html').read_text())
  self.assertIn('src="./site/app.js"',(ROOT/'index.html').read_text())
  self.assertIn('content="./site/"',(ROOT/'index.html').read_text())
  self.assertFalse(any(p.suffix=='.map' for p in files(ROOT)))
if __name__=='__main__':unittest.main()
