#!/usr/bin/env python3
"""Small independent public consumer. No exporter or existing validator imports."""
import csv,json
from pathlib import Path
ART=Path(__file__).resolve().parents[1]
FRAME={'T1':10000,'T2':40000,'T3':50000,'T4':400000,'T5':500000}
def reference(d,baseline,audit):
 versions=[r['release'] for r in d['releases']]
 assert versions==sorted(set(versions),key=lambda v:tuple(int(x) for x in v.split('.')))
 assert [p['pair'] for p in d['pairs']]==[a+'->'+b for a,b in zip(versions,versions[1:])]
 old={r['pair']:r for r in baseline}
 for p in d['pairs']:
  for k in ['T','S','G']:assert p[k]==int(old[p['pair']][k]),(p['pair'],k)
  for k in ['E','T','S','G']:
   n=sum(p['per_stratum'][s][k] for s in p['per_stratum']);assert n==p[k]
   weighted=sum(FRAME[s]*p['per_stratum'][s][k]/p['per_stratum'][s]['n'] for s in FRAME)/10000
   assert abs(weighted-p['weighted_top1M'][k]['pct'])<=.000051
  for target,q in p['plans'].items():
   if q['scope']=='full-corpus':
    assert sum(q['fate'].values())==q['eligible']
    assert sum(q.get('category',{}).values())==q['eligible']
    a=next(r for r in audit['plans'] if r['pair']==p['pair'])['targets'][target]
    for k in ['eligible','plans_total','plans_invalid']:assert q[k]==a[k]
    for k in ['every_fails','some_fail','none_fail']:assert q['fate'].get(k,0)==a[k]
    assert q['any_invalid_base_unchanged']==a['unchanged_original']
   else:assert q['eligible'] is None and q['n']==2205
 assert audit['plan_unions']==d['summary']['unique_failing']
 assert audit['A_Aplus_union_same_set']
 return {'status':'passed','method':'Independent standard-library arithmetic over original aggregate CSV, per-stratum counts and separately computed saved-vector audit. Identity checks remain restricted.'}
if __name__=='__main__':
 d=json.loads((ART/'data/research.json').read_text());audit=json.loads((ART/'data/independent-audit.json').read_text())
 print(json.dumps(reference(d,list(csv.DictReader((ART/'data/release-pair-baseline.csv').open())),audit)))
