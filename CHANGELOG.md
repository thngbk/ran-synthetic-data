# Changelog

All notable changes to this project will be documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/). Any change
that alters byte-level output for a given seed increments the minor or major
version; the runner refuses silent version drift.

## [0.0.5] - 2026-05-13

### Repository

- **Extracted from `ran-forecasting-stress-test` as a standalone package.** The
  generator (`ranfst.scenarios`, `ranfst.kpis`, `ranfst.events`) now lives in
  its own repository with its own CITATION, NOTICE, and minimal dependency
  surface (numpy, pandas, pyarrow, scipy, click, pyyaml). Model baselines and
  the evaluation harness remain in the original repository, repackaged as
  `ranfst_bench`, and depend on `ranfst` rather than vendoring it.
- CLI trimmed to generator-only commands: `list-scenarios`, `describe`,
  `generate`. The evaluation subcommands move to `ranfst-bench`.

### Datasets

- All nine scenarios (S, A–H) reproduce byte-identically from a
  `(scenario, seed, ranfst version)` triple at 5-min granularity.
- Companion 35-day benchmark dataset under `results/v0.0.5-35d-run/` in the
  benchmark repository is the canonical reproducible artefact at this version.
