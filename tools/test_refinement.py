"""Curated public documentation, scientific preservation and archive regressions."""
import csv,json,unittest,zipfile
from pathlib import Path
from verify_publication import ROOT
from curated_release import verify_curated,verify_links,FIGURE_PDFS
from sync_public import DOCS
class RefinementTests(unittest.TestCase):
 def test_figure_correspondence_and_values(self):
  references=json.loads((ROOT/'docs/figure-references.json').read_text())
  self.assertEqual([f['number'] for f in references['figures']],[1,2,3])
  self.assertEqual(references['figures'][0]['generated_assets'],[])
  self.assertEqual([f['figure_values_key'] for f in references['figures'] if f['kind']=='numerical result'],['fig_cascade','fig_remediation_plan_failures'])
  self.assertNotIn('manuscript_sha256',references)
  self.assertEqual(len(json.loads((ROOT/'reproducibility_artifact/figures/figure-values.json').read_text())['values']),61)
 def test_four_canonical_documents_and_generated_hosting_copies(self):
  self.assertEqual({p.name for p in (ROOT/'docs').glob('*.md')},set(DOCS))
  from download_integrity import verify_downloads
  self.assertEqual(verify_downloads(ROOT)['status'],'passed')
 def test_all_26_classes_and_original_csv_remain_consistent(self):
  research=json.loads((ROOT/'reproducibility_artifact/data/research.json').read_text());rows=list(csv.DictReader((ROOT/'reproducibility_artifact/data/release-pair-baseline.csv').read_text().splitlines()))
  self.assertEqual(len(rows),26);self.assertEqual([(p['pair'],p['class']) for p in research['pairs']],[(p['pair'],p['class']) for p in rows])
  self.assertEqual({k:sum(p['class']==k for p in research['pairs']) for k in ['null','refactor','defensive','scoring']},{'null':14,'refactor':4,'defensive':2,'scoring':6})
 def test_no_manuscript_or_internal_report_is_distributed(self):self.assertEqual(verify_curated(ROOT)['manuscripts'],0)
 def test_archive_is_standalone_with_scientific_source_fixtures_and_tests(self):
  with zipfile.ZipFile(ROOT/'downloads/scientific-artifact.zip') as archive:
   names=set(archive.namelist());prefix='same_input_artifact/'
   for name in ['BUNDLE_MANIFEST.json','SCIENTIFIC_MANIFEST.json','docs/REPRODUCIBILITY.md','reproducibility_artifact/scripts/test_artifact.py','reproducibility_artifact/source/observatory_replay/remediate.mjs','reproducibility_artifact/examples/flooring-input.json','reproducibility_artifact/examples/flooring-expected.json']:self.assertIn(prefix+name,names)
   self.assertFalse(any(name.endswith('.zip') for name in names))
   for name in names:
    if name.endswith('.pdf'):self.assertIn(Path(name).name,FIGURE_PDFS)
 def test_failed_gates_coverage_and_analysis_status_remain_visible(self):
  research=json.loads((ROOT/'reproducibility_artifact/data/research.json').read_text());self.assertFalse(research['gates']['live']['pass']);self.assertEqual(research['gates']['live']['exact_score'],169);self.assertFalse(research['gates']['compatibility']['pass_as_worded']);self.assertEqual(len(research['actions']),9)
  methods=(ROOT/'docs/METHODS_AND_LIMITATIONS.md').read_text()
  for text in ['169/195','2,205','512','exploratory','restricted','90%','Local hashes']:self.assertIn(text,methods)
 def test_all_document_and_evidence_links_resolve(self):self.assertEqual(verify_links(ROOT)['status'],'passed')
 def test_owner_review_links_are_retained(self):
  links=json.loads((ROOT/'review-links.json').read_text());self.assertEqual(links['anonymous_website_url'],'https://anonymous.4open.science/w/web-scorer-release-audit/');self.assertEqual(links['anonymous_repository_url'],'https://anonymous.4open.science/r/web-scorer-release-audit/')
  for link in links.values():self.assertIn(link,(ROOT/'README.md').read_text())
 def test_pdf_disguised_as_an_unapproved_file_is_rejected(self):
  import tempfile,shutil
  from verify_publication import files
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   for path in files(ROOT):
    out=root/path.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,out)
   (root/'unexpected.dat').write_bytes(b'%PDF-1.7 hidden manuscript')
   with self.assertRaisesRegex(AssertionError,'unapproved PDF'):verify_curated(root)
 def test_a_removed_document_link_is_rejected(self):
  import tempfile,shutil
  from verify_publication import files
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   for path in files(ROOT):
    out=root/path.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,out)
   with (root/'docs/FIGURES.md').open('a') as stream:stream.write('\n[Removed](MANUSCRIPT_ACTIONS.md)\n')
   with self.assertRaisesRegex(AssertionError,'Broken public link'):verify_links(root)
if __name__=='__main__':unittest.main()
