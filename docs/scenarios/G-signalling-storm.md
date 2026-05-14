# Scenario G — Signalling storm / abrupt regime change

> **RAN relevance:** High. **O‑RAN explicit; cross‑cited in 3GPP and ENI.**

## Source citations

- **O‑RAN.WG1 TS 104 036 §4.15** — *O‑RAN Signalling Storm Protection*. Verbatim: *"Misbehaving or compromised IoT/devices launch signaling‑storm DDoS via repeated registration."* Defines the input set: connection establishment timestamps, cell ID, C‑RNTI / 5G‑GUTI, RSRP/RSRQ, Timing Advance, Beam ID.
- **3GPP TS 28.104 §7.2.7.2 / §8.4.7.1.3** — *5GC Control plane congestion analysis*. Verbatim: *"It is desirable to use MDA to assist control plane congestion analysis in order to detect, prevent or resolve identified congestion issue."*
- **ETSI GS ENI 001 §5.5.2** (Assurance of Service Requirements) — covers the spike‑detection‑and‑prioritisation pattern.

## Operational description

A device population (firmware push, mass‑event arrival, IoT botnet) launches a signalling storm — abrupt non‑seasonal spike in `RRC.ConnEstabAtt` per cell. **The storm has no representation in last week's training data and unfolds over seconds to minutes.**

## Trigger conditions

Connection establishment rate exceeds N × baseline within a sliding window. N is configurable (typical 3–10×).

## Input KPIs

- `RRC.ConnEstabAtt.Cause` (TS 28.552 §5.1.1.15.1) — *primary signal*; cause‑by‑cause breakdown
- `RRC.ConnEstabSucc.Cause` (TS 28.552 §5.1.1.15.2) — paired success counter
- `RRC.ConnMean`, `RRC.ConnMax` (TS 28.552 §5.1.1.4) — connected‑user counts
- `PAG.ReceivedNbrCnInitiated`, `PAG.ReceivedNbrRanIntiated`, `PAG.DiscardedNbr` (TS 28.552 §5.1.1.27) — paging records
- `RACH.PreambleACell`, `.PreambleBCell` (TS 28.552 §5.1.1.20.1) — RACH preambles per cell
- `UECNTX.ConnEstabAtt.Cause` (TS 28.552 §5.1.1.16) — NG signalling connection setup atomics

## Synthetic generation

Inject abrupt connection establishment surges:
1. **IoT botnet** — 10–50× spike in `RRC.ConnEstabAtt` from a small subset of UEs (identified by C‑RNTI grouping in ground truth) over a 60–600 s window.
2. **Firmware push** — moderate spike (3–5×) but sustained over hours; vendor pushing updates to a UE class.
3. **Mass‑event arrival** — 4–8× spike over a 20–40 min window (event egress / venue ingress).

## Ground‑truth labels

- Per‑event start/end timestamps
- Intensity (multiplier vs baseline)
- Affected cell set
- Storm class (botnet | firmware | mass_event)

## Headline metric

**Detection lead time** at fixed FPR. Streaming detectors should hit detection within seconds; batch retrainers cannot detect inside their retrain window.

## Expected outcome by model family

This is the regime where streaming pattern matching is structurally most differentiated. **Streaming detectors that track per‑observation distribution shifts can catch abrupt establishment‑cause changes within a few observations; weekly retrainers are blind during the entire storm window.**

## Why this matters operationally

Signalling storms are an active operational concern at scale. They cause cascading core‑network impact (AMF/SMF congestion). **Detection latency directly determines whether the storm is contained at the affected cells or propagates network‑wide.**
