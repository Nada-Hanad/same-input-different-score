import copy,json,unittest
from pathlib import Path
from prepare import classify,vkey
from validate import validate,ART
class ArtifactTests(unittest.TestCase):
 def setUp(self):self.d=json.loads((ART/'data/research.json').read_text())
 def test_dataset(self):validate(self.d)
 def test_source_status_semantics(self):
  self.assertEqual(classify('NONE'),'every_fails');self.assertEqual(classify('ALL'),'none_fail');self.assertEqual(classify('SOME'),'some_fail')
 def test_semver_numeric(self):self.assertLess(vkey('1.4.9'),vkey('1.4.10'))
 def test_bad_pair_order_rejected(self):
  self.d['pairs'][0],self.d['pairs'][1]=self.d['pairs'][1],self.d['pairs'][0]
  with self.assertRaises(AssertionError):validate(self.d)
 def test_leak_rejected(self):
  self.d['host']='fixture.invalid'
  with self.assertRaises(AssertionError):validate(self.d)
 def test_plan_partition_rejected(self):
  next(p for p in self.d['pairs'] if p['old']=='1.5.2')['plans']['B']['fate']['every_fails']+=1
  with self.assertRaises(AssertionError):validate(self.d)
 def test_synthetic_bonus_and_floor(self):
  for x in json.loads((ART/'fixtures/scoring-boundaries.json').read_text())['cases']:
   u=100+sum(v for v in x['modifiers'] if v<=0);s=max(0,u+sum(v for v in x['modifiers'] if v>0)*(u>=90))
   self.assertEqual(u,x['uncurved']);self.assertEqual(s,x['score'])

class ScientificRegressionTests(unittest.TestCase):
 def setUp(self):self.d=json.loads((ART/'data/research.json').read_text())
 def test_published_scientific_data_has_no_manuscript_metadata(self):
  self.assertNotIn('manuscript',self.d);self.assertNotIn('paper_available',self.d)
  self.assertEqual(len(self.d['manifest']),20)
  for entry in self.d['manifest']:self.assertNotIn('manuscript_sha256',entry)
 def test_registered_corrected_exposure(self):
  p=next(x for x in self.d['pairs'] if x['old']=='1.3.8');self.assertEqual(p['E'],0);self.assertEqual(p['exposure']['registered'],0);self.assertEqual(p['exposure']['corrected'],41);self.assertEqual(p['exposure']['corrected_ci95'],[0.0113,0.1488]);self.assertEqual(p['T'],32);self.assertEqual(p['n_T_outside_E'],32)
 def test_pair_metrics_independent_baseline(self):
  import csv
  with (ART/'data/release-pair-baseline.csv').open() as f: rows=list(csv.DictReader(f))
  self.assertEqual(len(rows),26)
  for a,b in zip(self.d['pairs'],rows):
   self.assertEqual(a['pair'],b['pair'])
   for k in ['E','T','S','G','n_both_ok']:self.assertEqual(a[k],int(b[k]))
 def test_a_aplus_identity_and_thresholds(self):
  i=self.d['a_aplus_identity'];self.assertEqual(i['thresholds'],{'A':90,'A+':100});self.assertEqual(i['union']['intersection'],132);self.assertTrue(i['union']['same_websites']);self.assertEqual(len(i['pairs']),13)
  for p in i['pairs']:self.assertTrue(p['same_websites']);self.assertEqual(p['A'],p['A+']);self.assertEqual(p['A_only'],0);self.assertEqual(p['A+_only'],0)
 def test_coverage_and_restoration(self):
  self.assertEqual(sum(p['plans']['B']['scope']=='full-corpus' for p in self.d['pairs']),13);self.assertEqual(sum(p['plans']['B']['scope']=='control-sample' for p in self.d['pairs']),13)
  for p in self.d['pairs']:
   for x in p['plans'].values():
    if x['scope']=='full-corpus':r=x['restoration'];self.assertEqual(r['failing_websites'],r['any_subset_restores']+r['no_subset_reaches']);self.assertEqual(r['failing_websites'],x['fate'].get('every_fails',0)+x['fate'].get('some_fail',0))
    else:self.assertIsNone(x['eligible']);self.assertNotIn('restoration',x)
 def test_expected_real_scorer_outputs(self):
  x=self.d['synthetic_replay'];self.assertEqual(x['network_attempts'],0);self.assertEqual([x['scoring_rule'][k]['score'] for k in ['old','new']],[120,125]);self.assertEqual([x['parser'][k]['score'] for k in ['old','new']],[65,20]);self.assertEqual(x['plan']['subsets_evaluated_per_release'],512);self.assertTrue(x['plan']['every_tied_plan_fails']);self.assertFalse(x['plan']['any_new_subset_reaches'])
 def test_all_three_access_categories(self):
  self.assertEqual({x['access_category'] for x in self.d['manifest']},{'Included and downloadable','Reproducible using public fixtures','Restricted original data required'})
 def test_bundle_verifier_rejects_tamper(self):
  import tempfile,hashlib
  from verify_bundle import verify
  with tempfile.TemporaryDirectory() as t:
   p=Path(t);(p/'reproducibility_artifact').mkdir();(p/'reproducibility_artifact/README.md').write_text('safe');h=hashlib.sha256(b'safe').hexdigest();(p/'BUNDLE_MANIFEST.json').write_text(json.dumps([{'path':'reproducibility_artifact/README.md','sha256':h}]))
   self.assertEqual(verify(p)['files'],1);(p/'reproducibility_artifact/README.md').write_text('tampered')
   with self.assertRaises(AssertionError):verify(p)

if __name__=='__main__':unittest.main()
