# Methods and limitations

## Observation process and comparison units

The study collected 20,613 actual websites; 20,616 attempted records include three panel comment lines. Of these, 16,264 websites were scored across 27 published releases, 1.3.2 through 1.7.1. Unpublished changelog-only releases 1.3.4 and 1.3.9 are excluded. Stored response evidence is held fixed while test/scoring code and installed dependencies vary. This is retrospective fixed-input assessment reconstruction, not prospective forecasting, a new live scan or a measured change in website security.

There are 422,864 website–release-pair comparisons across 26 consecutive pairs. E counts websites matching a stored exposure condition; T counts websites with any changed test outcome; S and G count score and grade changes. Per-test counts overlap and must not be summed as distinct websites. The 393 score/278 grade changes are comparison counts; earlier saved-vector verification identifies 299 distinct changed websites (206 once, 92 twice and one three times).

Exposure and source/dependency closure support mechanism interpretation, not uniquely isolated causality. For 1.3.8–1.4.0, the registered E=0 misses 32 changed-test websites. The post-analysis parser-faithful correction identifies 41 and contains all 32; its recorded weighted diagnostic is 0.0701% [0.0113, 0.1488]. Original E=0 remains in the baseline CSV and datasets. For 1.4.9–1.5.0, the stored exposure is a pre-replay correction rather than the original registered predicate.

## Implementation classifications

| Code in raw data | Interface label | Interpretation |
|---|---|---|
| `null` | No scoring-relevant change | No relevant source or installed-dependency change identified in the evaluated configuration; this is not missing data |
| `refactor` | Behavior-preserving refactor | Code change expected to preserve assessment behavior; an expectation distinct from observed outcomes |
| `defensive` | Input handling change | Guards or input handling changed; parsing/dependency changes may also be present |
| `scoring` | Scoring-relevant change | Source/dependencies could change tests, modifiers or grades |

The recorded classes are 14/4/2/6 respectively. No observed change is not the same as no implementation change: the 1.3.3–1.3.5 input guard has an observed zero, while 1.4.9–1.5.0 changes scores without changing test outcomes. Installed main-series dependencies and exploratory as-deployed configurations are distinct. Missing measurements remain “Not recorded” or “Not available”; numeric zeros and recorded zero intervals remain observations under the stated coverage, not universal no-effect guarantees.

## Nine-action plan model

The actions modify CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, CORP, COOP, COEP and cookie flags. Exact values and scoring transformations are in `examples/action-definitions.json` and copied `remediate.mjs`. All 512 subsets are enumerated at thresholds B=70, A=90 and A+=100. Eligibility requires the original score below target and at least one old sufficient subset; every tied minimum-size old subset is retained.

`none_fail` means every old minimum plan remains sufficient; `some_fail` means mixed validity; `every_fails` means every old minimum plan fails. Family identity, family change and failure are separate events. Restoration by extending an old plan differs from finding any new sufficient subset; unreachable sentinels are not action counts.

Thirteen pairs have full-corpus plan vectors; thirteen control comparisons use a 2,205-website sample. Target-specific eligible/restoration denominators are absent for sampled controls and must not be invented. The 125 B and 132 A/A+ union counts are distinct websites across full-corpus pairs, not sums of pair counts. A/A+ affected sets are equal in those evaluated pairs and union, not universally equivalent targets or plan families.

For 1.5.2–1.5.3, 83 websites have every tied old B plan fail, 80 have no new subset reaching B and three are restorable. Eighteen have unchanged displayed original scores 0/0: twelve older uncurved scores are negative, six are exactly zero, and all newer uncurved scores are negative. Score flooring can therefore hide differences relevant to plans. The plan model optimizes score sufficiency, omits operational safety and body/redirect repairs, and does not demonstrate successful deployment, effectiveness, harm or causal security improvement.

## Population analysis and uncertainty

Frame-weighted estimates exclude the legacy panel; the Tranco population denominator is 15,709 scored sites. Weighting assumes scored sites represent their rank stratum and does not resolve arbitrary nonresponse. Recorded SRI prevalence changes from 18.39% to 19.19%, +0.80 percentage points [0.56,1.06]; endpoint F share changes +0.34 points and mean score −0.12. These are assessment measurements under fixed inputs.

The artifact retains 2,224 verified population levels, recorded paired 2,000-draw intervals and complete grade distributions derived from saved scores. Earlier restricted-input checks independently reconstructed three paired intervals using seed 20260927. Public aggregate arithmetic does not freshly reproduce their empirical bootstrap. Most arbitrary nonconsecutive paired-change intervals and many outcome-level intervals are absent. No interval is invented for a missing value. Zero bootstrap bounds describe the sample and resampling procedure, not a population guarantee.

## Validation and provenance boundaries

- V1 storage fidelity is recorded as 16,264/16,264 exact; the public archive does not recollect or reserialize every original input.
- V2 live-service exact-score agreement is 169/195 (86.7%), below the prespecified 90%; grade agreement is 171/195. Absolute agreement with the deployed service is not established.
- V3 fails its original compatibility wording, although all inputs scored at collection pass. The 1.5.0 memo rerun completes 95/100, with five process failures; completed vectors match.
- Source closure is not a complete isolated intervention. Controlled parser fixtures establish executed behavior for their inputs, not unique attribution of every empirical transition.
- Candidate and retrospective positive-control audits read precomputed evidence; they are not prospective field validation. The platform never runs visitor-provided code.
- Disclosure “none found” applies to the reviewed sources and dates, not universal absence or a continuing service guarantee.

## Analysis status

The September plan precedes the main replay and specifies a four-action prefix. The later 8 October plan specification defines tied families over all 512 nine-action subsets; nonconsecutive plan-age work is subsequently prespecified. D18/D19 narrow thirteen plan controls to the sampled cohort. Historical dependency reconstruction, D20 disclosure/population/parser diagnostics/alternative-CSP follow-ups and margin analyses are exploratory. These distinctions are retained in structured evidence and are not promoted to preregistered status by this artifact.

Original protocol hashes are: September plan `699b3ab5eed8b7aa3578dc08a23be5d1bfdd46d5a93c2e91490022331cf741b2`; October plan specification `e4e67624c53fa473d23e07d5af876f2a185f9a2d1b14d38136d1bd3b789fab36`; deviation record `9413513f7be91aaa7a592df194505805cee42b7b3d2764c66672f9fbcf2b9333`. Local hashes identify retained records but do not certify independently trusted preregistration timestamps. Unredacted protocols contain identifiers and remain restricted.

Public verification checks derived aggregates and controlled synthetic examples. Complete empirical replay and website-set identity reconstruction require restricted evidence and historical environments. [REPRODUCIBILITY](REPRODUCIBILITY.md) describes those three levels; [EVIDENCE_MAP](EVIDENCE_MAP.md) traces individual results.
