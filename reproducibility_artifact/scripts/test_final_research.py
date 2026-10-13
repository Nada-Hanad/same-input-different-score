import copy,csv,hashlib,json,tempfile,unittest
from pathlib import Path
from validate import validate,ART
from reference_aggregates import reference
from verify_bundle import verify
class FinalResearchTests(unittest.TestCase):
 def setUp(self):self.d=json.loads((ART/'data/research.json').read_text())
 def test_negative_release_order(self):
  self.d['releases'][0],self.d['releases'][1]=self.d['releases'][1],self.d['releases'][0]
  with self.assertRaises(AssertionError):validate(self.d)
 def test_negative_plan_partition(self):
  p=next(p for p in self.d['pairs'] if p['plans']['B']['scope']=='full-corpus');p['plans']['B']['fate']['every_fails']=999
  with self.assertRaises(AssertionError):validate(self.d)
 def test_negative_missing_summary(self):
  del self.d['summary']['scores']
  with self.assertRaises(KeyError):validate(self.d)
 def test_corrupted_manifest_is_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);p=root/'reproducibility_artifact/data/research.json';p.parent.mkdir(parents=True);p.write_text('{}')
   (root/'BUNDLE_MANIFEST.json').write_text(json.dumps([{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]))
   verify(root);p.write_text('{"corrupted":true}')
   with self.assertRaises(AssertionError):verify(root)
 def test_unlisted_file_is_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'BUNDLE_MANIFEST.json').write_text('[]');(root/'secret.txt').write_text('unlisted')
   with self.assertRaises(AssertionError):verify(root)
 def test_independent_public_reference(self):
  r=reference(self.d,list(csv.DictReader((ART/'data/release-pair-baseline.csv').read_text().splitlines())),json.loads((ART/'data/independent-audit.json').read_text()));self.assertEqual(r['status'],'passed')
 def test_flooring_fixture(self):
  x=self.d['synthetic_flooring'];self.assertEqual([x['original'][k]['score'] for k in ['old','new']],[0,0]);self.assertEqual([x['original'][k]['uncurved'] for k in ['old','new']],[-35,-80]);self.assertEqual(x['plan']['minimum_actions'],3);self.assertEqual(len(x['plan']['tied_minimum_plans']),1);self.assertTrue(x['plan']['every_tied_plan_fails']);self.assertEqual(x['plan']['maximum_new_score'],30)
 def test_plotted_numerical_values(self):
  values=json.loads((ART/'figures/figure-values.json').read_text())['values'];pairs={p['pair']:p for p in self.d['pairs']}
  for r in values:
   if r['figure']=='fig_remediation_plan_failures':
    f=pairs[r['pair']]['plans'][r['target']]['fate'];self.assertEqual(r['every'],f.get('every_fails',0));self.assertEqual(r['some'],f.get('some_fail',0))
   if r['figure']=='fig_cascade':
    p=pairs[r['pair']];q=p['exposure']['corrected_weighted'] if r['metric']=='E' and p['exposure']['corrected'] is not None else p['weighted_top1M'][r['metric']];self.assertEqual(r['value'],q['pct']);self.assertEqual(r['ci95'],q['ci95'])
 def test_deferred_population_matches_full(self):
  public=ART.parent/'research_companion/public/data';core=json.loads((public/'research-core.json').read_text());extra=json.loads((public/'population.json').read_text());self.assertEqual(core['population']['levels'],{});self.assertEqual(extra['population'],self.d['population']);self.assertEqual(core['summary'],self.d['summary'])
 def test_synthetic_cookie_contract(self):
  x=json.loads((ART/'examples/flooring-input.json').read_text());c=x['session']['jar']['cookies'];self.assertEqual(len(c),1);self.assertEqual(c[0]['value'],'synthetic-only');self.assertEqual(c[0]['domain'],'fixture.invalid')
