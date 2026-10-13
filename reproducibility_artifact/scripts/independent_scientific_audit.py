#!/usr/bin/env python3
"""Independent reference calculation from restricted saved vectors, never imports the exporter.
Run only in the retained workspace: python3.11 ... --root . --out <new-json>.
No scorer execution, network requests or original-data writes. Output contains aggregate counts only.
"""
import argparse,csv,gzip,hashlib,itertools,json
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
FRAME={'T1':10000,'T2':40000,'T3':50000,'T4':400000,'T5':500000}
TARGETS={'B':70,'A':90,'A+':100}

def rows(path):
 for p in sorted(path.glob('*.jsonl.gz')):
  with gzip.open(p,'rt') as f:
   for line in f:
    if line.strip():yield json.loads(line)
def equal(a,b,label):
 assert a==b,label

def run(root):
 source=root/'outputs/observatory_tranco_2026-09-27';analysis=source/'analysis'
 exported=json.loads((root/'reproducibility_artifact/data/research.json').read_text())
 original=json.loads((analysis/'results.json').read_text())
 plans=json.loads((analysis/'plan_validity.json').read_text())
 pop=json.loads((analysis/'aggregate_drift.json').read_text())
 versions=[r['release'] for r in exported['releases']]
 replay={v:{r['host']:r for r in rows(source/'replay'/v) if r.get('status')=='ok'} for v in versions}
 hosts=sorted(set.intersection(*(set(x) for x in replay.values())))
 equal(len(hosts),16264,'fixed cohort');strata={h:replay[versions[0]][h]['stratum'] for h in hosts}
 defaults={'cross-origin-opener-policy':'coop-not-implemented','cross-origin-embedder-policy':'coep-not-implemented'}
 pairchecks=[];score_union=set();per_site=Counter()
 for old,new in zip(versions,versions[1:]):
  key=f'{old}->{new}';counts=Counter();st=defaultdict(Counter);individual=Counter()
  for h in hosts:
   a,b=replay[old][h],replay[new][h];changed=[]
   for t in set(a['tests'])|set(b['tests']):
    aa=a['tests'].get(t,defaults.get(t));bb=b['tests'].get(t,defaults.get(t))
    if aa!=bb:changed.append(t);individual[t]+=1
   flags={'T':bool(changed),'S':a['score']!=b['score'],'G':a['grade']!=b['grade']}
   for t in [65,70,90,100]:flags[f'X{t}']=(a['score']>=t)!=(b['score']>=t)
   for k,b_ in flags.items():counts[k]+=b_;st[strata[h]][k]+=b_
   st[strata[h]]['n']+=1
   if flags['S']:score_union.add(h);per_site[h]+=1
  p=next(x for x in original['pairs'] if x['pair']==key)
  for k,n in counts.items():equal(n,p[k],f'{key} {k}')
  equal(dict(individual),p['tests_changed'],f'{key} individual outcomes')
  for s in st:
   for k,n in st[s].items():equal(n,p['per_stratum'][s][k],f'{key} stratum')
  weighted={k:round(sum(FRAME[s]*st[s][k]/st[s]['n'] for s in FRAME)/10000,4) for k in ['T','S','G']}
  for k,w in weighted.items():equal(w,p['weighted_top1M'][k]['pct'],f'{key} weighted {k}')
  pairchecks.append({'pair':key,**dict(counts),'individual_changed_tests':sum(individual.values()),'weighted_pct':weighted})
 # Independently reconstruct all 512 plan families from the stored score vectors.
 sizes=np.array([len(c) for k in range(10) for c in itertools.combinations(range(9),k)])
 full_versions=sorted({v for p in plans['consecutive_pairs'] for v in p.split('->')},key=lambda v:tuple(map(int,v.split('.'))))
 vectors={}
 for v in full_versions:
  records={r['host']:r['scores'] for r in rows(source/'remediation_full'/v) if r.get('status')=='ok'}
  equal(set(records),set(hosts),f'{v} action vectors');vectors[v]=np.array([records[h] for h in hosts],dtype=np.int16)
  equal(vectors[v][:,0].tolist(),[replay[v][h]['score'] for h in hosts],f'{v} base vector')
 union={t:set() for t in TARGETS};unchanged_version_union={t:set() for t in TARGETS};pc=[]
 algorithm={r['release']:int(r['algorithm_version']) for r in exported['releases']}
 for pair,p in plans['consecutive_pairs'].items():
  old,new=pair.split('->');a,b=vectors[old],vectors[new];target_checks={};affected={}
  for target,T in TARGETS.items():
   sufficient=a>=T;minimum=np.min(np.where(sufficient,sizes[None,:],99),axis=1)
   eligible=(a[:,0]<T)&(minimum<99);family=sufficient&(sizes[None,:]==minimum[:,None]);invalid=family&(b<T)
   total=family.sum(axis=1);bad=invalid.sum(axis=1);some=eligible&(bad>0)&(bad<total);every=eligible&(bad==total)&(bad>0);fail=eligible&(bad>0)
   stats={'eligible':int(eligible.sum()),'plans_total':int(total[eligible].sum()),'plans_invalid':int(bad[eligible].sum()),'every_fails':int(every.sum()),'some_fail':int(some.sum()),'none_fail':int((eligible&~fail).sum()),'unchanged_original':int((fail&(a[:,0]==b[:,0])).sum()),'unreachable_affected':int((fail&(b.max(axis=1)<T)).sum())}
   q=p[f'all512_T{T}'];equal(stats['eligible'],q['eligible'],pair+' eligible');equal(stats['plans_total'],q['plans_total'],pair+' plans');equal(stats['plans_invalid'],q['plans_invalid'],pair+' invalid plans')
   for k,status in [('every_fails','NONE'),('some_fail','SOME'),('none_fail','ALL')]:equal(stats[k],q['status'].get(status,0),pair+' '+status)
   equal(stats['unchanged_original'],q['any_invalid_base_unchanged'],pair+' unchanged')
   affected[target]={hosts[i] for i in np.flatnonzero(fail)};union[target]|=affected[target]
   if algorithm[old]==algorithm[new]:unchanged_version_union[target]|=affected[target]
   target_checks[target]=stats
  equal(affected['A'],affected['A+'],pair+' A/A+ identities')
  pc.append({'pair':pair,'targets':target_checks,'A_Aplus_same_set':True})
 for t,T in TARGETS.items():equal(len(union[t]),plans['union_over_consecutive_pairs'][f'T{T}']['sites_with_failing_plan'],t+' union')
 # Weight every recorded main-sequence population level from actual replay records.
 tranco=[h for h in hosts if strata[h] in FRAME];equal(len(tranco),pop['sites'],'Tranco denominator');group={s:[h for h in tranco if strata[h]==s] for s in FRAME}
 def metric(r,k):
  if k=='mean score':return r['score']
  if k=='B or better':return int(r['score']>=70)
  if k=='A or better':return int(r['score']>=90)
  if k=='A+':return int(r['score']>=100)
  if k=='F':return int(r['score']<25)
  if k.startswith('penalised by '):return int(r['mods'].get(k[13:],0)<0)
  if k.startswith('outcome '):return int(k[8:] in r['tests'].values())
  raise ValueError(k)
 level_count=0
 for v in versions:
  for k,(point,ci) in pop['levels'][v].items():
   ref=sum(FRAME[s]*sum(metric(replay[v][h],k) for h in group[s])/len(group[s]) for s in FRAME)/1e6
   assert abs(ref-point)<1e-12,(v,k);level_count+=1
 # Independent paired-bootstrap reference using original cohort ordering and recorded seed/draws.
 intervals=[]
 for old,new,k in [('1.5.2','1.5.3','outcome sri-not-implemented-and-external-scripts-not-loaded-securely'),('1.3.2','1.7.1','F'),('1.3.2','1.7.1','mean score')]:
  rng=np.random.default_rng(20260927);boot=np.zeros(2000);point=0
  for s in FRAME:
   delta=np.array([metric(replay[new][h],k)-metric(replay[old][h],k) for h in group[s]],dtype=float)
   picks=rng.integers(len(delta),size=(2000,len(delta)));boot+=FRAME[s]*delta[picks].mean(axis=1)/1e6;point+=FRAME[s]*delta.mean()/1e6
  ci=np.quantile(boot,[.025,.975]);q=pop['changes'][f'registered: {old} -> {new}'][k]
  assert abs(q['change']-point)<1e-12;assert np.allclose(ci,q['ci95'],rtol=0,atol=1e-12),(k,ci,q['ci95'])
  intervals.append({'pair':f'{old}->{new}','metric':k,'change':point,'ci95':ci.tolist(),'draws':2000,'seed':20260927})
 result={'scope':'Independent saved-vector and stratified reference calculation; no exporter/analysis imports, no empirical scorer rerun. Host identities stay local.','release_pairs':pairchecks,'plans':pc,'unique_score_changed':len(score_union),'score_change_frequency':dict(Counter(per_site.values())),'plan_unions':{t:len(x) for t,x in union.items()},'unchanged_algorithm_plan_unions':{t:len(x) for t,x in unchanged_version_union.items()},'A_Aplus_union_same_set':union['A']==union['A+'],'population_levels_verified':level_count,'population_denominator':len(tranco),'paired_intervals':intervals,'status':'passed'}
 return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=run(a.root.resolve());a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({k:v for k,v in d.items() if k not in ['release_pairs','plans','paired_intervals']},indent=2))
