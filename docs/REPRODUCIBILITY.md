# Reproducibility

Scientific checks, historical scorer replay and figure generation work in both this repository and the extracted scientific archive. Frontend/hosting commands apply to the repository. Run from the release root with Python 3.11, Node 24.21.0 and Make. Python-only aggregate checks need the standard library; optional npm/PyPI installation needs registry access.

## 1. Verify public aggregates

```sh
make -C reproducibility_artifact reproduce
```

This checks all 26 pairs, original per-pair CSV counts, independent frame-weighted arithmetic, plan partitions/unions, saved verification summaries and content hashes. It does not rerun empirical scorers, recover website identities from aggregates or reconstruct complete empirical bootstrap intervals. `data/independent-audit.json`, `exposure-reference.json`, `margin-reference.json` and `audit-reference.json` retain earlier independent saved-vector checks and their scope.

`SCIENTIFIC_MANIFEST.json` pins scientific datasets, reference source, fixtures, scorer locks and figure bytes. `PUBLICATION_MANIFEST.json` and the default-deny allowlist verify the complete release, while the download manifest checks every public resource. Optional installs and generated outputs are excluded from distributed content.

## 2. Execute historical scorers on synthetic inputs

```sh
make -C reproducibility_artifact install-scorers replay
```

Four locked genuine packages are installed: 1.4.9, 1.5.0, 1.5.2 and 1.5.3. Scoring uses the unchanged worker and stored-input stub; HTTP, HTTPS, fetch, socket, TLS and DNS requests are trapped. Synthetic empty HSTS/TLD references are deliberate demonstration inputs and are not the empirical reference lists.

Three fixtures assert complete expected outputs:

| Fixture | Original old → new | Plan enumeration |
|---|---|---|
| Rule modifier, 1.4.9 → 1.5.0 | 120/A+ → 125/A+, unchanged test outcomes | One fixed input under each release |
| Parser, 1.5.2 → 1.5.3 | 65/B− → 20/F; SRI modifier −5 → −50 | All 512 nine-action subsets under each release; both tied one-action B plans fail |
| Unchanged original scores | Displayed 0/0, uncurved −35/−80 | All 512 subsets; sole old three-action B plan 70/B → 25/D−; maximum newer score 30 |

Inputs use `.invalid` hosts, synthetic HTML and safe cookie records. See `examples/README.md`, `examples/NOTICE.md`, `expected.json` and `flooring-expected.json`. Normal replay never overwrites expected outputs. Installations can be kept externally:

```sh
node reproducibility_artifact/examples/install.mjs /tmp/observatory-example-env
node reproducibility_artifact/examples/run.mjs /tmp/observatory-example-env
```

These examples demonstrate executed scorer behavior, not observed interventions or reproduction of empirical website counts.

## 3. Regenerate figures and the existing platform (repository)

```sh
make -C reproducibility_artifact PYTHON=python3.11 figure-env figures
npm --prefix research_companion ci
npm --prefix research_companion run typecheck
npm --prefix research_companion test
make build-site
python3 tools/verify_publication.py
python3 tools/serve_prefix.py
```

Figure outputs go to `reproducibility_artifact/generated/figures/`; [FIGURES](FIGURES.md) explains all 61 plotted values. Frontend builds produce a disposable `dist/`; `tools/build_site.py` synchronizes generated public assets from canonical `docs/` and `reproducibility_artifact/`, then prepares `site/` and the relative root bridge. There is no backend, analytics, remote font or visitor-code execution.

The server’s `/REPOSITORY/` route exercises Pages-prefix paths. `/sandbox-review/` simulates an opaque-origin hosting sandbox locally, including guarded preferences and classic-script data delivery. Filtered data can be copied when that sandbox blocks browser downloads. These local routes do not certify the actual anonymous service.

## 4. Complete empirical replay requires restricted inputs

Copied research files in `source/observatory_replay/` retain their original bytes and flat imports. Data/source manifests identify the original outputs and producing code. Full replay needs the restricted response corpus, frame/sample identities, original 27 scorer installations, all relevant action vectors, and common historical HSTS/TLD/certificate references. `data/environment.json` supplies installation/reference metadata and hashes, not all reference contents. The original empirical Python environment is not fully frozen here.

Run only against a new isolated corpus copy. From `reproducibility_artifact/`, a retrospective positive-control audit can consume already stored replay/action vectors:

```sh
export OBS_CORPUS_COPY=/path/to/isolated/restricted/corpus
mkdir -p "$OBS_CORPUS_COPY/analysis"
python3.11 source/observatory_replay/audit_release.py --in "$OBS_CORPUS_COPY" --baseline 1.6.3 --candidate 1.7.0 --candidate-replay replay --candidate-plans remediation_full
```

The stored candidate `main-093035e3` needs completed candidate replay and candidate 512-subset vectors before comparison with 1.7.1. This historical candidate identifier is unrelated to the publication repository’s `master` branch. Review `run_replay.py`, set `OBS_PKG_DIR` for historical installations, and pin dependencies/reference inputs before running a fresh experiment. No restricted empirical replay is claimed from the public archive alone.
