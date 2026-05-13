# Scenario A — Energy‑saving cell sleep transition

> **RAN relevance:** High. **Triply‑cited** — appears independently in the 3GPP management view, the ETSI ENI use case catalogue, and the O‑RAN WG1 implementation specification.

## Source citations

- **3GPP TS 28.104 §7.2.4.1 / §8.4.4.1** — *Energy saving analysis*. Outputs include `trafficLoadTrends` (an explicit load forecast that drives sleep decisions), and recommendations covering ES‑Cell selection, candidate take‑over cells, time to enter/terminate, and load thresholds.
- **3GPP TR 28.908 §5.2.7.2.1** — *RAN domain ES; AI/ML inference configuration*. Verbatim: *"RAN domain ES can use AI to formulate energy saving solutions … ML entity configuration needs to be triggered to enable RAN domain ES function."*
- **ETSI GS ENI 001 §5.2.5** — *Energy saving in radio network*. Verbatim: *"The power consumption of 5G base station is about 2.5–3.5 times of 4G base stations … 5G energy saving is the most urgent problem to be solved by operators in 5G commercial deployment."*
- **O‑RAN.WG1 TS 104 036 §4.21** — *Energy Saving*. Defines EE/EC measurement reports, load statistics per cell and per carrier, and per‑carrier transmit‑power metrics as the canonical input set.

## Operational description

When a Capacity Booster (CB) cell enters energy‑saving sleep state, its traffic is absorbed by neighbour Coverage cells. The neighbour‑cell load distribution changes step‑wise within seconds; the inverse step occurs at wake‑up. **A weekly retrainer's neighbour‑load model is wrong for hours after each sleep/wake transition.**

## Trigger conditions

Verbatim from TS 28.104 §8.4.4:
- Predicted load on the ES candidate cell falls below the deactivation threshold for the configured time window.
- A neighbouring cell's load forecast indicates capacity to absorb the CB's offered traffic.
- Time‑window context (e.g. 18:00–06:00 sleep window) is satisfied.

## Input KPIs

- `RRU.PrbTotDl`, `RRU.PrbTotUl` (TS 28.552 §5.1.1.2) — load on CB and neighbour cells
- `RRC.ConnMean`, `RRC.ConnMax` (TS 28.552 §5.1.1.4) — connected users on CB and neighbours
- `DRB.UEThpDl.SNSSAI`, `DRB.UEThpUl.SNSSAI` (TS 28.552 §5.1.1.3) — per‑slice throughput
- `PEE.AvgPower`, `PEE.Energy` (TS 28.552 §5.1.1.19.2.1, §5.1.1.19.3) — base‑station power
- `CARR.MeanTxPwr`, `CARR.MaxTxPwr` (TS 28.552 §5.1.1.29.1–.2) — per‑carrier TX power
- `EEMN,DV` (TS 28.554 §6.7.1) — derived energy‑efficiency KPI in bit/J

## Synthetic generation

Cluster of 1 CB + 3–5 Coverage cells per group, ~20 groups. Baseline diurnal load on each cell. CB cell enters sleep at randomised times within a configured window (default: nightly between 22:00 and 02:00, drift ±90 min); on entry, CB load → 0 and a parameterised fraction (default 60–80%) of its diurnal load redistributes onto Coverage neighbours within 60 s. Wake‑up is the inverse transition, also randomised. Power consumption follows the load step‑wise with a configurable lag (10–60 s).

## Ground‑truth labels

- Per‑cell, per‑second sleep state ∈ {Active, Sleeping, Transitioning}
- Sleep‑entry and wake‑up timestamps
- Load redistribution coefficient per neighbour pair

## Headline metric

**Recovery time** = number of steps after a sleep‑entry transition until the rolling MAE of each neighbour's load forecast returns to within 1.2× of the pre‑transition rolling MAE. Reported as median across cells × transitions.

## Expected outcome by model family

- **Hand‑coded seasonal lookup** (SlotEWMA): catastrophic. The hour‑of‑week slot for "neighbour cell at 02:30 Tuesday" was learned with the CB awake; once the CB enters sleep, the slot value is permanently wrong until the slot has been re‑observed across enough sleep cycles. Recovery time ≥ 1 week.
- **Weekly batch retrainers** (SARIMA, Prophet, LightGBM): stale until next retrain. Recovery time ≤ 168 h, dominated by retrain cadence not algorithm.
- **Streaming online** (DriftMind, SNARIMAX): adapts within 10s of observations. Recovery time on the order of minutes.
- **Pretrained zero‑shot** (Chronos): unknown — depends on pretraining corpus; likely plateau at structural error floor.

## Why this matters operationally

Energy is the largest operational cost in modern RAN deployments. Cell sleep is the single biggest available lever. Forecaster errors during sleep transitions translate directly into either SLA breaches (under‑provisioning the absorbing cells) or wasted power (over‑provisioning). **This is operationally the most expensive category of forecast error in the deployment context.**
