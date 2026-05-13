# Scenario F — Failure prediction from KPI degradation trends

> **RAN relevance:** High. **Triply‑cited.**

## Source citations

- **3GPP TS 28.104 §7.2.3.1 / §8.4.3.1** — *MDA assisted Failure prediction*. Outputs `failurePredictionObject`, `potentialFailureType` ∈ {Operational, Physical, Time‑Domain Violation}, `eventTime`, `recommendedActions`.
- **ETSI GS ENI 001 §5.5.1** — *Network fault identification and prediction*. Verbatim: *"Performance and other problems generally exist before the equipment/service fails … one minute rapid optical layer failure location can be achieved."* The ENI document also names a concrete pre‑failure signature: FEC count, input optical power, laser bias current.
- **O‑RAN.WG1 TS 104 036 §4.15** — *O‑RAN Signalling Storm Protection* (the abrupt‑regime variant of failure detection).

## Operational description

Network elements degrade gradually before failing. Pre‑failure KPI signatures are subtle, multivariate, and rare in historical training data. **A model that adapts to the developing signature in real time can warn earlier than one that waits for the next retrain.**

## Trigger conditions

- PM counters breach configurable thresholds.
- Alarm precursor patterns appear in multivariate KPI space.

## Input KPIs

- `DRB.PacketLossRateUl.SNSSAI`, `DRB.F1UpacketLossRateUl/Dl` (TS 28.552 §5.1.3.1) — packet loss
- `DRB.PdcpPacketDropRateDl.SNSSAI`, `DRB.RlcPacketDropRateDl.SNSSAI` (TS 28.552 §5.1.3.2) — drop rates
- `MM.HoExeInterFail.cause`, `MM.HoResAlloInterFail.cause` (TS 28.552 §5.1.1.6) — handover failures by cause
- `RRC.ReEstabAtt`, `RRC.ReEstabSuccWithUeContext`, `…WithoutUeContext` (TS 28.552 §5.1.1.17) — RRC re‑establishment counters (RLF indicator)
- `PEE.AvgTemperature`, `PEE.MaxTemperature` (TS 28.552 §5.1.1.19.4) — thermal precursor for PA degradation
- `DRB.AirIfDelayDl`, `DRB.RlcDelayUl` (TS 28.552 §5.1.1.1) — delay tail under degradation

## Synthetic generation

~50 cells. At randomised times, inject failure scenarios:
1. **PA degradation** — temperature trend rises gradually (0.05 °C/hour for 12–24 h) before the PA goes into thermal protection. Co‑located: TX power capping, throughput cap, increased BLER.
2. **Fronthaul jitter onset** — `DRB.F1UpacketLossRateDl` rises gradually from baseline (50 PPM) to 5,000 PPM over 30–60 minutes before total link failure.
3. **RRC instability** — `RRC.ReEstabAtt` rises 5× over 10 minutes preceding mass disconnect event.
4. **Antenna VSWR drift** — wideband CQI distribution shifts left over hours.

## Ground‑truth labels

- Per‑cell failure type (pa_degradation | fronthaul_jitter | rrc_instability | vswr_drift)
- Failure timestamp
- Pre‑failure window (start of detectable signature)

## Headline metric

**Failure prediction lead time** — time between first anomaly score above threshold and the failure event. Reported per failure type with paired **false‑positive rate** at a fixed lead‑time target.

## Expected outcome by model family

- **Streaming forecasters with anomaly capability** (DriftMind): expected to detect within the pre‑failure window — lead times of 10–60 minutes for thermal scenarios, 1–10 minutes for fronthaul scenarios, seconds for RRC instability.
- **Batch retrainers without anomaly logic**: cannot detect.
- **Seasonal baselines**: cannot detect (no anomaly score).

## Why this matters operationally

Predictive maintenance is the operational holy grail. **A 10–60 minute lead time on a PA degradation event is the difference between a planned‑maintenance ticket and an unplanned outage.** ENI's "one‑minute rapid optical layer failure location" target is the operator‑stated benchmark.
