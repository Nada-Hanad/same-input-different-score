# Figures

The included figure binaries and all 61 plotted numerical values are retained unchanged. The paper title and section/figure correspondence are useful research references; the manuscript itself is not distributed.

| Correspondence | Content | Public artifact |
|---|---|---|
| Figure 1 | Methodological MDN HTTP Observatory scoring pipeline | Explained in METHODS_AND_LIMITATIONS; no manuscript extraction or bundled diagram |
| Figure 2 | Weighted exposure, test, score and grade change rates | `fig_cascade.pdf` / `.png` |
| Figure 3 | Websites with failing minimum-action plans | `fig_remediation_plan_failures.pdf` / `.png` |
| Supplementary | 1.7.1 uncurved A-plan margins | `fig_margin_companion.pdf` / `.png` |

Tables 1–3 correspond to validation, relevant release comparisons and disclosure. `figure-references.json` is the machine-readable map; it contains no manuscript-version or PDF metadata.

From the release root:

```sh
make -C reproducibility_artifact PYTHON=python3.11 figure-env
make -C reproducibility_artifact figures
```

The isolated environment uses pinned Matplotlib 3.10.7, NumPy 2.4.6 and dependencies. Installation needs PyPI; plotting is offline. Outputs go to `reproducibility_artifact/generated/figures/`. Prepared figures are in `reproducibility_artifact/figures/`; the static host receives generated copies. PDFs use anonymous author metadata and omit creation/modification dates.

`figure-values.json` records each point/bar and its original interval. Cascade uses the recorded corrected exposure diagnostic for 1.3.8–1.4.0, 0.0701% [0.0113,0.1488]; the registered E=0 remains separately preserved. Exact zeros use a labeled plotting floor without changing the values or interval endpoints. Plan bars distinguish every-plan and some-tied-plan failures within each pair and are not distinct-website unions. Nine other full-corpus pairs and thirteen sampled controls have no observed failure under their respective coverage.

`figures_public.py` reconstructs numerical figure geometry from included aggregates; it does not extract images from a manuscript or invent uncertainty. Its two numerical paper figures and one supplementary plot are checked against the original values. Original research plot sources are retained in `source/observatory_replay/`; other reference-pack plots require restricted inputs. [EVIDENCE_MAP](EVIDENCE_MAP.md) identifies producing code and data.
