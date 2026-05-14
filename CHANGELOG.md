# Changelog

All notable changes to this project will be documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/). Any change
that alters byte-level output for a given seed increments the minor or major
version; the runner refuses silent version drift.

## [0.0.5] - 2026-05-13

### Initial release

- Standalone synthetic RAN telemetry generator with minimal dependency surface
  (numpy, pandas, pyarrow, scipy, click, pyyaml).
- Nine scenarios (S, A–H) anchored in primary 3GPP, ETSI, and O-RAN specifications.
  All scenarios reproduce byte-identically from a `(scenario, seed, ranfst version)`
  triple at 5-minute granularity.
- CLI: `list-scenarios`, `describe`, `generate`.
- Per-scenario specifications with full citations, KPI sets, event schemas, and
  trigger conditions under `docs/scenarios/`.
