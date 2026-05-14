# Scenario B — Coverage problem onset

> **RAN relevance:** High. **Triply‑cited.**

## Source citations

- **3GPP TS 28.104 §7.2.1.1 / §8.4.1.1** — *Coverage problem analysis*. Outputs `coverageProblemId`, `coverageProblemType` ∈ {WeakCoverage, CoverageHole, PilotPollution, Overshoot, DlUlChannelCoverageMismatch}, plus a `radioEnvironmentMap`.
- **ETSI GS ENI 001 §5.3.2** — *Radio Coverage and Capacity Optimization*. Verbatim: *"Performing exhaustive search to find optimal RF parameter combination … can be extremely complex. Today's network lacks efficient way."*
- **O‑RAN.WG1 TS 104 036 §4.19** — *Integrated SON; CCO loop*. Defines RLF, MDT, and RCEF reports as canonical inputs.

## Operational description

A coverage event (mast outage, antenna tilt change, environmental obstruction, or vegetation seasonal change) shifts the RSRP/SINR distribution of one or more cells over minutes to hours. The change is **non‑seasonal** — it has no representation in last week's training data.

## Trigger conditions

Verbatim from TS 28.104 §7.2.1.1: *"necessary to proactively avoid the RAN coverage related problems well before they occur."*

Specifically:
- The RSRP distribution at a cell shifts beyond a configured threshold.
- The rolling mean of UE‑reported RSRP drops below a quality floor.

## Input KPIs

- `L1M.SS-RSRP.BinX` (TS 28.552 §5.1.1.22.1) — SS‑RSRP distribution per SSB beam (–140 to –40 dBm)
- `CARR.WBCQIDist.BinX.BinY.BinZ` (TS 28.552 §5.1.1.11.1) — Wideband CQI distribution
- `CARR.PDSCHMCSDist.BinX.BinY.BinZ` (TS 28.552 §5.1.1.12.1) — PDSCH MCS distribution
- `L1M.PHR1.BinX` (TS 28.552 §5.1.1.26.1) — Power headroom distribution
- `MM.HoExeInterFail.cause` (TS 28.552 §5.1.1.6.1.9) — handover failures by cause (radio‑link cause spikes during coverage events)

## Synthetic generation

~50 cells. At randomised times per cell, inject one of three coverage events:
1. **Antenna tilt change** — RSRP distribution shifts by parameterised δ (default mean –3 dB) over a 10–60 s ramp.
2. **Mast outage / partial sector failure** — abrupt step change; RSRP for affected UEs drops 8–15 dB over 1–5 s.
3. **Slow seasonal drift** — vegetation growth or building construction; RSRP mean drifts –0.05 dB/day for 30 days.

CQI and MCS distributions shift correspondingly via a calibrated mapping. Handover failure rate increases proportional to RSRP shift magnitude.

## Ground‑truth labels

- Per‑cell event type (antenna_tilt | mast_outage | slow_drift)
- Event timestamp, magnitude, ramp duration

## Headline metric

**Detection lead time** = time between when the model's anomaly score first exceeds threshold and when the operator‑defined "coverage problem" condition is met (e.g. cell mean RSRP below floor for 30 consecutive minutes). Reported per event type.

## Expected outcome by model family

- **Seasonal lookups** (SlotEWMA): cannot detect — they have no anomaly score.
- **Batch retrainers**: detect at retrain‑cadence latency; weekly retrain → up to 168 h lag.
- **Streaming online**: designed to detect distribution shifts in clusters. Expected lead time on antenna‑tilt shifts: 5–30 minutes. On abrupt mast outages: seconds.
- **Pretrained**: structurally unable to recognise cell‑specific shifts unless fine‑tuned.

## Why this matters operationally

Coverage problems are the highest‑frequency operational issue in RAN. Detection lead time directly translates into the difference between a self‑healing event and a customer‑visible outage.
