# Methodology

This document describes how the `ranfst` package generates synthetic Radio Access Network telemetry. It covers the standards vocabulary, the two‑phase generation architecture, the diurnal envelope, per‑cell heterogeneity, the event‑injection mechanism, granularity choices, reproducibility guarantees, and versioning rules.

This generator is dataset‑production-only. Anything to do with evaluating forecasting or anomaly‑detection models against the data is out of scope for this repository.

## Standardised vocabulary

| Term | Source |
|---|---|
| KPI | TS 28.554 — end‑to‑end Key Performance Indicators |
| PM (Performance Measurement) | TS 28.552 — performance measurement counters |
| MDA / MDAS | TS 28.104 — Management Data Analytics Service |
| AI/ML management | TR 28.908 — study on AI/ML management |
| ENI use case | ETSI GS ENI 001 v3.2.1 |
| O‑RAN use case | ETSI TS 104 036 (WG1 Use Cases Detailed Spec R003 v12) |
| Non‑RT RIC / Near‑RT RIC | O‑RAN Alliance |
| `RRU.PrbTotDl`, `MM.HoExeInterReq`, etc. | TS 28.552 counter IDs (verbatim) |

The scenarios in this generator are anchored against 3GPP TS 28.104 §7.2.8, which defines a normative Management Data Analytics service: *prediction and statistics of management data over a future period, on a sliding‑window basis*. Each of the eight non‑control scenarios (A–H) targets a distinct §7.2.x analytics capability, and each scenario's KPI set, event taxonomy, and trigger conditions are taken verbatim from the cited paragraphs of TS 28.104, TR 28.908, ETSI GS ENI 001, and O‑RAN.WG1 TS 104 036.

## Two‑phase generation architecture

Each scenario constructs its dataset in two phases.

**Baseline phase.** Produces unperturbed per‑(cell, KPI) time series with realistic diurnal + weekly seasonality, per‑cell heterogeneity, and KPI‑specific clipping and integer rounding. The output is the regime hand‑coded seasonal lookups were effectively designed for: pure seasonal forecasting territory, no regime changes, no drift.

**Event‑injection phase.** Scenario‑specific helpers mutate KPI series over labelled time intervals and write a parallel `*.events.parquet` ground‑truth sidecar. Each event row records `event_type`, `start_step`, `end_step`, scenario‑specific metadata columns (e.g. `redistribution_fraction`, `affected_neighbours` for Scenario A), and the start/end timestamps. Scenario S has an empty events sidecar — it is the unperturbed control.

## Diurnal envelope

A single shared envelope multiplies every load‑class KPI to give every cell the same operational rhythm. Constructed from a daily sine‑wave superposition (peak ~09:00, secondary ~20:00, trough ~04:00) plus a 35% weekend dip:

```
diurnal = 0.6
        + 0.30 × sin(2π · (hours − 9) / 24)
        + 0.15 × sin(2π · (hours − 20) / 24)
weekday_factor = 1.0 weekdays, 0.65 Sat/Sun
envelope = diurnal × weekday_factor
```

KPIs whose physical meaning is not load‑driven (e.g. RSRP, temperature) declare `envelope_influence < 1` so the diurnal pattern does not propagate into signal‑quality measurements that would not move with the load cycle in reality.

## Per‑cell heterogeneity

Each cell receives a single random scale factor drawn from a clipped Gaussian:

```
scale = clip(1 + N(0, 0.15), 0.6, 1.6)
```

This produces a realistic spread of per‑cell base loads — dense urban macros in the upper tail, suburban small cells in the lower tail — without explicitly modelling cell types.

## KPI configuration

Each KPI is described by a small immutable `KpiConfig` record containing:

- `name` — the KPI identifier, used verbatim from 3GPP TS 28.552 §5.1.1 (e.g. `RRU.PrbTotDl`, `MM.HoExeInterReq`, `PEE.AvgPower`)
- `unit` — the unit defined in the spec
- `base` — per‑cell mean at unit envelope, anchored to operator‑plausible values from public deployment reports
- `noise_pct` — noise scale as a percentage of the base value (relative or absolute by KPI)
- `envelope_influence` ∈ \[0, 1\] — how strongly the diurnal envelope modulates this KPI
- `clip_min` / `clip_max` / `integer` — domain constraints from the spec

A reviewer disputing the synthetic data's plausibility for a given KPI can find the entire configuration in one record next to the cited 3GPP paragraph that motivates it. See [`kpi-catalogue.md`](kpi-catalogue.md) for the full per‑KPI listing.

## Granularity

Every scenario emits at one of two granularities:

- **Slow loop:** 5‑minute granularity for KPIs aggregated over a granularity period. Selected windows can be re‑aggregated to 15‑minute or 1‑hour bins downstream.
- **Fast loop:** 1‑second granularity for per‑observation telemetry. Reserved for scenarios where sub‑minute dynamics are operationally meaningful (e.g. Scenario H handover‑target saturation, Scenario G signalling storms).

The `granularity` argument to the CLI selects one of `slow`, `fast`, or `both`. Scenario S currently emits at slow only.

## Reproducibility lock

Every dataset ships with a `*.manifest.json` capturing:

```json
{
  "scenario_id": "A",
  "scenario_name": "Energy-saving cell sleep transition",
  "seed": 42,
  "ranfst_version": "0.0.5",
  "n_cells": 50,
  "duration_days": 35.0,
  "granularity": "slow",
  "generated_at": "2026-05-12T10:30:00+00:00",
  "n_rows": 504000,
  "n_events": 612,
  "kpis_emitted": [
    "RRU.PrbTotDl", "RRU.PrbTotUl", "RRC.ConnMean", "RRC.ConnMax",
    "DRB.UEThpDl", "DRB.UEThpUl", "MM.HoExeInterReq", "MM.HoExeInterSucc",
    "PEE.AvgPower"
  ],
  "n_steps": 10080,
  "granularity_minutes": 5
}
```

Each scenario instance holds a single `numpy.random.Generator` derived from the integer seed; all randomness used during generation flows from that generator. Output is byte‑identical for a given `(scenario, seed, ranfst version)` triple on any host.

## Versioning

The package follows [SemVer](https://semver.org). Breaking changes to the generator (any change that alters byte‑level output for a given seed) increment the major version. Backward‑compatible additions (new scenarios, new KPIs without altering existing ones) increment the minor version. Bug fixes that don't alter output increment the patch version.

Every dataset manifest is bound to a generator version. Regenerating a manifest against a newer version requires explicit re‑acknowledgement; the runner refuses silent version drift.

## Scope and exclusions

In scope:

- Streaming and batch telemetry on RAN measurement points defined by TS 28.552 / TS 28.554.
- Per‑cell, per‑slice, per‑beam, per‑NF observation scopes.
- Labelled regime‑change events on the time axis (sleep transitions, coverage onset, MLB redistribution, handover bursts, slice mix shifts, failure precursors, signalling storms, saturation events).

Out of scope (for v0.x):

- UE‑level positioning telemetry (covered in O‑RAN UC 13 but tangential to the §7.2.8 framing).
- Security / DDoS mitigation telemetry (Scenario G addresses signalling‑storm detection, not mitigation).
- Sub‑frame‑level scheduler telemetry (xApp control‑loop granularity, faster than the 1‑second fast loop).
