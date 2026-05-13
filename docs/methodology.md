# Methodology

## Framing — DriftMind as an MDA service implementation

3GPP TS 28.104 v18.3.0 §7.2.8 defines a normative Management Data Analytics (MDA) capability:

> *Prediction and statistics of Management data — MDAS supports producing predictions and statistics on any 3GPP‑defined performance measurement (TS 28.552) or Key Performance Indicator (TS 28.554), over a future period, on a sliding‑window basis.*

This is, almost word‑for‑word, the operational specification of a streaming online forecaster. The benchmark in this repository evaluates how well candidate engines fulfil that normative service on operationally relevant scenarios. The headline question is not which algorithm is "best" in the abstract, but which engines deliver the §7.2.8 service well enough to deploy at the RAN edge.

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

## Evaluation surface

A run consists of:

1. The generator emits a synthetic dataset for a given (scenario, seed, version) triple.
2. Each forecaster in `baselines/` is instantiated, given the same warmup window, and evaluated against the same test windows of the dataset.
3. Metrics are computed by the model‑agnostic runner in `evaluation/`.
4. Results land in `results/<run-name>/` with the (scenario, seed, version, model, hyperparameters, metric) tuple.

No forecaster sees data labels; the same warmup is given to every model; the same prediction targets are scored on the same actuals. Hyperparameter handling follows the asymmetric convention described under "Default‑vs‑tuned" below — DriftMind runs at default configuration; classical baselines run at the best per‑scenario configuration when the sweep harness is available.

## Forecaster protocol

Every model in `baselines/` implements the `Forecaster` protocol defined in [`evaluation/protocol.py`](../evaluation/protocol.py). The protocol intentionally accommodates both streaming and batch regimes:

- **Streaming online forecasters** implement `fit_one(observation)` (or equivalent per‑observation update) and `predict(horizon) -> np.ndarray`.
- **Batch forecasters** implement `fit(window)` and `forecast(horizon) -> np.ndarray`. They retrain on a rolling window with a configurable cadence (default: weekly).
- **Pretrained forecasters** implement `predict(context, horizon) -> np.ndarray` with no training step.

The runner adapts to whichever methods a forecaster implements. Hyperparameter handling is *asymmetric* — see "Default‑vs‑tuned" below.

## Prediction target

Every forecaster is scored on the **h‑step‑ahead point**, i.e. `fc[-1]` against `series[i + horizon]`, where `i` is the index of the last observation the model was given before predicting. Cursor advances by 1 (online) or by the model's natural prediction cadence (batch, where it advances by `horizon`).

This avoids the family‑mixing problem in which batch models' MAE includes "easy" 1‑step predictions while online models are scored only on "hard" h‑step predictions. **One target. One metric. Same operation, every model.**

## Metrics

| Dimension | Metric | Definition |
|---|---|---|
| Stationary accuracy | `MAE_norm` | `MAE_raw / norm_std`, where `norm_std` is the full‑series standard deviation. Reported median across series at h ∈ {1, 6, 12, 24}. |
| Recovery time | `t_recover` | Number of steps after a labelled regime‑change event until rolling MAE returns to within 1.2× the pre‑event rolling MAE. |
| Anomaly detection | `(detection_rate, fpr)` | Detection rate and false‑positive rate at a fixed alarm threshold. ROC pair reported per scenario. |
| Detection lead time | `t_lead` | Time between the model's anomaly score first crossing threshold and the operator‑defined event time. Per‑event‑type histogram. |
| Streaming throughput | `rate_pts_s` | Steady‑state points/second in a single‑process invocation against the concatenated dataset for the scenario. |
| Per‑event compute | `cpu_s_per_event` | CPU‑seconds spent during the labelled regime‑change windows. |

Metrics that a model cannot produce (e.g. a seasonal lookup with no anomaly score) are reported as `N/A`. **The absence of a capability is itself a result and is shown in the headline matrix.**

## Reproducibility lock

Every result file in `results/` ships with a sidecar `manifest.json` capturing:

```json
{
  "scenario": "A",
  "seed": 42,
  "generator_version": "0.1.0",
  "model": "driftmind",
  "model_version": "2.2.0",
  "hyperparameters": {"fitRate": 1, "inputSize": 168, ...},
  "host": "linux-x86_64-cpu",
  "started_at": "2026-05-15T10:32:11Z",
  "completed_at": "2026-05-15T10:38:47Z",
  "metric_summary": {...}
}
```

The official v2 joint run is performed against a frozen generator version + seed range, locked in writing with all participating parties before the run.

## Default‑vs‑tuned

