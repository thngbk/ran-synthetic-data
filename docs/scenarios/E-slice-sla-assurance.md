# Scenario E — Network slice SLA assurance with multi‑tenant load mix

> **RAN relevance:** High. **Triply‑cited.**

## Source citations

- **3GPP TS 28.104 §7.2.2.2 / §7.2.2.3 / §8.4.2.3** — *Network slice throughput analysis* and *Network slice traffic prediction*; explicit per‑NF traffic prediction for pre‑provisioning.
- **ETSI GS ENI 001 §5.5.2** — *Assurance of Service Requirements*. Verbatim: *"One slice reveals a considerable deviation from normal resource consumption patterns. Since this slice is deployed over a shared infrastructure where other slices and services are also provisioned, the abnormal behaviour may impact these other slices."*
- **O‑RAN.WG1 TS 104 036 §4.9** — *RAN Slice SLA Assurance* (slow loop / fast loop). **§4.12** — *NSSI Resource Allocation Optimization*, with explicit per‑S‑NSSAI PMs from TS 28.552.

## Operational description

Multiple slices share the same physical RAN. Each slice has distinct demand patterns — eMBB diurnal, URLLC flat, mMTC IoT‑cyclic. Slice priorities and SLAs must be enforced under transient mix changes (new tenant slice activation, ServiceProfile renegotiation, demand surge on one slice impacting another).

## Trigger conditions

- New slice activation event (per‑NF demand baseline shifts immediately)
- Slice ServiceProfile parameter change (e.g. `dLThptPerSlice` target raised)
- Cross‑slice contention event (one slice's surge starves another)

## Input KPIs

- `RRU.PrbUsedDl.SNSSAI`, `RRU.PrbUsedUl.SNSSAI` (TS 28.552 §5.1.1.2.5, .2.7) — per‑slice PRB
- `DRB.UEThpDl.SNSSAI`, `DRB.UEThpUl.SNSSAI` (TS 28.552 §5.1.1.3.1, .3.3)
- `DRB.AirIfDelayDl.SNSSAI`, `DRB.AirIfDelayUl.SNSSAI` (TS 28.552 §5.1.1.1)
- `DRB.PdcpSduVolumeDL_Filter`, `DRB.PdcpSduVolumeUL_Filter` (TS 28.552 §5.1.2.1)
- `GTP.InDataOctN3UPF.SNSSAI`, `GTP.OutDataOctN3UPF.SNSSAI` (TS 28.552 §5.4.1) — per‑slice volume
- `UTSNSI`, `DTSNSI` (TS 28.554 §6.3.2–.3) — composite slice throughput KPIs
- `DlUeThroughput_Nss.SNSSAI` (TS 28.554 §6.3.6.3.3) — slice‑level integrity SLA

## Synthetic generation

3–5 slices per cell with distinct demand profiles:
- **eMBB slice:** diurnal, daytime peak, weekend higher than weekday
- **URLLC slice:** ~flat with sub‑second jitter
- **mMTC slice:** hourly cyclic burst pattern (IoT polling)
- **Voice slice:** bimodal commute/evening pattern

Inject events:
1. **New slice activation** — fourth slice comes online at randomised time, immediately consumes 15–25% of cell capacity.
2. **Surge on one slice** — eMBB slice load spikes 3× over a 30 min window.
3. **Cross‑slice contention** — URLLC SLA breach because eMBB consumed all PRBs.

## Ground‑truth labels

- Per‑slice activation/deactivation timestamps
- Surge event timestamps
- SLA breach intervals

## Headline metric

**SLA breach prediction lead time** — how many minutes ahead does the forecaster predict the breach? Combined with **false‑positive rate** at a fixed lead‑time threshold.

## Expected outcome by model family

- **Streaming forecasters**: track per‑slice demand independently and predict breach onset minutes ahead.
- **Batch retrainers**: cannot adapt to a new slice's distribution until next retrain.
- **Seasonal baselines**: do not even know the slices exist.

## Why this matters operationally

Slice SLA assurance is the commercial value proposition of 5G. **Predictive breach detection is the difference between proactive renegotiation and customer‑facing penalty.**
