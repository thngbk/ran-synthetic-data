# Scenario S — Stationary periodic baseline (control)

> **RAN relevance:** Floor. This is the regime hand‑coded seasonal lookups were effectively designed for. Included as a credibility floor: a forecaster that cannot match seasonal lookups on stationary periodic data is not deployment‑grade.

## Source citations

- 3GPP TS 28.554 §6.4 (Utilization KPI), §6.3 (Integrity KPI) — evaluation metrics
- 3GPP TS 28.552 §5.1.1.2 (PRB usage), §5.1.1.4 (RRC connections) — input series
- ETSI GS ENI 001 §5.3.2 — generic radio coverage and capacity context

## Operational description

Stationary weekday/weekend cells with strong daily and weekly seasonality. No regime changes, no events, no drift. Pure seasonal forecasting territory.

## Trigger conditions

None. This is the unperturbed baseline.

## Input KPIs

- `RRU.PrbTotDl`, `RRU.PrbTotUl` (TS 28.552 §5.1.1.2.1–.2)
- `RRC.ConnMean`, `RRC.ConnMax` (TS 28.552 §5.1.1.4.1–.2)
- `DRB.UEThpDl.SNSSAI`, `DRB.UEThpUl.SNSSAI` (TS 28.552 §5.1.1.3.1, .3.3)
- `MM.HoExeInterReq`, `MM.HoExeInterSucc` (TS 28.552 §5.1.1.6.1.7–.8)
- `PEE.AvgPower` (TS 28.552 §5.1.1.19.2.1)

## Synthetic generation

~50 cells, 4 weeks each. Slow‑loop counters at 5‑min granularity; fast‑loop at 1 s. Daily seasonality (24 h period with rush‑hour peaks), weekly seasonality (weekday/weekend distinction). Gaussian noise floor at 5–10% of signal magnitude. **No regime changes.**

## Ground‑truth labels

None — every observation is "nominal".

## Headline metric

Median `MAE_norm` at horizon h ∈ {1, 6, 12, 24} steps, scored on the h‑step prediction (`fc[-1]`) consistent across model families.

## Expected outcome by model family

- **Hand‑coded seasonal baselines** (SlotEWMA, SARIMA with `m=24`): expected to **win or tie** on this scenario by construction.
- **Streaming online forecasters** (DriftMind, FastNPTS, SNARIMAX, PSR): expected to be **competitive**, within 10–20% of seasonal baselines.
- **Batch retrainers** (Prophet, LightGBM, Seasonal Naive): expected to be **competitive** at horizons ≥ 6, less so at h = 1.
- **Pretrained zero‑shot** (Chronos): variable — depends on pretraining corpus alignment with hourly RAN cycles.

## Why this matters operationally

A forecaster that cannot match seasonal lookups on stationary periodic data is not deployment‑grade. Scenario S verifies the floor.
