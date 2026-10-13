# Same Input, Different Score

**Auditing Release-Induced Changes in Web Security Assessments**

This research artifact examines how releases of the MDN HTTP Observatory change assessments when website responses are held fixed. It separates changes in tests, scores, grades and modeled remediation plans, with source and dependency evidence for interpreting the differences.

[Explore the anonymous interactive platform](https://anonymous.4open.science/w/web-scorer-release-audit/) · [Anonymous repository](https://anonymous.4open.science/r/web-scorer-release-audit/)

The platform provides seven linked views: Overview, Release Explorer, Remediation Plans, Mechanisms, Population Effects, Release-Impact Audit and Artifact. Selections can be shared using the URL fragment.

## Main findings

- The fixed-input study compares 27 published releases on 16,264 scored websites: 26 consecutive pairs and 422,864 website–pair comparisons, with 393 score changes and 278 grade changes.
- Across the 13 full-corpus plan comparisons, 125 distinct websites have a failing old minimum-action B plan; the A and A+ affected unions each contain 132 websites. Sampled plan controls are reported separately.
- The 1.5.2–1.5.3 parser comparison has 83 websites whose every tied minimum B plan fails, including 18 with unchanged displayed original scores.
- A public synthetic fixture executes the historical scorers with original scores 0/0 and uncurved scores −35/−80. Its same old three-action B plan scores 70/B then 25/D−. This is a controlled demonstration, not an empirical frequency estimate.
- Live-service exact-score agreement was 169/195 (86.7%), below the prespecified 90% threshold. Fixed-input contrasts do not establish absolute agreement with the deployed service or actual security improvement.

## Quick start

Use Python 3.11, Node 24.21.0 and Make. From the repository root:

```sh
python3 tools/verify_publication.py
make -C reproducibility_artifact validate test
python3 tools/serve_prefix.py
```

Open `http://127.0.0.1:5175/REPOSITORY/` to explore the committed static site. For genuine historical scorer examples:

```sh
make -C reproducibility_artifact install-scorers replay
```

[REPRODUCIBILITY](docs/REPRODUCIBILITY.md) covers figure generation, source layout, frontend builds and the standalone [scientific archive](downloads/scientific-artifact.zip).

## Documentation and structure

- [Methods and limitations](docs/METHODS_AND_LIMITATIONS.md): observation process, sampling, action model, validation failures and analysis status.
- [Evidence map](docs/EVIDENCE_MAP.md): results, original source identifiers, included code and access requirements.
- [Figures](docs/FIGURES.md): plotting inputs, section/figure correspondence and regeneration commands.

`reproducibility_artifact/` contains aggregate datasets, scientific tests, copied research source, historical scorer examples and figures. `research_companion/` contains the existing React/TypeScript application; its public assets are generated from canonical artifact files and documentation. `site/` is the committed static build required for anonymous hosting. `tools/` verifies files, prepares hosting assets and packages the release.

## Reproducibility boundary

Public aggregate verification and synthetic scorer replay are independently runnable. Complete empirical replay, website-set identities and fresh population bootstraps require the restricted response corpus, website/action vectors and historical reference inputs; these are not distributed. Recorded intervals and prior restricted-input verification are retained with their scope. Synthetic inputs never substitute for empirical evidence.

No manuscript is bundled. The supplied anonymous links have not been independently tested through the live proxy for this cleaned release. Third-party notices are retained; see [licensing](LICENSE.md).
