# Scenario C — Mobility load balancing (MLB) regime change

> **RAN relevance:** High. **Triply‑cited.**

## Source citations

- **3GPP TR 28.908 §5.1.10.2.2** — *Automated Load Balancing*. Verbatim: *"AutoLB ML entity helps to decide how to distribute load among cells."*
- **3GPP TS 28.104 §7.2.2.5** — *Network slice load analysis*.
- **ETSI GS ENI 001 §5.3.6** — *Application Characteristic based Network Operation*. Verbatim: *"thousands of KPI per second … subtle patterns that can have a large impact on user experience."*
- **O‑RAN.WG1 TS 104 036 §4.5 (Traffic Steering)**, **§4.19 (Integrated SON / MLB)** — define cell‑load + active‑user counts + PRB utilisation as the input set.

## Operational description

Operator pushes a configuration change (new neighbour relations, new beam pattern, sector split, Cell Individual Offset adjustment, or sibling‑cell capacity change). Traffic redistributes across the affected cell set within minutes. **The new equilibrium does not match last week's training data.**

## Trigger conditions

- Configuration change event (e.g. CIO adjusted on cell A → traffic shifts to cell B)
- Sibling‑cell capacity event (e.g. neighbour cell goes into maintenance, all its load arrives)

## Input KPIs

- `RRU.PrbTotDl`, `RRU.PrbTotUl` (TS 28.552 §5.1.1.2)
- `RRU.PrbUsedDl.SNSSAI`, `RRU.PrbUsedUl.SNSSAI` (TS 28.552 §5.1.1.2.5, .2.7) — per‑slice
- `DRB.MeanActiveUeDl`, `DRB.MaxActiveUeDl` (TS 28.552 §5.1.1.23) — active UE counts
- `MM.HoExeInterReq`, `MM.HoExeInterSucc`, `MM.HoExeInterFail.cause` (TS 28.552 §5.1.1.6.1.7–.9)
- `MM.HoExeIntraReq`, `MM.HoExeIntraSucc` (TS 28.552 §5.1.1.6.2)
- `GRANHOSR` (TS 28.554 §6.6.1) — composite handover success rate

## Synthetic generation

Clusters of 5–10 cells. At randomised times, inject one of:
1. **CIO adjustment** — δ (3–6 dB) shifts a fraction (15–30%) of cell A's load to cell B over 1–5 minutes.
2. **Neighbour maintenance window** — cell C goes offline; its full load redistributes across {A, B, D, E} over 30–120 s.
3. **Sector split / capacity expansion** — cell A's load halves over a 5–10 min window as cell A' comes online.

## Ground‑truth labels

- Per‑event timestamp, type (cio | maintenance | sector_split)
- Affected cell set
- Load redistribution matrix

## Headline metric

**Post‑shift cumulative error** = sum of absolute errors over the first N steps after the configuration event, normalised by `norm_std`. Reported per event type.

## Expected outcome by model family

Same shape as Scenario A — seasonal baselines stale until next slot cycle; streaming forecasters adapt within minutes; batch retrainers wait until next retrain.

## Why this matters operationally

Configuration changes are routine — they happen weekly to monthly per cell across an operator's network. **A forecaster that requires a full retrain cycle after every such change is not deployable at the per‑cell granularity that AI‑driven RAN management requires.**
