# ranfst — RAN Synthetic Telemetry Generator

Reproducible synthetic telemetry generator for Radio Access Network (RAN) forecasting and anomaly-detection benchmarks. Emits per‑(cell, KPI) time series across **nine network scenarios** — every scenario, every KPI, and every operational pattern anchored in primary 3GPP, ETSI, and O‑RAN specifications.

Every dataset is **byte‑identical reproducible** from a `(scenario, seed, ranfst version)` triple. Anyone running the same combination produces the same bytes on any host.

---

## What this package is — and is not

`ranfst` is *only* the generator. It does not include forecasting models, evaluation harnesses, or benchmark results. Those live in a companion repository, **[ran-forecasting-stress-test](https://github.com/thngbk/ran-forecasting-stress-test)** (package `ranfst_bench`), which depends on this one. The split keeps the dataset citable on its own and the benchmark harness free to evolve independently.

---

## Scenarios

Nine scenarios spanning the operationally relevant RAN regime mix. Each is anchored in 3GPP TS 28.104 Management Data Analytics (MDA) service capabilities.

| ID | Name | Triply‑cited¹ | Primary 3GPP citation | Operational regime |
|---|---|---|---|---|
| **S** | Stationary periodic baseline (control) | — | TS 28.552 §5.1 | Diurnal + weekly seasonality, no events. |
| **A** | Energy‑saving cell sleep transition | ✓ | TS 28.104 §7.2.4.1 / §8.4.4.1 | Step‑wise neighbour‑load redistribution. |
| **B** | Coverage problem onset | ✓ | TS 28.104 §7.2.1.1 | Gradual RSRP / RSRQ degradation. |
| **C** | Mobility load balancing (MLB) regime change | ✓ | TS 28.104 §7.2.2.5; TR 28.908 §5.1.10.2.2 | Load redistribution across a neighbourhood. |
| **D** | MRO handover anomaly bursts | ✓ | TS 28.104 §7.2.5.1 | Multiplicative bursts on `MM.HoExeInterReq`. |
| **E** | Network slice SLA assurance | ✓ | TS 28.104 §7.2.2.2/3 | Per‑slice eMBB / URLLC / mMTC mix shifts. |
| **F** | Failure prediction from KPI degradation | ✓ | TS 28.104 §7.2.3.1 / §8.4.3.1 | Slow degradation preceding a failure. |
| **G** | Signalling storm / abrupt regime change | ✓ | TS 28.104 §7.2.7.2; ETSI GS ENI 001 §5.5.2 | Abrupt 5–20× spike on `RRC.ConnEstabAtt`. |
| **H** | Handover‑target resource saturation | ✓ | TS 28.104 §7.2.5.x | Saturation when source‑cell offered load > capacity. |

¹ "Triply‑cited" means the scenario's regime appears independently in (a) the 3GPP management view (TS 28.104 / TR 28.908), (b) the ETSI ENI use case catalogue (GS ENI 001), and (c) the O‑RAN WG1 implementation specification (TS 104 036).

Per‑scenario specifications with full citations, KPI sets, event schemas, and trigger conditions live under [`docs/scenarios/`](docs/scenarios/).

---

## How it works

Each scenario constructs its dataset in two phases:

- **Baseline phase** — produces unperturbed per‑(cell, KPI) time series with realistic diurnal + weekly seasonality, per‑cell heterogeneity, and KPI‑specific clipping/integer rounding.
- **Event‑injection phase** — scenario‑specific helpers mutate KPI series over labelled time intervals and write a parallel `*.events.parquet` ground‑truth sidecar (`event_type`, `start_step`, `end_step`, scenario‑specific metadata).

Output per scenario:

```
scenario_X.parquet           # per‑(cell, KPI, t) telemetry
scenario_X.events.parquet    # labelled event ground‑truth sidecar
scenario_X.manifest.json     # scenario, seed, ranfst version, n_cells, duration_days, n_steps, KPIs
```

KPI configurations use 3GPP TS 28.552 §5.1.1 names verbatim (e.g. `RRU.PrbTotDl`, `MM.HoExeInterReq`, `PEE.AvgPower`). Each KPI declares `base`, `noise_pct`, `envelope_influence`, `clip_min`/`clip_max`, and integer constraint inline next to the cited spec paragraph that motivates it.

Full methodology: [`docs/methodology.md`](docs/methodology.md). KPI catalogue: [`docs/kpi-catalogue.md`](docs/kpi-catalogue.md).

---

## Reproducibility lock

- Every dataset ships with a `*.manifest.json` capturing `(scenario, seed, ranfst version, n_cells, duration_days, n_steps, n_events, KPIs)`.
- Generator versioning follows SemVer: any change altering byte‑level output for a given seed increments the version. The runner refuses silent version drift.
- Each scenario instance holds a single `numpy.random.Generator` derived from the integer seed. All randomness used during generation flows from that generator.

---

## Quick start

```bash
pip install ranfst

# Discover what's available
ranfst list-scenarios

# Read a scenario's description (with citations)
ranfst describe --scenario A

# Generate one scenario's dataset
ranfst generate --scenario A --seed 42 --output ./data/scenario_A.parquet

# Generate every scenario at one seed
for s in S A B C D E F G H; do
    ranfst generate --scenario $s --seed 42 \
        --output ./data/scenario_$s.parquet \
        --n-cells 12 --duration-days 35
done
```

From source:

```bash
git clone https://github.com/thngbk/ran-synthetic-data.git
cd ran-synthetic-data
pip install -e ".[dev]"
pytest
```

---

## Companion benchmark

The benchmark harness — forecasting baselines (DriftMind, Slot EWMA, Fast NPTS, Seasonal Naive, ARIMA, Triggered ARIMA, Triggered Prophet), evaluation runner, recovery / detection metrics, and result aggregation — lives at **[ran-forecasting-stress-test](https://github.com/thngbk/ran-forecasting-stress-test)** under the package name `ranfst_bench`. It depends on `ranfst` and is the source of any published model‑comparison results that reference these datasets.

---

## Citation

If you use this generator or a dataset produced from it, please cite via [`CITATION.cff`](CITATION.cff).

---

## Author

Roman Ferrando, Thingbook.

---

## Licence

Apache‑2.0 (see [LICENSE](LICENSE)).