The benchmark adopts an **asymmetric measurement convention** that reflects the deployment trade‑off operators actually face.

A benchmark that gives every forecaster a uniform per‑scenario hyperparameter sweep budget answers the question *"which algorithm has the lowest error under optimal tuning?"* That is a research question. RAN‑FST asks a different question: *"which engine delivers the §7.2.8 service well enough to deploy at the RAN edge, given how each engine actually behaves when dropped in?"*

In production deployment, the classical baselines all require per‑dataset hyperparameter selection. SlotEWMA needs the right `n_slots` (288 for daily, 2016 for weekly, 144 for half‑day — wrong choice on the v0.0.3 stress dataset puts SlotEWMA below the mean baseline). ARIMA / SARIMA needs `(p, d, q)` and `(P, D, Q, m)` plus a retrain cadence; misconfiguration produces unbounded error. Prophet needs `changepoint_prior_scale`, seasonality flags, and a holidays calendar. FastNPTS needs `seasonality`, `n_samples`, and a recency‑decay rate. None of these are dataset‑independent.

DriftMind is positioned to work at default configuration — the product's *"data‑scientist‑free"* deployment promise. Measuring DriftMind under hyperparameter sweeps would measure something the product does not deliver in practice.

The convention is therefore:

- **DriftMind runs at default configuration.** The configuration values are whatever the production engine ships with as its `forecasterCreation` defaults — exactly what an operator gets when they pull the published Docker image and accept the canned settings.
- **Classical baselines run at the best per‑scenario configuration** when the per‑baseline sweep harness is available. The harness enumerates each baseline's `baselines/<name>/sweep.yaml` grid on the calibration split, identifies the best configuration on each scenario, and reports that configuration's metric in the headline. Every other configuration's result is retained (in `results/.../sweep/`) so the choice cannot be cherry‑picked after the fact.

This is asymmetric *in DriftMind's disfavour*. DriftMind has to beat baselines that have been given a per‑scenario tuning advantage. If DriftMind wins under that asymmetry, the deployment story is real. If DriftMind loses, the result tells operators that the alternative engine requires a data scientist on staff to extract its full value, which is itself useful information. The asymmetric convention is the harder test for DriftMind, not the easier one.

The framing supersedes an earlier framing that motivated uniform sweep parity by reference to a v1 Ericsson finding ("DriftMind ran with engine defaults while baselines were hand‑tuned"). On reflection, **DriftMind running with engine defaults is the correct methodology**, not the unfair one — it is what the engine actually delivers in deployment. Aligning the benchmark with deployment reality requires the asymmetric convention, not uniform sweep.

**Status in v0.0.3 preview.** Neither side has been swept; every baseline runs at default. This is a preview‑grade simplification that under‑represents what the classical baselines can deliver under proper per‑scenario tuning. The asymmetric convention takes full effect at v0.0.4 / v0.1.0 when the per‑baseline sweep harness lands.

## Granularity

Every scenario emits at two granularities:

- **Slow loop** (Non‑RT RIC consumption): 5‑minute granularity for KPIs aggregated over a granularity period. Selected windows aggregate to 15‑minute and 1‑hour for evaluation at coarser horizons.
- **Fast loop** (Near‑RT RIC consumption): 1‑second granularity for per‑observation telemetry feeding fast‑loop control decisions.

A model implementation declares which granularity it consumes; the runner provides the appropriate stream.

## Scope and exclusions

In scope:
- Streaming, batch, and pretrained forecasters operating on RAN telemetry as defined by TS 28.552 / TS 28.554.
- Anomaly detection from KPI degradation trends and abrupt regime changes.
- Per‑cell, per‑slice, per‑beam, per‑NF observation scopes.

Out of scope (for v0.x):
- UE‑level positioning algorithms (covered in O‑RAN UC 13 but tangential to the §7.2.8 framing).
- Pure security / DDoS mitigation logic (Scenario G addresses signalling‑storm *detection*, not mitigation).
- Sub‑frame‑level scheduler logic (this is xApp control loop territory, faster than even our 1‑second granularity).

## Versioning

The benchmark is versioned per [SemVer](https://semver.org). Breaking changes to the generator (any change that alters byte‑level output for a given seed) increment the major version. Backward‑compatible additions (new scenarios, new KPIs without altering existing ones) increment the minor version. Bug fixes that don't alter output increment the patch version.

Every result is bound to a generator version. Re‑running a result against a newer version requires explicit re‑acknowledgement; the runner refuses silent version drift.

## Citation

See [citations.md](citations.md) for the full primary‑source manifest.
