# Scenario D — MRO handover anomaly bursts

> **RAN relevance:** High. **Triply‑cited.**

## Source citations

- **3GPP TS 28.104 §7.2.5.1** — *Mobility performance analysis*. Identifies too‑early / too‑late / ping‑pong handover anomalies.
- **3GPP TR 28.908 §5.2.2.2.3** — explicitly cites the MLB/MRO conflict pattern: *"MLB unexpectedly removing overload in a cell."*
- **O‑RAN.WG1 TS 104 036 §4.19 (Integrated SON / MRO)** + **§4.6 (Beam‑based MRO, bMRO)** — define per‑beam handover failure statistics with KPM granularity ≥ 1 s.

## Operational description

Mobility regime changes (commute flow, event egress, train passing through coverage area, weekday/weekend transitions) produce non‑stationary handover patterns. UE dwell‑time and HO rate distributions shift on minute‑to‑hour scales. Beam‑based MRO (bMRO) sees per‑beam HO success rates change with crowd density.

## Trigger conditions

- Anomaly counter spike: `HO.IntraSys.TooEarly`, `.TooLate`, or `.ToWrongCell` exceeds threshold over a sliding window.
- Sustained drop in `GRANHOSR`.

## Input KPIs

- `MM.HoExeInterReq`, `.HoExeInterSucc`, `.HoExeInterFail.cause` (TS 28.552 §5.1.1.6.1.7–.9)
- `MM.HoExeIntraReq`, `.HoExeIntraSucc` (TS 28.552 §5.1.1.6.2)
- `HO.IntraSys.TooEarly`, `.TooLate`, `.ToWrongCell` (TS 28.552 §5.1.1.25.1)
- `HO.InterSys.TooEarly`, `.TooLate`, `.Unnecessary`, `.Ping-pong` (TS 28.552 §5.1.1.25.2–.4)
- `MR.IntraCellSSBSwitchReq`, `MR.IntrCellSuccSSBSwitch` (TS 28.552 §5.1.1.21) — per‑beam switching
- `GRANHOSR` (TS 28.554 §6.6.1)

## Synthetic generation

Cells along a "mobility corridor" (highway, transit line). Inject mobility events:
1. **Commute peak** — HO request rate ramps up 4× from 07:00–09:00 daily.
2. **Event egress** — sharp burst (HO request rate 10× baseline) over a 20–40 min window at randomised event times.
3. **Train passage** — moving HO event hot‑spot crosses ~5 cells in sequence, each cell experiencing a 60–120 s burst.

## Ground‑truth labels

- Per‑event timestamps, mobility class (commute | event | train)
- Affected cell sequence
- Expected HO failure‑cause distribution

## Headline metric

**Burst detection rate + false‑positive rate** at a fixed alarm threshold. Streaming forecasters score on lead time + FPR.

## Expected outcome by model family

- **Streaming forecasters**: track per‑cell HO rate and per‑beam SSB switch rate during bursts.
- **Seasonal lookups**: detect commute peaks (recur daily) but miss event‑driven and train‑passage bursts.
- **Batch retrainers**: similar to seasonal — sees the recurring cycles, misses the transients.

## Why this matters operationally

MRO is one of the canonical SON functions and is explicitly named in 3GPP TR 37.817 (NG‑RAN AI/ML use cases). **A forecaster that cannot track HO regime changes is structurally unsuited to the SON deployment context.**
