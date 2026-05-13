# Scenario H — Handover‑target resource saturation

> **RAN relevance:** High. **3GPP explicit (the canonical fast‑loop case).**

## Source citations

- **3GPP TS 28.104 §7.2.5.2 / §8.4.5.2** — *Handover optimization analysis (UE‑load‑based)*. Verbatim: outputs *"current and predicted virtual & radio resource consumption of gNB; selection priority for target cell; cells to **avoid** for an indicated time period."*

## Operational description

Per‑handover decisions need to predict the *target gNB's* virtual + radio resource state to avoid HO rejection. **Cloud‑RAN auto‑scaling, restarts, and sibling‑tenant load make week‑old PRB / vCPU baselines unreliable.**

## Trigger conditions

Handover request arrives at source gNB; target‑cell selection requires a per‑target‑cell forecast of resource availability over the next 5–30 seconds.

## Input KPIs

- `RRU.PrbTotDl`, `RRU.PrbTotUl` (TS 28.552 §5.1.1.2) — physical PRB utilisation, target cell
- `VirtualResUtilizaiton` (TS 28.554 §6.4.2) — virtualised resource utilisation (CPU, memory, disk)
- `DRB.PdcpSduVolumeDL_Filter` (TS 28.552 §5.1.2.1) — data volume on target cell
- MDT RSRP / RSRQ / SINR (per O‑RAN UC) — radio quality at target

## Synthetic generation

Cluster of cells with shared O‑Cloud infrastructure. Inject:
1. **Sibling‑tenant surge** — neighbouring cell's load consumes shared vCPU pool.
2. **O‑Cloud auto‑scale event** — target cell's vCPU allocation halves for 2–5 minutes during scaling.
3. **Restart** — target cell briefly unavailable, then load‑imbalanced as it ramps.

## Ground‑truth labels

- Per‑event timestamps
- Affected cell set
- Resource state during event

## Headline metric

**Per‑handover target‑cell prediction MAE** at horizon h ∈ {5 s, 30 s, 5 min}.

## Expected outcome by model family

- **Streaming forecasters**: track target‑cell state at sub‑minute granularity.
- **Batch retrainers**: operate at granularity periods (5–60 minutes) too coarse for per‑handover decisions.

## Why this matters operationally

Handover decisions are the highest‑frequency control loop in RAN. Wrong target selection causes drops, ping‑pongs, and SLA violations. **This is the canonical "fast‑loop" forecast where streaming is structurally appropriate and batch is structurally not.**
