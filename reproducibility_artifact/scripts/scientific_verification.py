"""Independent local checks; exports only metadata and aggregate set comparisons."""
import gzip,hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plan_identity_check(source):
 plans=json.loads((source/'plan_validity.json').read_text());unions={90:set(),100:set()};comparisons=[];restoration={}
 for pair,p in plans['consecutive_pairs'].items():
  sets={90:set(),100:set()};counts={90:{'NONE':0,'SOME':0},100:{'NONE':0,'SOME':0}};restore={T:{'any_subset_restores':0,'no_subset_reaches':0,'failing_websites':0} for T in [70,90,100]}
  f=source/'plan_validity_units'/f"{pair.replace('->','_to_')}.jsonl.gz"
  if f.exists():
   with gzip.open(f,'rt') as rows:
    for line in rows:
     u=json.loads(line);T=u['target'];assert T in [70,90,100]
     assert u['score_old']<T and all(s>=T for s in u['plan_scores_old'])
     assert all(len(a)==u['k_old'] for a in u['plans_old'])
     if u['status']!='ALL':
      assert all(x['score_new']<T for x in u['invalid_plans'])
      assert (len(u['invalid_plans'])==len(u['plans_old']))==(u['status']=='NONE')
      restore[T]['failing_websites']+=1;restore[T]['no_subset_reaches' if u['k_new'] is None else 'any_subset_restores']+=1
      if T in sets:sets[T].add(u['host']);unions[T].add(u['host']);counts[T][u['status']]+=1
  else:assert p['vectors_differ_sites']==0
  for T in sets:
   for cls in ['NONE','SOME']:assert counts[T][cls]==p[f'all512_T{T}']['status'].get(cls,0)
  comparisons.append({'pair':pair,'A':len(sets[90]),'A+':len(sets[100]),'same_websites':sets[90]==sets[100],'intersection':len(sets[90]&sets[100]),'A_only':len(sets[90]-sets[100]),'A+_only':len(sets[100]-sets[90]),'classifications':{str(T):counts[T] for T in sets},'scope':'13 full-corpus pairs; identities checked locally and not exported'})
  restoration[pair]={label:restore[T] for label,T in [('B',70),('A',90),('A+',100)]}
 return {'pairs':comparisons,'union':{'A':len(unions[90]),'A+':len(unions[100]),'same_websites':unions[90]==unions[100],'intersection':len(unions[90]&unions[100])},'thresholds':{'A':90,'A+':100},'limitations':'Equality of affected sets is observed in these 13 pairs, not a general equivalence of target grades or tied plan families.'},restoration
