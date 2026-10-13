#!/usr/bin/env python3
"""Export explicit aggregate fields only. Never copy raw input records."""
import argparse, csv, gzip, hashlib, json
from collections import Counter, defaultdict
from pathlib import Path
from environment_snapshot import snapshot
from scientific_verification import plan_identity_check
ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'reproducibility_artifact'
SOURCE = ROOT / 'outputs/observatory_tranco_2026-09-27/analysis'
PACK = ROOT / 'directions/recourse_invalidation/reference_pack/Observatory_paper_reference_2026-10-09'
FRAME = {'T1':10000,'T2':40000,'T3':50000,'T4':400000,'T5':500000}
TARGETS = {'B':70, 'A':90, 'A+':100}

def read(p): return json.loads(p.read_text())
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def vkey(v): return tuple(map(int,v.split('.')))
def classify(status):
 return {'NONE':'every_fails','SOME':'some_fail','ALL':'none_fail'}[status]
def pick(d, keys): return {k:d[k] for k in keys if k in d}
def write(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
def safe_plan(d):
 return pick(d,['eligible','not_needed_under_old','lost_without_plan','out_of_reach_under_old','plans_total','plans_invalid','units_with_ties','category','any_invalid_base_unchanged','changed_base_unchanged','additional_effort_min','additional_effort_max','optimal_plan_slack','invalid_plan_slack','robust_margin_5','robust_margin_10','weighted_any_invalid_all_sites','weighted_any_invalid_eligible','weighted_count_changed_all_sites','R3_scanner_guided']) | {'fate':{classify(k):v for k,v in d['status'].items()}}

def recompute(results,plans,versions):
 counts={p['pair']:Counter() for p in results['pairs']};seen=set();n=0
 grades={v:defaultdict(Counter) for v in versions}
 with gzip.open(PACK/'derived/scores_by_release.csv.gz','rt') as f:
  for row in csv.DictReader(f):
   if row['collection']!='scored': continue
   assert row['host'] not in seen,'duplicate website';seen.add(row['host']);n+=1
   for v in versions: grades[v][row['stratum']][row[f'grade_{v}']]+=1
   for old,new in zip(versions,versions[1:]):
    c=counts[f'{old}->{new}'];c['S']+=row[f'score_{old}']!=row[f'score_{new}'];c['G']+=row[f'grade_{old}']!=row[f'grade_{new}']
 assert n==16264
 for p in results['pairs']:
  assert counts[p['pair']]['S']==p['S'] and counts[p['pair']]['G']==p['G'],p['pair']
 unions={t:set() for t in TARGETS};unchanged_union={t:set() for t in TARGETS};unit_counts={};kcounts={}
 for pair,p in plans['consecutive_pairs'].items():
  c={t:Counter() for t in TARGETS};ks={t:Counter() for t in TARGETS};seen_units=set()
  f=SOURCE/'plan_validity_units'/f"{pair.replace('->','_to_')}.jsonl.gz"
  if f.exists():
   with gzip.open(f,'rt') as rows:
    for line in rows:
     r=json.loads(line);tg=next(t for t,x in TARGETS.items() if x==r['target']); ident=(r['host'],tg)
     assert ident not in seen_units;seen_units.add(ident)
     assert r['score_old']<r['target']
     assert all(score>=r['target'] for score in r['plan_scores_old'])
     assert all(len(plan)==r['k_old'] for plan in r['plans_old'])
     assert 0<=r['k_old']<=9
     if r['status']!='ALL':
      assert r['invalid_plans'];assert all(x['score_new']<r['target'] for x in r['invalid_plans'])
      assert (len(r['invalid_plans'])==len(r['plans_old']))==(r['status']=='NONE')
      c[tg][classify(r['status'])]+=1;unions[tg].add(r['host'])
      if r['score_old']==r['score_new']: c[tg]['unchanged']+=1
     ks[tg][f"{r['k_old']} → {r['k_new'] if r['k_new'] is not None else 'unreachable'}"]+=1
   for tg,T in TARGETS.items():
    d=p[f'all512_T{T}']; assert c[tg]['every_fails']==d['status'].get('NONE',0); assert c[tg]['some_fail']==d['status'].get('SOME',0); assert c[tg]['unchanged']==d['any_invalid_base_unchanged']
  else:
   assert p['vectors_differ_sites']==0,'missing non-null unit evidence'
  unit_counts[pair]={t:dict(x) for t,x in c.items()};kcounts[pair]={t:dict(x) for t,x in ks.items()}
 for tg,T in TARGETS.items(): assert len(unions[tg])==plans['union_over_consecutive_pairs'][f'T{T}']['sites_with_failing_plan']
 distributions={}
 for v,st in grades.items():
  keys=set().union(*(set(c) for c in st.values()))
  distributions[v]={'counts':{g:sum(c[g] for c in st.values()) for g in keys},'weighted_fraction':{g:sum(FRAME[t]*st[t][g]/sum(st[t].values()) for t in FRAME)/sum(FRAME.values()) for g in keys},'ci95':None,'note':'New companion-derived grade distribution from stored score matrix; frame weights match original estimator; no bootstrap interval generated.'}
 return {'scored_sites':n,'score_changes':sum(c['S'] for c in counts.values()),'grade_changes':sum(c['G'] for c in counts.values()),'unique_failing':{t:len(s) for t,s in unions.items()},'unit_counts':unit_counts,'grade_distributions':distributions},kcounts,unions

def build():
 for name in ['results.json','attribution.json','gates.json']:
  assert digest(SOURCE/name)==digest(PACK/'results'/name),f'frozen/production discrepancy: {name}'
 for name in ['plan_validity.json','aggregate_drift.json']:
  assert digest(SOURCE/name)==digest(PACK/'results/plan_validity'/name),f'frozen/production discrepancy: {name}'
 action_source=(ROOT/'audit/scripts/observatory_replay/remediate.mjs').read_text()
 import re
 csp=re.search(r'const CSP_VALUE = get\("--csp", "([^"]+)"\)',action_source)[1]
 assert read(ART/'examples/action-definitions.json')[0]['value']==csp
 for a in read(ART/'examples/action-definitions.json')[1:-1]:
  assert f'["{a["id"]}", "{a["header"]}", "{a["value"]}"]' in action_source
 identity,restoration=plan_identity_check(SOURCE)
 r=read(SOURCE/'results.json');plans=read(SOURCE/'plan_validity.json');attr=read(SOURCE/'attribution.json');pop=read(SOURCE/'aggregate_drift.json')
 ledger=list(csv.DictReader((PACK/'derived/release_ledger.csv').open()));release=[x for x in ledger if x['on_npm']=='yes']; versions=[x['release'] for x in release]
 assert versions==sorted(set(versions),key=vkey) and len(versions)==27
 verified,kcounts,unions=recompute(r,plans,versions)
 alg={x['release']:int(x['algorithm_version']) for x in release};md={x['release']:x for x in release}
 pairs=[]
 for p in r['pairs']:
  old,new=p['pair'].split('->');full=plans['consecutive_pairs'].get(p['pair']);ctrl=plans['sampled_control_pairs'].get(p['pair']);assert bool(full)!=bool(ctrl)
  pn={}
  for tg,T in TARGETS.items():
   if full: pn[tg]=safe_plan(full[f'all512_T{T}'])|{'scope':'full-corpus','n':plans['n_sites'],'action_count_transitions':kcounts[p['pair']][tg],'restoration':restoration[p['pair']][tg]}
   else:
    assert ctrl['vectors_differ']==0
    pn[tg]={'scope':'control-sample','n':ctrl['sites_compared'],'fate':{'every_fails':0,'some_fail':0},'eligible':None,'note':'Identical 512-score vectors in the 2,205-website control sample. Target-specific eligible denominators are not recorded; full-corpus plan validity is unavailable.'}
  pairs.append(pick(p,['pair','class','n_both_ok','E','T','S','G','n_T_outside_E','tests_changed','delta','grade_moves','per_stratum','weighted_top1M','weighted_scorable','pct_of_both_ok','n_S_without_T'])|{'old':old,'new':new,'algorithm_old':alg[old],'algorithm_new':alg[new],'release':pick(md[new],['changelog_date','scoring_change_from_diff','changelog_scoring_relevant','jsdom_installed_for_replay','htmlparser2_installed_for_replay']),'plans':pn,'exposure':{'recorded':p['E'],'registered':p['E'] if old=='1.3.8' else None,'recorded_status':'D5 pre-replay correction, not the original registered predicate' if old=='1.4.9' else 'Stored condition from original results.json','corrected':read(ART/'data/exposure-reference.json')['counts']['corrected'] if old=='1.3.8' else None,'corrected_ci95':p.get('weighted_top1M_E_unsplit',{}).get('ci95'),'corrected_weighted':p.get('weighted_top1M_E_unsplit'),'correction_status':'Post-analysis parser-faithful correction, documented 28 September 2026 in RESULTS_2026-09-28 §4.2/§4.4; original registered predicate preserved.' if old=='1.3.8' else None},'evidence':['results.json','pairs.csv','plan_validity.json','release_ledger.csv'],'exposure_note':('Registered E=0 misses 32 outcome changes. The parser-faithful correction matches 41 websites and contains all 32 changes (RESULTS_2026-09-28 §4.2–4.4). Corrected weighted exposure and its interval are recorded as weighted_top1M_E_unsplit; no new interval is computed.' if old=='1.3.8' else 'Stored exposure condition; source and dependency closures do not establish an isolated causal effect.')})
 assert len(pairs)==26 and sum(x['n_both_ok'] for x in pairs)==422864
 assert verified['score_changes']==393 and verified['grade_changes']==278 and verified['unique_failing']['B']==125 and verified['unique_failing']['A']==132
 major=[
 ('scale','RQ1','Abstract; §4.2','27 releases; 26 pairs; 16,264 scored websites; 422,864 comparisons','results.json','analyze_revisions.py','fig_location'),
 ('collection','RQ1','§4.2','20,613 actual websites; raw attempted-record counts include three panel comment lines','gates.json','summarize_gates.py',None),
 ('outcomes','RQ1','Abstract; §5.2; Table 2','393 score changes; 278 grade changes across website–release-pair comparisons','results.json','analyze_revisions.py','fig_location'),
 ('version','RQ3','§5.5','294 score changes and 251 grade changes retain the reported algorithm version','results.json','build_reference_pack.py',None),
 ('validation','RQ1','§5.1; Table 1','V1 exact 16,264/16,264; V2 exact 169/195, below 90%; V3 fails as worded','gates.json','summarize_gates.py',None),
 ('attribution','RQ2','§5.3','Zero unexplained outcome changes under the inspected source/dependency-closure analysis','attribution.json','attribution.py',None),
 ('exposure','RQ2','Table 2 footnote','1.3.8–1.4.0: recorded E=0; corrected exposure 41','results.json','analyze_revisions.py',None),
 ('plans','RQ3','§5.4; Figure 3','125 distinct websites with failing B plans; 132 with failing A plans across 13 full-corpus pairs','plan_validity.json','plan_validity.py','fig_plan_fate'),
 ('parser','RQ2 / RQ3','Abstract; §5.3–5.4','1.5.2–1.5.3: 128 score changes, 99 grade changes; every B plan fails for 83 websites, 18 unchanged original scores','plan_validity.json','plan_validity.py','fig_plan_fate'),
 ('repair','RQ3','§5.4','Parser pair: 80 B targets unreachable in nine-action model; three restore with one additional action','plan_validity.json','plan_validity.py',None),
 ('margins','RQ3','§5.4','Displayed margin differs from uncurved margin because of the 90-point bonus threshold','plan_validity.json','plan_validity.py','fig_margins'),
 ('population','RQ1','§5.2','Weighted grade shares, mean scores and outcome prevalence; paired bootstrap change intervals','aggregate_drift.json','aggregate_drift.py',None),
 ('audit','RQ3','§5.5','Positive control and candidate main-093035e3 with dependency contrasts','release_audit_1.7.1_vs_main-093035e3.json','audit_release.py',None),
 ('dependencies','RQ2','§5.3; limitations','Exploratory as-deployed dependency analysis and jsdom parsing probe','jsdom_parse_check.json','jsdom_parse_check.py',None),
 ('sensitivity','RQ3','Limitations','Alternative CSP action sensitivity; nine-action restrictions','plan_validity_sensitivity_csp.json','plan_validity_sensitivity.py',None),
 ('plan-age','RQ3','Follow-up ledger §9','Nonconsecutive plan age analysis is subsequently prespecified, distinct from adjacent pairs','plan_age.csv','plan_validity.py','fig_plan_age')]
 manifest=[]
 for id,rq,loc,claim,file,script,fig in major:
  path=SOURCE/file; sp=ROOT/'audit/scripts/observatory_replay'/script
  manifest.append({'id':id,'rq':rq,'manuscript_location':loc,'claim':claim,'source':str(path.relative_to(ROOT)),'source_sha256':digest(path),'script':str(sp.relative_to(ROOT)),'script_sha256':digest(sp),'figure':(f'directions/recourse_invalidation/figures_2026-10-08/{fig}.pdf' if fig and 'plan' in fig or fig=='fig_margins' else f'directions/recourse_invalidation/figures_2026-09-28/{fig}.pdf' if fig else None),'command':(f'python3 audit/scripts/observatory_replay/{script} --in <isolated-copy-of-corpus> --doc <local-reference-guide> --out <new-output-directory>' if script=='build_reference_pack.py' else f'python3 audit/scripts/observatory_replay/{script} --in <isolated-copy-of-corpus> --baseline 1.7.1 --candidate main-093035e3' if script=='audit_release.py' else f'python3 audit/scripts/observatory_replay/{script} --in <isolated-copy-of-corpus>'),'restricted_inputs':True,'evidence_level':'stored artifact plus inspected producing code; counts independently cross-checked where specified','configuration':'Published releases with installed replay dependencies; exploratory as-deployed configurations kept separate'})
 matrix=PACK/'derived/scores_by_release.csv.gz'
 manifest.append({'id':'grade-distribution','rq':'RQ1','manuscript_location':'Companion-derived view; selected grade groups in manuscript §5.2','claim':'Complete grade distribution derived from stored score matrix, preserving original frame weights; no new intervals','source':str(matrix.relative_to(ROOT)),'source_sha256':digest(matrix),'script':'reproducibility_artifact/scripts/prepare.py','script_sha256':digest(Path(__file__)),'figure':None,'command':'python3 reproducibility_artifact/scripts/prepare.py','restricted_inputs':True,'evidence_level':'New aggregate derived and checked against stored B-or-better levels','configuration':'All 27 stored releases; counts include panel; weighted fractions exclude panel'})
 audits=[]
 for p in sorted(SOURCE.glob('release_audit_*.json')):
  d=read(p); audits.append(pick(d,['baseline','candidate','algorithm_version','sites_compared','status_changes','test_outcome_changed','tests_changed','score_changed','grade_changed','score_moves','grade_moves','weighted_score_changed','weighted_grade_changed','plan_vectors_differ_sites'])|{'plans':{tg:safe_plan(d[f'plans_T{T}']) for tg,T in TARGETS.items()},'source':p.name,'kind':'retrospective positive control' if d['baseline']=='1.6.3' else 'candidate / dependency contrast'})
 gates=read(SOURCE/'gates.json')['gates']
 safe_gates={'storage':pick(gates['V1_storage_fidelity'],['exact','of','pass']),'live':pick(gates['V2_live_calibration'],['exact_score','both_scored','exact_score_rate','pass']),'compatibility':pick(gates['V3_compatibility'],['pass_as_worded','pass_on_inputs_scored_at_collection']),'attribution':gates['V4_attribution'],'memo':gates['remediation_memo']}
 # Recompute the disclosure union without exporting any website identifiers.
 disclosed={tg:set() for tg in TARGETS}
 for pair in plans['consecutive_pairs']:
  old,new=pair.split('->')
  if alg[old]!=alg[new]: continue
  p=SOURCE/'plan_validity_units'/f"{pair.replace('->','_to_')}.jsonl.gz"
  if p.exists():
   with gzip.open(p,'rt') as f:
    for line in f:
     u=json.loads(line)
     if u['status']!='ALL': disclosed[next(t for t,x in TARGETS.items() if x==u['target'])].add(u['host'])
 sample=list(csv.DictReader((PACK/'sample/sample_Y8YJG_20260927.csv').open()))
 collected=len({x['host'] for x in sample if x['host'] and not x['host'].startswith('#')})
 assert collected==20613
 parser_units={t:set() for t in TARGETS}
 with gzip.open(SOURCE/'plan_validity_units/1.5.2_to_1.5.3.jsonl.gz','rt') as f:
  for line in f:
   u=json.loads(line)
   if u['status']!='ALL': parser_units[next(t for t,x in TARGETS.items() if x==u['target'])].add(u['host'])
 wanted=set().union(*parser_units.values()); outcomes={v:{} for v in ['1.5.2','1.5.3']}
 for v in outcomes:
  for f in sorted((SOURCE.parent/'replay'/v).glob('*.jsonl.gz')):
   with gzip.open(f,'rt') as rows:
    for line in rows:
     if not line.strip():continue
     u=json.loads(line)
     if u['host'] in wanted:
      value=u['tests']['subresource-integrity']
      assert u['host'] not in outcomes[v] or outcomes[v][u['host']]==value
      outcomes[v][u['host']]=value
 mechanism_counts={t:dict(Counter(f"{outcomes['1.5.2'][h]} → {outcomes['1.5.3'][h]}" for h in hs)) for t,hs in parser_units.items()}
 summary={'releases':len(versions),'pairs':len(pairs),'scored':verified['scored_sites'],'collected':collected,'comparisons':sum(x['n_both_ok'] for x in pairs),'scores':verified['score_changes'],'grades':verified['grade_changes'],'unique_failing':verified['unique_failing'],'unchanged_algorithm_scores':sum(p['S'] for p in pairs if p['algorithm_old']==p['algorithm_new']),'unchanged_algorithm_grades':sum(p['G'] for p in pairs if p['algorithm_old']==p['algorithm_new']),'unchanged_algorithm_failing':{t:len(x) for t,x in disclosed.items()},'full_plan_pairs':len(plans['consecutive_pairs']),'sampled_plan_pairs':len(plans['sampled_control_pairs'])}
 for v,g in verified['grade_distributions'].items():
  assert abs(sum(g['weighted_fraction'].values())-1)<1e-12
  assert sum(g['counts'].values())==verified['scored_sites']
  assert abs(sum(g['weighted_fraction'].get(k,0) for k in ['B','B+','A-','A','A+'])-pop['levels'][v]['B or better'][0])<1e-12
 for entry in manifest:
  entry['access_category']='Restricted original data required'
  entry['included_dataset']='data/research.json'
  entry['included_dataset_url']='/data/research.json'
  name=Path(entry['script']).name
  entry['script_download_url']='/files/source/observatory_replay/'+name if (ART/'source/observatory_replay'/name).exists() else None
 manifest.append({'id':'synthetic-replay','rq':'RQ2 / RQ3','manuscript_location':'Controlled companion demonstration; not an empirical paper result','claim':'Real scorer fixed-input differences and failing tied B plans on public synthetic responses, including unchanged displayed original scores','source':'reproducibility_artifact/examples/expected.json','source_sha256':digest(ART/'examples/expected.json'),'script':'reproducibility_artifact/examples/run.mjs','script_sha256':digest(ART/'examples/run.mjs'),'figure':None,'command':'node examples/run.mjs','restricted_inputs':False,'evidence_level':'Actual historical assessment-code execution with assertions and denied network access','configuration':'Four exact npm release installations; synthetic empty reference lists','access_category':'Reproducible using public fixtures','included_dataset':'examples/expected.json','included_dataset_url':'/data/synthetic-replay.json'})
 manifest.append({'id':'aggregate-verification','rq':'RQ1 / RQ3','manuscript_location':'Companion artifact validation','claim':'Standalone released aggregate count, partition, unit and privacy validation','source':'reproducibility_artifact/data/research.json','source_sha256':None,'script':'reproducibility_artifact/scripts/validate.py','script_sha256':digest(ART/'scripts/validate.py'),'figure':None,'command':'python3 scripts/validate.py','restricted_inputs':False,'evidence_level':'Validation of included derived data; not raw-response rerun','configuration':'Python standard library only','access_category':'Included and downloadable','included_dataset':'data/research.json','included_dataset_url':'/data/research.json'})
 manifest.append({'id':'paper-figures','rq':'RQ1 / RQ3','manuscript_location':'Figures 2 and 3; supplementary companion margin plot','claim':'Numerical regeneration of the current cascade and tied-plan failure figures from included aggregates','source':'reproducibility_artifact/figures/figure-values.json','source_sha256':digest(ART/'figures/figure-values.json'),'script':'reproducibility_artifact/scripts/figures_public.py','script_sha256':digest(ART/'scripts/figures_public.py'),'figure':'reproducibility_artifact/figures/fig_cascade.pdf','figure_download_url':'/figures/fig_cascade.pdf','script_download_url':'/files/scripts/figures_public.py','command':'make figure-env figures','restricted_inputs':False,'evidence_level':'Public plotting-value regressions and clean isolated figure regeneration','configuration':'Optional isolated Matplotlib3.10.7 and NumPy2.4.6, exact dependency versions; no restricted data or new intervals','access_category':'Included and downloadable','included_dataset':'figures/figure-values.json','included_dataset_url':'/figures/figure-values.json'})
 for entry in manifest:
  entry['result_kind']=('synthetic demonstration' if entry['id']=='synthetic-replay' else 'new derived view' if entry['id'] in ['grade-distribution','aggregate-verification','paper-figures'] else 'exploratory analysis' if entry['id'] in ['population','dependencies','sensitivity','margins','version'] else 'candidate / retrospective audit' if entry['id']=='audit' else 'original experiment')
  entry['verification_method']=('independent saved-vector reconstruction, plus recorded source inspection' if entry['id'] in ['scale','outcomes','plans','parser','repair','version','population','grade-distribution'] else 'real scorer execution and exhaustive assertions' if entry['id']=='synthetic-replay' else 'recorded artifact and producing-code inspection')
  entry['qualification']='Saved-vector checks do not independently recollect inputs or establish external-service agreement. Full empirical replay remains restricted.' if entry['restricted_inputs'] else 'Controlled synthetic execution is distinct from empirical website frequencies.' if entry['id']=='synthetic-replay' else 'Checks released derived data only.'
  if entry['id'] in ['scale','outcomes']:entry['figure']=None
  if entry['id'] in ['plans','parser']:entry['figure']='reproducibility_artifact/figures/fig_remediation_plan_failures.pdf';entry['figure_download_url']='/figures/fig_remediation_plan_failures.pdf'
 data={'schema_version':1,'a_aplus_identity':identity,'actions':read(ART/'examples/action-definitions.json'),'synthetic_replay':read(ART/'examples/expected.json'),'synthetic_flooring':read(ART/'examples/flooring-expected.json'),'title':'Same Input, Different Score','subtitle':'Auditing Release-Induced Changes in Web Security Assessments','summary':summary,'releases':[pick(x,['release','changelog_date','algorithm_version','jsdom_installed_for_replay','htmlparser2_installed_for_replay']) for x in release],'pairs':pairs,'mechanisms':attr['entries'],'population':pop,'audits':audits,'gates':safe_gates,'unions':plans['union_over_consecutive_pairs'],'margins':plans['uncurved_margins'],'parser_mechanism_counts':mechanism_counts,'grade_distributions':verified['grade_distributions'],'manifest':manifest,'missing':['Synthetic real-scorer fixtures are included; empirical website-response fixtures remain restricted.','Control-sample target-specific eligible counts are not recorded.','Full-corpus plan validity for the 13 sampled pairs has not been run.','Most test-outcome prevalence levels have no recorded confidence intervals.','Collection count uses the D10-corrected narrative accounting; raw attempted records number 20,616.','Pre-analysis timestamp is locally hashed, not independently certified.','Source-closure attribution is not a complete isolated mechanism intervention.']}
 write(ART/'data/research.json',data);write(ROOT/'research_companion/public/data/research.json',data)
 write(ROOT/'research_companion/public/data/synthetic-replay.json',data['synthetic_replay'])
 write(ROOT/'research_companion/public/data/synthetic-flooring.json',data['synthetic_flooring'])
 core=data|{'population':{'sites':pop['sites'],'note':pop['note'],'levels':{},'changes':{}},'grade_distributions':{}}
 write(ROOT/'research_companion/public/data/research-core.json',core)
 write(ROOT/'research_companion/public/data/population.json',{'population':pop,'grade_distributions':data['grade_distributions']})
 write(ROOT/'research_companion/public/data/scientific-verification.json',{'a_aplus_identity':identity})
 write(ROOT/'research_companion/public/data/evidence-manifest.json',manifest)
 (ART/'data/release-pair-baseline.csv').write_bytes((SOURCE/'pairs.csv').read_bytes())
 write(ART/'data/scientific-verification.json',{'a_aplus_identity':identity})
 write(ART/'data/environment.json',snapshot(versions))
 write(ART/'data/evidence-manifest.json',manifest);write(ART/'data/verification.json',verified)
 sources=[SOURCE/'results.json',SOURCE/'plan_validity.json',SOURCE/'aggregate_drift.json',SOURCE/'gates.json',SOURCE/'attribution.json',PACK/'derived/release_ledger.csv',PACK/'derived/scores_by_release.csv.gz',PACK/'sample/sample_Y8YJG_20260927.csv']+sorted((SOURCE/'plan_validity_units').glob('*.jsonl.gz'))+sorted(SOURCE.glob('release_audit_*.json'))+sorted((SOURCE.parent/'replay/1.5.2').glob('*.jsonl.gz'))+sorted((SOURCE.parent/'replay/1.5.3').glob('*.jsonl.gz'))
 write(ART/'data/input-hashes.json',[{'path':str(p.relative_to(ROOT)),'sha256':digest(p)} for p in sources])
 # Public documentation excludes source files with raw identifiers, confidential excerpts, or author metadata.
 (ROOT/'research_companion/public/docs').mkdir(exist_ok=True)
 from public_docs import refresh_public_docs
 refresh_public_docs(ROOT,data)
 import shutil
 for name in ['evidence-manifest.json','environment.json','verification.json','scientific-verification.json','source-code-manifest.json','independent-audit.json']:
  fp=ART/'data'/name
  if fp.exists():shutil.copyfile(fp,ROOT/'research_companion/public/data'/name)
 destination=ROOT/'research_companion/public/files/source/observatory_replay'
 destination.mkdir(parents=True,exist_ok=True)
 for fp in (ART/'source/observatory_replay').glob('*'):
  if fp.is_file():shutil.copyfile(fp,destination/fp.name)
 for folder in ['figures','examples']:
  destination=ROOT/'research_companion/public'/folder;destination.mkdir(exist_ok=True)
  files=list((ART/'figures').glob('*')) if folder=='figures' else [ART/'examples'/n for n in ['flooring-input.json','flooring-expected.json','run.mjs','worker.mjs','action-definitions.json']]
  for fp in files:
   if fp.is_file():shutil.copyfile(fp,destination/fp.name)
 (ROOT/'research_companion/public/files/scripts').mkdir(exist_ok=True)
 shutil.copyfile(ART/'scripts/figures_public.py',ROOT/'research_companion/public/files/scripts/figures_public.py')
 shutil.copyfile(ART/'THIRD_PARTY_NOTICES.txt',ROOT/'research_companion/public/THIRD_PARTY_NOTICES.txt')
 public=ROOT/'research_companion/public'
 write(public/'data/download-manifest.json',[{'path':str(f.relative_to(public)),'sha256':digest(f),'bytes':f.stat().st_size} for f in sorted(public.rglob('*')) if f.is_file() and f.name!='download-manifest.json'])
 write(ART/'data/download-manifest.json',read(public/'data/download-manifest.json'))
 print(json.dumps(summary,indent=2))
 return data
if __name__=='__main__': build()
