#!/usr/bin/env python3
"""Independent minimum-plan margin count from restricted uncurved action vectors."""
import gzip,itertools,json
from collections import Counter
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[2];source=root/'outputs/observatory_tranco_2026-09-27';records={}
for p in sorted((source/'remediation_uncurved/1.7.1').glob('*.jsonl.gz')):
 with gzip.open(p,'rt') as f:
  for line in f:
   if line.strip():
    r=json.loads(line);records[r['host']]=r
sizes=np.array([k for k in range(10) for _ in itertools.combinations(range(9),k)])
c=Counter();eligible=0;every_zero=0
for r in records.values():
 a=np.array(r['scores']);u=np.array(r['uncurved']);reach=a>=90;minimum=min(sizes[reach],default=99)
 if a[0]>=90 or minimum==99:continue
 eligible+=1;ix=reach&(sizes==minimum);c.update((u[ix]-90).tolist());every_zero+=bool((u[ix]==90).all())
d={'release':'1.7.1','target':'A','eligible':eligible,'optimal_plans':sum(c.values()),'uncurved_zero_plans':c[0],'every_plan_zero_margin_websites':every_zero,'uncurved_margin':dict(c),'status':'passed','method':'Independent enumeration from saved uncurved vectors; no original analysis imports'}
assert (eligible,sum(c.values()),c[0],every_zero)==(10496,11382,6454,5577)
(root/'reproducibility_artifact/data/margin-reference.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d))
