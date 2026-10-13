#!/usr/bin/env python3
"""Independent calibration/audit counters from retained records; aggregates only."""
import gzip,itertools,json
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[2];source=root/'outputs/observatory_tranco_2026-09-27'
def read(sub,v):
 out={}
 for p in sorted((source/sub/v).glob('*.jsonl.gz')):
  with gzip.open(p,'rt') as f:
   for line in f:
    if line.strip():
     r=json.loads(line);out[r['host']]=r
 return out
cal=json.loads((source/'analysis/calibration_live.json').read_text())['rows'];both=[r for r in cal if r.get('ours_score') is not None and r.get('api_score') is not None]
c={'both_scored':len(both),'exact_score':sum(r['ours_score']==r['api_score'] for r in both),'exact_grade':sum(r['ours_grade']==r['api_grade'] for r in both)};assert c=={'both_scored':195,'exact_score':169,'exact_grade':171}
checks=[];sizes=np.array([k for k in range(10) for _ in itertools.combinations(range(9),k)])
for p in sorted((source/'analysis').glob('release_audit_*.json')):
 q=json.loads(p.read_text());positive=q['baseline']=='1.6.3';a=read('replay',q['baseline']);b=read('replay' if positive else 'candidate_replay',q['candidate']);hosts=sorted(h for h in a if a[h].get('status')=='ok' and b.get(h,{}).get('status')=='ok')
 stats={'sites_compared':len(hosts),'score_changed':sum(a[h]['score']!=b[h]['score'] for h in hosts),'grade_changed':sum(a[h]['grade']!=b[h]['grade'] for h in hosts)}
 defaults={'cross-origin-opener-policy':'coop-not-implemented','cross-origin-embedder-policy':'coep-not-implemented'}
 stats['test_outcome_changed']=sum(any(a[h]['tests'].get(t,defaults.get(t))!=b[h]['tests'].get(t,defaults.get(t)) for t in set(a[h]['tests'])|set(b[h]['tests'])) for h in hosts)
 for k,v in stats.items():assert q[k]==v,k
 ao=read('remediation_full',q['baseline']);bn=read('remediation_full' if positive else 'candidate_remediation_full',q['candidate']);x=np.array([ao[h]['scores'] for h in hosts],dtype=np.int16);y=np.array([bn[h]['scores'] for h in hosts],dtype=np.int16)
 stats['plan_vectors_differ_sites']=int((x!=y).any(axis=1).sum());assert q['plan_vectors_differ_sites']==stats['plan_vectors_differ_sites']
 for T in [70,90,100]:
  k=np.where(x>=T,sizes,99).min(axis=1);eligible=(x[:,0]<T)&(k<99);family=(x>=T)&(sizes==k[:,None]);bad=(family&(y<T)).sum(axis=1);every=eligible&(bad>0)&(bad==family.sum(axis=1));some=eligible&(bad>0)&~every
  assert int(every.sum())==q[f'plans_T{T}']['status'].get('NONE',0);assert int(some.sum())==q[f'plans_T{T}']['status'].get('SOME',0)
 checks.append({'baseline':q['baseline'],'candidate':q['candidate'],**stats})
d={'calibration':c,'release_audits':checks,'method':'Independent counters over recorded calibration, candidate replay and 512-score vectors; no live request or original analysis imports','status':'passed'}
(root/'reproducibility_artifact/data/audit-reference.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d))
