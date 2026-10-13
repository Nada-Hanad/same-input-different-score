#!/usr/bin/env python3
"""Standalone checks on the included aggregates; no private inputs required."""
import json,re
from pathlib import Path
ART=Path(__file__).resolve().parents[1]

def validate(d):
 assert d['schema_version']==1
 s=d['summary'];p=d['pairs'];v=[r['release'] for r in d['releases']]
 assert len(v)==27 and len(set(v))==27
 assert v==sorted(v,key=lambda x:tuple(map(int,x.split('.'))))
 assert len(p)==26 and len({x['pair'] for x in p})==26
 assert [x['pair'] for x in p]==[f'{a}->{b}' for a,b in zip(v,v[1:])]
 assert sum(x['n_both_ok'] for x in p)==s['comparisons']==422864
 assert sum(x['S'] for x in p)==s['scores']==393
 assert sum(x['G'] for x in p)==s['grades']==278
 assert s['scored']==16264 and s['collected']==20613
 assert s['unique_failing']=={'B':125,'A':132,'A+':132}
 for x in p:
  assert x['n_both_ok']==s['scored']
  assert all(0<=x[k]<=x['n_both_ok'] for k in ['E','T','S','G'])
  assert x['G']<=x['S']
  assert sum(x['delta'].values())==x['S'] and sum(x['grade_moves'].values())==x['G']
  for z in x['weighted_top1M'].values():
   assert 0<=z['ci95'][0]<=z['pct']<=z['ci95'][1]<=100
  for z in x['plans'].values():
   if z['scope']=='full-corpus':
    assert sum(z['fate'].values())==z['eligible']
    assert z['eligible']+z['not_needed_under_old']+z['out_of_reach_under_old']==s['scored']
    assert z['any_invalid_base_unchanged']<=z['fate'].get('every_fails',0)+z['fate'].get('some_fail',0)
   else:assert z['n']==2205 and z['eligible'] is None and sum(z['fate'].values())==0
 for v,g in d['grade_distributions'].items():
  assert sum(g['counts'].values())==s['scored']
  assert abs(sum(g['weighted_fraction'].values())-1)<1e-12
  assert g['ci95'] is None
 assert not {'manuscript','paper_available','discrepancies'}.intersection(d), 'publication metadata is not scientific input'
 exposure=next(x for x in p if x['old']=='1.3.8')['exposure'];assert exposure['registered']==0 and exposure['corrected']==41 and exposure['corrected_ci95']==[0.0113,0.1488]
 assert d['a_aplus_identity']['union']['same_websites'] and d['a_aplus_identity']['union']['intersection']==132
 assert {e['access_category'] for e in d['manifest']}=={'Included and downloadable','Reproducible using public fixtures','Restricted original data required'}
 parser=next(x for x in p if x['old']=='1.5.2')
 assert parser['plans']['B']['fate']['every_fails']==83 and parser['plans']['B']['any_invalid_base_unchanged']==18
 assert d['gates']['live']['pass'] is False and d['gates']['live']['exact_score']==169
 assert d['gates']['compatibility']['pass_as_worded'] is False
 for a in d['audits']:
  assert a['sites_compared']==s['scored']
  for z in a['plans'].values():assert sum(z['fate'].values())==z['eligible']
 assert len({x['id'] for x in d['manifest']})==len(d['manifest'])
 def scan(x):
  if isinstance(x,dict):
   assert not {'host','hostname','headers','body','html','credentials','raw_cookie','ours_at','api_at'}.intersection(x),'restricted field exported'
   for v in x.values():scan(v)
  elif isinstance(x,list):
   for v in x:scan(v)
  elif isinstance(x,str):
   assert '/Users/' not in x and '/home/' not in x
   assert not re.search(r'(?i)([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|set-cookie\s*:|authorization\s*:|bearer\s+[A-Z0-9._-]{12,})',x)
 scan(d)
 return {'status':'passed','pairs':len(p),'major_counts':'393 scores / 278 grades / B 125 / A 132 / parser B 83, unchanged 18','scope':'Aggregate consistency and privacy checks; not a raw-response rerun.'}
if __name__=='__main__':print(json.dumps(validate(json.loads((ART/'data/research.json').read_text())),indent=2))
