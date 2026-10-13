# Evidence map

The result-to-evidence explorer uses the same 20 structured entries as `reproducibility_artifact/data/evidence-manifest.json`. Original research paths are provenance identifiers, not accessible URLs. Public links below and in the platform point only to included resources.

| ID / question | Result | Producing code identifier | Access |
|---|---|---|---|
| scale / RQ1 | 27 releases; 26 pairs; 16,264 scored websites; 422,864 comparisons | `audit/scripts/observatory_replay/analyze_revisions.py` | Restricted original data required |
| collection / RQ1 | 20,613 actual websites; raw attempted-record counts include three panel comment lines | `audit/scripts/observatory_replay/summarize_gates.py` | Restricted original data required |
| outcomes / RQ1 | 393 score changes; 278 grade changes across website–release-pair comparisons | `audit/scripts/observatory_replay/analyze_revisions.py` | Restricted original data required |
| version / RQ3 | 294 score changes and 251 grade changes retain the reported algorithm version | `audit/scripts/observatory_replay/build_reference_pack.py` | Restricted original data required |
| validation / RQ1 | V1 exact 16,264/16,264; V2 exact 169/195, below 90%; V3 fails as worded | `audit/scripts/observatory_replay/summarize_gates.py` | Restricted original data required |
| attribution / RQ2 | Zero unexplained outcome changes under the inspected source/dependency-closure analysis | `audit/scripts/observatory_replay/attribution.py` | Restricted original data required |
| exposure / RQ2 | 1.3.8–1.4.0: recorded E=0; corrected exposure 41 | `audit/scripts/observatory_replay/analyze_revisions.py` | Restricted original data required |
| plans / RQ3 | 125 distinct websites with failing B plans; 132 with failing A plans across 13 full-corpus pairs | `audit/scripts/observatory_replay/plan_validity.py` | Restricted original data required |
| parser / RQ2 / RQ3 | 1.5.2–1.5.3: 128 score changes, 99 grade changes; every B plan fails for 83 websites, 18 unchanged original scores | `audit/scripts/observatory_replay/plan_validity.py` | Restricted original data required |
| repair / RQ3 | Parser pair: 80 B targets unreachable in nine-action model; three restore with one additional action | `audit/scripts/observatory_replay/plan_validity.py` | Restricted original data required |
| margins / RQ3 | Displayed margin differs from uncurved margin because of the 90-point bonus threshold | `audit/scripts/observatory_replay/plan_validity.py` | Restricted original data required |
| population / RQ1 | Weighted grade shares, mean scores and outcome prevalence; paired bootstrap change intervals | `audit/scripts/observatory_replay/aggregate_drift.py` | Restricted original data required |
| audit / RQ3 | Positive control and candidate main-093035e3 with dependency contrasts | `audit/scripts/observatory_replay/audit_release.py` | Restricted original data required |
| dependencies / RQ2 | Exploratory as-deployed dependency analysis and jsdom parsing probe | `audit/scripts/observatory_replay/jsdom_parse_check.py` | Restricted original data required |
| sensitivity / RQ3 | Alternative CSP action sensitivity; nine-action restrictions | `audit/scripts/observatory_replay/plan_validity_sensitivity.py` | Restricted original data required |
| plan-age / RQ3 | Nonconsecutive plan age analysis is subsequently prespecified, distinct from adjacent pairs | `audit/scripts/observatory_replay/plan_validity.py` | Restricted original data required |
| grade-distribution / RQ1 | Complete grade distribution derived from stored score matrix, preserving original frame weights; no new intervals | `reproducibility_artifact/scripts/prepare.py` | Restricted original data required |
| synthetic-replay / RQ2 / RQ3 | Real scorer fixed-input differences and failing tied B plans on public synthetic responses, including unchanged displayed original scores | `reproducibility_artifact/examples/run.mjs` | Reproducible using public fixtures |
| aggregate-verification / RQ1 / RQ3 | Standalone released aggregate count, partition, unit and privacy validation | `reproducibility_artifact/scripts/validate.py` | Included and downloadable |
| paper-figures / RQ1 / RQ3 | Numerical regeneration of the current cascade and tied-plan failure figures from included aggregates | `reproducibility_artifact/scripts/figures_public.py` | Included and downloadable |

## Included evidence

[Aggregate research dataset](../reproducibility_artifact/data/research.json), [original 26-pair CSV](../reproducibility_artifact/data/release-pair-baseline.csv) and [source-code manifest](../reproducibility_artifact/data/source-code-manifest.json) preserve source identities and hashes. The dataset contains release/dependency metadata, gates, all nine actions, per-target plan partitions, population levels, audit reports, mechanisms and analysis-status labels.

Independent verification summaries are `independent-audit.json`, `exposure-reference.json`, `margin-reference.json`, `audit-reference.json` and `scientific-verification.json` in the same data directory. The last contains A/A+ affected-set verification; website identities remain restricted. `verification.json` supplies exported count/grade-distribution checks. `input-hashes.json` identifies original input files without distributing them.

Copied producing code is in `reproducibility_artifact/source/observatory_replay/`; `source-code-manifest.json` maps each original path and SHA-256 to its included copy. `prepare.py` retains aggregate-export calculations but needs the restricted study workspace; it is not a public-data regeneration command. Recorded script hashes identify original study producers. Current consumer/exporter files have packaging-only refinements and their current hashes are in the publication manifest. Public arithmetic is provided separately by `reference_aggregates.py`, using the original CSV and saved independent summaries.

## Research correspondence

§4.2 describes collection/replay; §5.1 and Table 1 describe validation; §5.2 and Table 2 cover assessments and population; §5.3 covers mechanisms/exposure; §5.4 and Figure 3 cover plans; §5.5 and Table 3 cover audits/disclosure. Figure 2 is the weighted cascade; Figure 1 is the methodological pipeline. These references locate reported results without distributing a manuscript.

A source hash and passing checks do not establish unrestricted empirical reproducibility. [REPRODUCIBILITY](REPRODUCIBILITY.md) separates public arithmetic, real-scorer synthetic replay and restricted complete replay. [METHODS_AND_LIMITATIONS](METHODS_AND_LIMITATIONS.md) retains failed gates, missing denominators and exploratory status.
