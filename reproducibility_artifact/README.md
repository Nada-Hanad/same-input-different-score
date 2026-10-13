# Scientific artifact

Aggregate results, original research source, historical scorer examples, scientific tests and figures for **Same Input, Different Score: Auditing Release-Induced Changes in Web Security Assessments**.

From this directory, `make reproduce` checks public aggregates and release integrity. `make install-scorers replay` executes three fixtures on four locked historical scorers. `make figure-env figures` regenerates plots from included aggregates.

See [REPRODUCIBILITY](../docs/REPRODUCIBILITY.md), [METHODS_AND_LIMITATIONS](../docs/METHODS_AND_LIMITATIONS.md), [EVIDENCE_MAP](../docs/EVIDENCE_MAP.md) and [FIGURES](../docs/FIGURES.md). Full empirical replay requires restricted response/action vectors and historical reference inputs. No manuscript or empirical response fixture is distributed. Third-party notices and scorer lockfiles retain original attributions.
