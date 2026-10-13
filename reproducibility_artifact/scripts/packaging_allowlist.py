"""Explicit approved paths. Unknown files are excluded even inside the artifact directories."""
from pathlib import PurePosixPath
SCRIPTS={'prepare.py','validate.py','environment_snapshot.py','scientific_verification.py','public_docs.py','public_safety.py','package.py','verify_bundle.py','verify_all.sh','test_artifact.py','packaging_allowlist.py','test_release_safety.py','parser_fixture.mjs','independent_scientific_audit.py','verify_exposure_local.py','verify_margins_local.py','verify_audits_local.py','reference_aggregates.py','figures_public.py','test_final_research.py','scientific_integrity.py'}
DATA={'research.json','verification.json','evidence-manifest.json','input-hashes.json','environment.json','scientific-verification.json','source-code-manifest.json','download-manifest.json','release-pair-baseline.csv','research-core.json','research-core.js','population.json','population.js','synthetic-flooring.json','figure-references.json','independent-audit.json','exposure-reference.json','margin-reference.json','audit-reference.json','frontend-licenses.json'}
DOCS={'REPRODUCIBILITY.md','METHODS_AND_LIMITATIONS.md','EVIDENCE_MAP.md','FIGURES.md'}
SOURCES={'input_codec.mjs','stub_retriever.mjs','replay_all.mjs','remediate.mjs','plan_validity.py','analyze_revisions.py','audit_release.py','memo_jsdom.mjs','memo_html_parser.mjs','run_replay.py','aggregate_drift.py','figures.py','plan_validity_figures.py'}
FRONT_SOURCE={'main.tsx','model.ts','model.test.ts','app.test.tsx','components.tsx','style.css'}
VIEWS={'Overview.tsx','Releases.tsx','Plans.tsx','PlanDetails.tsx','WorkedExample.tsx','Mechanisms.tsx','Population.tsx','Audits.tsx','Artifact.tsx'}
EXAMPLES={'README.md','NOTICE.md','worker.mjs','run.mjs','install.mjs','expected.json','action-definitions.json','rule-input.json','parser-input.json','flooring-input.json','flooring-expected.json'}

FIGURES={'fig_cascade.png','fig_cascade.pdf','fig_remediation_plan_failures.png','fig_remediation_plan_failures.pdf','fig_margin_companion.png','fig_margin_companion.pdf','figure-values.json'}
def public_path(parts):
 return parts==['files','scripts','figures_public.py'] or parts==['THIRD_PARTY_NOTICES.txt'] or (len(parts)==2 and parts[0]=='figures' and parts[1] in FIGURES) or (len(parts)==2 and parts[0]=='examples' and parts[1] in EXAMPLES) or (len(parts)==2 and parts[0]=='data' and parts[1] in DATA|{'synthetic-replay.json'}) or (len(parts)==2 and parts[0]=='docs' and parts[1] in DOCS) or (len(parts)==4 and parts[:3]==['files','source','observatory_replay'] and parts[3] in SOURCES)
def allowed(path):
 a=list(PurePosixPath(path).parts)
 if not a or any(x in a for x in ['.git','node_modules','__pycache__','.vite','raw_data','outputs']):return False
 if len(a)==1 and a[0] in ['README.md','LICENSE.md','THIRD_PARTY_NOTICES.md','SCIENTIFIC_MANIFEST.json']:return True
 if a[0]=='docs':return len(a)==2 and a[1] in DOCS|{'figure-references.json'}
 if a[0]=='reproducibility_artifact':
  b=a[1:]
  return (len(b)==1 and b[0] in ['README.md','Makefile','requirements-figures.txt','THIRD_PARTY_NOTICES.txt']) or (len(b)==2 and b[0]=='figures' and b[1] in FIGURES) or (len(b)==2 and b[0]=='scripts' and b[1] in SCRIPTS) or (len(b)==2 and b[0]=='data' and b[1] in DATA) or (len(b)==2 and b[0]=='docs' and b[1] in DOCS) or (len(b)==2 and b[0]=='fixtures' and b[1] in ['parser-input.html','scoring-boundaries.json']) or (len(b)==3 and b[:2]==['source','observatory_replay'] and b[2] in SOURCES) or (len(b)==2 and b[0]=='examples' and b[1] in EXAMPLES) or (len(b)==3 and b[:2]==['examples','lib'] and b[2] in ['input_codec.mjs','stub_retriever.mjs']) or (len(b)==4 and b[:2]==['examples','environments'] and b[2] in ['1.4.9','1.5.0','1.5.2','1.5.3'] and b[3] in ['package.json','package-lock.json'])
 if a[0]=='research_companion':
  b=a[1:]
  return (len(b)==1 and b[0] in ['README.md','.gitignore','.nvmrc','index.html','package.json','package-lock.json','tsconfig.json','vite.config.ts']) or (len(b)==2 and b[0]=='src' and b[1] in FRONT_SOURCE) or (len(b)==3 and b[:2]==['src','views'] and b[2] in VIEWS) or (b and b[0]=='public' and public_path(b[1:])) or b==['dist','index.html'] or (len(b)==3 and b[:2]==['dist','assets'] and b[2].startswith('index-') and PurePosixPath(b[2]).suffix in ['.js','.css']) or (b and b[0]=='dist' and public_path(b[1:]))
 return False
