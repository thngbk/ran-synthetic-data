# ranfst — RAN Synthetic Telemetry Generator

Reproducible synthetic telemetry generator for Radio Access Network (RAN) forecasting and anomaly-detection benchmarks. Emits per‑(cell, KPI) time series across **nine network scenarios** — every scenario, every KPI, and every operational pattern anchored in primary 3GPP, ETSI, and O‑RAN specifications.

Every dataset is **byte‑identical reproducible** from a `(scenario, seed, ranfst version)` triple. Anyone running the same combination produces the same bytes on any host.

---

## Scenarios

Nine scenarios spanning the operationally relevant RAN regime mix. Each is anchored in 3GPP TS 28.104 Management Data Analytics (MDA) service capabilities.

| ID | Name | Triply‑cited¹ | Primary 3GPP citation | Operational regime |
|---|---|---|---|---|
| **S** | Stationary periodic baseline (control) | — | TS 28.552 §5.1 | Diurnal + weekly seasonality, no events. |
| **A** | Energy‑saving cell sleep transition | ✓ | TS 28.104 §7.2.4.1 / §8.4.4.1 | Step‑wise neighbour‑load redistribution. |
| **B** | Coverage problem onset | ✓ | TS 28.104 §7.2.1.1 | Gradual RSRP / RSRQ degradation. |
| **C** | Mobility load balancing (MLB) regime change | ✓ | TS 28.104 §7.2.2.5; TR 28.908 §5.1.10.2.2 | Load redistribution across a neighbourhood. |
| **D** | MRO handover anomaly bursts | ✓ | TS 28.104 §7.2.5.1 | Multiplicative bursts on `MM.HoExeInterReq`. |
| **E** | Network slice SLA assurance | ✓ | TS 28.104 §7.2.2.2/3 | Per‑slice eMBB / URLLC / mMTC mix shifts. |
| **F** | Failure prediction from KPI degradation | ✓ | TS 28.104 §7.2.3.1 / §8.4.3.1 | Slow degradation preceding a failure. |
| **G** | Signalling storm / abrupt regime change | ✓ | TS 28.104 §7.2.7.2; ETSI GS ENI 001 §5.5.2 | Abrupt 5–20× spike on `RRC.ConnEstabAtt`. |
| **H** | Handover‑target resource saturation | ✓ | TS 28.104 §7.2.5.x | Saturation when source‑cell offered load > capacity. |

¹ "Triply‑cited" means the scenario's regime appears independently in (a) the 3GPP management view (TS 28.104 / TR 28.908), (b) the ETSI ENI use case catalogue (GS ENI 001), and (c) the O‑RAN WG1 implementation specification (TS 104 036).

The remainder of this section is a per‑scenario reference: real‑world regime, primary‑source citations, what the generator injects, KPIs emitted, and operational stakes. Full per‑scenario specifications with trigger conditions and complete event schemas live under [`docs/scenarios/`](docs/scenarios/).

---

### S — Stationary periodic baseline (control)

**Operational regime.** Unperturbed cells with strong daily and weekly seasonality. No regime changes, no drift, no events — the control. The regime hand‑coded seasonal lookups were effectively designed for, included as a credibility floor on top of which the eight perturbed scenarios layer their events.

**Reference specifications.**
- *3GPP TS 28.554 §6.4* (Utilization KPI), *§6.3* (Integrity KPI) — evaluation metrics
- *3GPP TS 28.552 §5.1.1.2* (PRB usage), *§5.1.1.4* (RRC connections) — input series
- *ETSI GS ENI 001 §5.3.2* — generic radio coverage and capacity context

**Synthetic generation.** ~50 cells, 35 days each, slow‑loop (5‑min) granularity. Daily seasonality (24 h period with rush‑hour peaks), weekly seasonality (weekday/weekend distinction). Gaussian noise floor at 5–10% of signal magnitude. Events sidecar is empty (`n_events = 0`).

**KPIs emitted.** `RRU.PrbTotDl`, `RRU.PrbTotUl`, `RRC.ConnMean`, `RRC.ConnMax`, `DRB.UEThpDl`, `DRB.UEThpUl`, `MM.HoExeInterReq`, `MM.HoExeInterSucc`, `PEE.AvgPower`. Full per‑KPI 3GPP TS 28.552 §5.1.1 paragraph citations: [`docs/scenarios/S-stationary-control.md`](docs/scenarios/S-stationary-control.md).

**Operational significance.** A forecaster that cannot match seasonal lookups on stationary periodic data is not deployment‑grade. Scenario S verifies the floor and serves as the unperturbed reference against which the other eight scenarios' regime shifts are measured.

---

### A — Energy‑saving cell sleep transition

**Operational regime.** When a Capacity Booster (CB) cell enters energy‑saving sleep, its traffic is absorbed by neighbour Coverage cells; the load distribution changes step‑wise within seconds, and the inverse step occurs at wake‑up. A weekly retrainer's neighbour‑load model is wrong for hours after each transition.

**Reference specifications.**
- *3GPP TS 28.104 §7.2.4.1 / §8.4.4.1* — *Energy saving analysis*. Outputs `trafficLoadTrends` (explicit load forecast driving sleep decisions) plus recommendations for ES‑Cell selection, candidate take‑over cells, time to enter/terminate, and load thresholds.
- *3GPP TR 28.908 §5.2.7.2.1* — *RAN domain ES; AI/ML inference configuration*: *"RAN domain ES can use AI to formulate energy saving solutions … ML entity configuration needs to be triggered to enable RAN domain ES function."*
- *ETSI GS ENI 001 §5.2.5* — *Energy saving in radio network*: notes that 5G base‑station power consumption is 2.5–3.5× that of 4G, and "5G energy saving is the most urgent problem to be solved by operators in 5G commercial deployment."
- *O‑RAN.WG1 TS 104 036 §4.21* — *Energy Saving*. Defines EE/EC measurement reports, per‑cell / per‑carrier load statistics, and per‑carrier transmit‑power metrics as the canonical input set.

**Synthetic generation.** Cluster of 1 CB + 3–5 Coverage cells per group, ~20 groups. CB enters sleep at randomised times within a configured window (default: nightly 22:00–02:00, drift ±90 min); on entry, CB load → 0 and 60–80% of its diurnal load redistributes onto Coverage neighbours within 60 s. Wake‑up is the inverse. Power follows load step‑wise with a configurable lag (10–60 s). Ground‑truth labels: per‑cell sleep state ∈ {Active, Sleeping, Transitioning}, sleep‑entry / wake‑up timestamps, load redistribution coefficient per neighbour pair.

**KPIs emitted.** Default emission: `RRU.PrbTotDl`, `RRU.PrbTotUl`, `RRC.ConnMean`, `RRC.ConnMax`, `DRB.UEThpDl`, `DRB.UEThpUl`, `MM.HoExeInterReq`, `MM.HoExeInterSucc`, `PEE.AvgPower`. Per the spec, extended emissions can add `PEE.Energy`, `CARR.MeanTxPwr`, `CARR.MaxTxPwr`, and the derived `EEMN,DV` (bit/J) — see [`docs/scenarios/A-energy-saving-sleep.md`](docs/scenarios/A-energy-saving-sleep.md).

**Operational significance.** Energy is the largest operational cost in modern RAN deployments and cell sleep is the single biggest available lever. Forecaster errors during sleep transitions translate directly into either SLA breaches (under‑provisioning absorbing cells) or wasted power (over‑provisioning).

---

### B — Coverage problem onset

**Operational regime.** A coverage event (mast outage, antenna tilt change, environmental obstruction, vegetation seasonal change) shifts the RSRP / SINR distribution of one or more cells over minutes to hours. The change is non‑seasonal — it has no representation in last week's training data.

**Reference specifications.**
- *3GPP TS 28.104 §7.2.1.1 / §8.4.1.1* — *Coverage problem analysis*. Outputs `coverageProblemId`, `coverageProblemType` ∈ {WeakCoverage, CoverageHole, PilotPollution, Overshoot, DlUlChannelCoverageMismatch}, plus a `radioEnvironmentMap`.
- *ETSI GS ENI 001 §5.3.2* — *Radio Coverage and Capacity Optimization*: "Performing exhaustive search to find optimal RF parameter combination … can be extremely complex. Today's network lacks efficient way."
- *O‑RAN.WG1 TS 104 036 §4.19* — *Integrated SON; CCO loop*. Defines RLF, MDT, and RCEF reports as canonical inputs.

**Synthetic generation.** ~50 cells. At randomised times per cell, inject one of three coverage events: (1) antenna tilt change — RSRP shifts by parameterised δ (default mean –3 dB) over a 10–60 s ramp; (2) mast outage / partial sector failure — abrupt step change, RSRP for affected UEs drops 8–15 dB over 1–5 s; (3) slow seasonal drift — vegetation or construction; RSRP mean drifts –0.05 dB/day for 30 days. CQI and MCS distributions shift correspondingly via a calibrated mapping; handover failure rate increases proportional to RSRP shift magnitude.

**KPIs emitted.** `L1M.SS-RSRP.BinX` (TS 28.552 §5.1.1.22.1), `CARR.WBCQIDist.BinX.BinY.BinZ` (§5.1.1.11.1), `CARR.PDSCHMCSDist.BinX.BinY.BinZ` (§5.1.1.12.1), `L1M.PHR1.BinX` (§5.1.1.26.1), `MM.HoExeInterFail.cause` (§5.1.1.6.1.9). Full citations: [`docs/scenarios/B-coverage-problem-onset.md`](docs/scenarios/B-coverage-problem-onset.md).

**Operational significance.** Coverage problems are the highest‑frequency operational issue in RAN. The window between onset detection and self‑heal action determines whether the event becomes a customer‑visible outage.

---

### C — Mobility load balancing (MLB) regime change

**Operational regime.** Operator pushes a configuration change (new neighbour relations, new beam pattern, sector split, Cell Individual Offset adjustment, sibling‑cell capacity change). Traffic redistributes across the affected cell set within minutes. The new equilibrium does not match last week's training data.

**Reference specifications.**
- *3GPP TR 28.908 §5.1.10.2.2* — *Automated Load Balancing*: "AutoLB ML entity helps to decide how to distribute load among cells."
- *3GPP TS 28.104 §7.2.2.5* — *Network slice load analysis*.
- *ETSI GS ENI 001 §5.3.6* — *Application Characteristic based Network Operation*: "thousands of KPI per second … subtle patterns that can have a large impact on user experience."
- *O‑RAN.WG1 TS 104 036 §4.5* (Traffic Steering), *§4.19* (Integrated SON / MLB) — define cell‑load + active‑user counts + PRB utilisation as the input set.

**Synthetic generation.** Clusters of 5–10 cells. At randomised times, inject one of: (1) CIO adjustment — δ (3–6 dB) shifts 15–30% of cell A's load to cell B over 1–5 min; (2) neighbour maintenance window — cell C goes offline, its full load redistributes across {A, B, D, E} over 30–120 s; (3) sector split / capacity expansion — cell A's load halves over a 5–10 min window as cell A' comes online. Ground‑truth labels record per‑event timestamp, type ∈ {cio, maintenance, sector_split}, affected cell set, and load redistribution matrix.

**KPIs emitted.** `RRU.PrbTotDl`, `RRU.PrbTotUl`, `RRU.PrbUsedDl.SNSSAI`, `RRU.PrbUsedUl.SNSSAI`, `DRB.MeanActiveUeDl`, `DRB.MaxActiveUeDl`, `MM.HoExeInterReq`/`Succ`/`Fail.cause`, `MM.HoExeIntraReq`/`Succ`, `GRANHOSR` (TS 28.554 §6.6.1). Full citations: [`docs/scenarios/C-mlb-regime-change.md`](docs/scenarios/C-mlb-regime-change.md).

**Operational significance.** Configuration changes are routine — weekly to monthly per cell across an operator's network. A forecaster that requires a full retrain cycle after every such change is not deployable at the per‑cell granularity AI‑driven RAN management requires.

---

### D — MRO handover anomaly bursts

**Operational regime.** Mobility regime changes (commute flow, event egress, train passing through coverage, weekday/weekend transitions) produce non‑stationary handover patterns. UE dwell‑time and HO rate distributions shift on minute‑to‑hour scales. Beam‑based MRO (bMRO) sees per‑beam HO success rates change with crowd density.

**Reference specifications.**
- *3GPP TS 28.104 §7.2.5.1* — *Mobility performance analysis*. Identifies too‑early, too‑late, and ping‑pong handover anomalies.
- *3GPP TR 28.908 §5.2.2.2.3* — explicitly cites the MLB/MRO conflict pattern: "MLB unexpectedly removing overload in a cell."
- *O‑RAN.WG1 TS 104 036 §4.19* (Integrated SON / MRO) + *§4.6* (Beam‑based MRO, bMRO) — define per‑beam handover failure statistics with KPM granularity ≥ 1 s.

**Synthetic generation.** Cells along a "mobility corridor" (highway, transit line). Inject mobility events: (1) commute peak — HO request rate ramps 4× from 07:00–09:00 daily; (2) event egress — sharp burst at 10× baseline over a 20–40 min window at randomised event times; (3) train passage — moving HO event hot‑spot crosses ~5 cells in sequence, each cell experiencing a 60–120 s burst. Ground‑truth labels record per‑event timestamps, mobility class ∈ {commute, event, train}, affected cell sequence, and expected HO failure‑cause distribution.

**KPIs emitted.** `MM.HoExeInterReq`/`Succ`/`Fail.cause` (TS 28.552 §5.1.1.6.1.7–.9), `MM.HoExeIntraReq`/`Succ` (§5.1.1.6.2), `HO.IntraSys.TooEarly`/`TooLate`/`ToWrongCell` (§5.1.1.25.1), `HO.InterSys.TooEarly`/`TooLate`/`Unnecessary`/`Ping-pong` (§5.1.1.25.2–.4), `MR.IntraCellSSBSwitchReq`/`MR.IntrCellSuccSSBSwitch` (§5.1.1.21) — per‑beam switching, `GRANHOSR` (TS 28.554 §6.6.1). Full citations: [`docs/scenarios/D-mro-handover-bursts.md`](docs/scenarios/D-mro-handover-bursts.md).

**Operational significance.** MRO is a canonical SON function explicitly named in 3GPP TR 37.817 (NG‑RAN AI/ML use cases). A forecaster that cannot track HO regime changes is structurally unsuited to the SON deployment context.

---

### E — Network slice SLA assurance (multi‑tenant load mix)

**Operational regime.** Multiple slices share the same physical RAN. Each slice has distinct demand patterns — eMBB diurnal, URLLC flat with sub‑second jitter, mMTC IoT‑cyclic. Slice priorities and SLAs must be enforced under transient mix changes (new tenant slice activation, ServiceProfile renegotiation, demand surge on one slice impacting another).

**Reference specifications.**
- *3GPP TS 28.104 §7.2.2.2 / §7.2.2.3 / §8.4.2.3* — *Network slice throughput analysis* and *Network slice traffic prediction*; explicit per‑NF traffic prediction for pre‑provisioning.
- *ETSI GS ENI 001 §5.5.2* — *Assurance of Service Requirements*: "One slice reveals a considerable deviation from normal resource consumption patterns. Since this slice is deployed over a shared infrastructure where other slices and services are also provisioned, the abnormal behaviour may impact these other slices."
- *O‑RAN.WG1 TS 104 036 §4.9* — *RAN Slice SLA Assurance* (slow loop / fast loop). *§4.12* — *NSSI Resource Allocation Optimization*, with explicit per‑S‑NSSAI PMs from TS 28.552.

**Synthetic generation.** 3–5 slices per cell with distinct demand profiles: eMBB (diurnal, daytime peak, weekend higher than weekday), URLLC (~flat with sub‑second jitter), mMTC (hourly cyclic burst pattern, IoT polling), Voice (bimodal commute/evening). Events: (1) new slice activation — fourth slice comes online at randomised time, immediately consumes 15–25% of cell capacity; (2) surge on one slice — eMBB spikes 3× over a 30 min window; (3) cross‑slice contention — URLLC SLA breach because eMBB consumed all PRBs.

**KPIs emitted.** `RRU.PrbUsedDl.SNSSAI`, `RRU.PrbUsedUl.SNSSAI`, `DRB.UEThpDl.SNSSAI`, `DRB.UEThpUl.SNSSAI`, `DRB.AirIfDelayDl.SNSSAI`, `DRB.AirIfDelayUl.SNSSAI`, `DRB.PdcpSduVolumeDL_Filter`, `DRB.PdcpSduVolumeUL_Filter`, `GTP.InDataOctN3UPF.SNSSAI`, `GTP.OutDataOctN3UPF.SNSSAI`, `UTSNSI`, `DTSNSI`, `DlUeThroughput_Nss.SNSSAI`. Full citations: [`docs/scenarios/E-slice-sla-assurance.md`](docs/scenarios/E-slice-sla-assurance.md).

**Operational significance.** Slice SLA assurance is the commercial value proposition of 5G. Predictive breach detection is the difference between proactive renegotiation and customer‑facing penalty.

---

### F — Failure prediction from KPI degradation

**Operational regime.** Network elements degrade gradually before failing. Pre‑failure KPI signatures are subtle, multivariate, and rare in historical training data. A model that adapts to the developing signature in real time can warn earlier than one that waits for the next retrain.

**Reference specifications.**
- *3GPP TS 28.104 §7.2.3.1 / §8.4.3.1* — *MDA assisted Failure prediction*. Outputs `failurePredictionObject`, `potentialFailureType` ∈ {Operational, Physical, Time‑Domain Violation}, `eventTime`, `recommendedActions`.
- *ETSI GS ENI 001 §5.5.1* — *Network fault identification and prediction*: "Performance and other problems generally exist before the equipment/service fails … one minute rapid optical layer failure location can be achieved." Names concrete pre‑failure signatures: FEC count, input optical power, laser bias current.
- *O‑RAN.WG1 TS 104 036 §4.15* — *O‑RAN Signalling Storm Protection* (the abrupt‑regime variant of failure detection).

**Synthetic generation.** ~50 cells. At randomised times, inject failure scenarios: (1) PA degradation — temperature trend rises 0.05 °C/hour for 12–24 h before thermal protection; co‑located TX power capping, throughput cap, increased BLER; (2) fronthaul jitter onset — `DRB.F1UpacketLossRateDl` rises gradually from baseline (50 PPM) to 5 000 PPM over 30–60 min before total link failure; (3) RRC instability — `RRC.ReEstabAtt` rises 5× over 10 min preceding mass‑disconnect; (4) antenna VSWR drift — wideband CQI distribution shifts left over hours.

**KPIs emitted.** `DRB.PacketLossRateUl.SNSSAI`, `DRB.F1UpacketLossRateUl`/`Dl`, `DRB.PdcpPacketDropRateDl.SNSSAI`, `DRB.RlcPacketDropRateDl.SNSSAI`, `MM.HoExeInterFail.cause`, `MM.HoResAlloInterFail.cause`, `RRC.ReEstabAtt`, `RRC.ReEstabSuccWithUeContext`, `…WithoutUeContext`, `PEE.AvgTemperature`, `PEE.MaxTemperature`, `DRB.AirIfDelayDl`, `DRB.RlcDelayUl`. Full citations: [`docs/scenarios/F-failure-prediction.md`](docs/scenarios/F-failure-prediction.md).

**Operational significance.** Predictive maintenance is the operational holy grail. A 10–60 minute lead time on a PA degradation event is the difference between a planned‑maintenance ticket and an unplanned outage. ENI's "one‑minute rapid optical layer failure location" target is the operator‑stated benchmark.

---

### G — Signalling storm / abrupt regime change

**Operational regime.** A device population (firmware push, mass‑event arrival, IoT botnet) launches a signalling storm — an abrupt non‑seasonal spike in `RRC.ConnEstabAtt` per cell. The storm has no representation in last week's training data and unfolds over seconds to minutes.

**Reference specifications.**
- *O‑RAN.WG1 TS 104 036 §4.15* — *O‑RAN Signalling Storm Protection*: "Misbehaving or compromised IoT/devices launch signaling‑storm DDoS via repeated registration." Defines the input set: connection establishment timestamps, cell ID, C‑RNTI / 5G‑GUTI, RSRP/RSRQ, Timing Advance, Beam ID.
- *3GPP TS 28.104 §7.2.7.2 / §8.4.7.1.3* — *5GC Control plane congestion analysis*: "It is desirable to use MDA to assist control plane congestion analysis in order to detect, prevent or resolve identified congestion issue."
- *ETSI GS ENI 001 §5.5.2* — Assurance of Service Requirements; covers the spike‑detection‑and‑prioritisation pattern.

**Synthetic generation.** Inject abrupt connection establishment surges: (1) IoT botnet — 10–50× spike in `RRC.ConnEstabAtt` from a small subset of UEs (identified by C‑RNTI grouping in ground truth) over a 60–600 s window; (2) firmware push — moderate 3–5× spike sustained over hours, vendor pushing updates to a UE class; (3) mass‑event arrival — 4–8× spike over a 20–40 min window. Ground‑truth labels record per‑event start/end timestamps, intensity multiplier, affected cell set, storm class ∈ {botnet, firmware, mass_event}.

**KPIs emitted.** `RRC.ConnEstabAtt.Cause` (primary signal, TS 28.552 §5.1.1.15.1), `RRC.ConnEstabSucc.Cause` (§5.1.1.15.2), `RRC.ConnMean`, `RRC.ConnMax`, `PAG.ReceivedNbrCnInitiated`, `PAG.ReceivedNbrRanIntiated`, `PAG.DiscardedNbr`, `RACH.PreambleACell`, `RACH.PreambleBCell`, `UECNTX.ConnEstabAtt.Cause`. Full citations: [`docs/scenarios/G-signalling-storm.md`](docs/scenarios/G-signalling-storm.md).

**Operational significance.** Signalling storms are an active operational concern at scale, causing cascading core‑network impact (AMF/SMF congestion). Detection latency determines whether the storm is contained at the affected cells or propagates network‑wide.

---

### H — Handover‑target resource saturation

**Operational regime.** Per‑handover decisions need to predict the *target gNB's* virtual + radio resource state to avoid HO rejection. Cloud‑RAN auto‑scaling, restarts, and sibling‑tenant load make week‑old PRB / vCPU baselines unreliable. This is the canonical fast‑loop case.

**Reference specifications.**
- *3GPP TS 28.104 §7.2.5.2 / §8.4.5.2* — *Handover optimization analysis (UE‑load‑based)*. Outputs: "current and predicted virtual & radio resource consumption of gNB; selection priority for target cell; cells to **avoid** for an indicated time period."

**Synthetic generation.** Cluster of cells with shared O‑Cloud infrastructure. Inject: (1) sibling‑tenant surge — neighbouring cell's load consumes shared vCPU pool; (2) O‑Cloud auto‑scale event — target cell's vCPU allocation halves for 2–5 min during scaling; (3) restart — target cell briefly unavailable, then load‑imbalanced as it ramps. Ground‑truth labels record per‑event timestamps, affected cell set, resource state during event.

**KPIs emitted.** `RRU.PrbTotDl`, `RRU.PrbTotUl` (TS 28.552 §5.1.1.2) — target‑cell physical PRB utilisation; `VirtualResUtilizaiton` (TS 28.554 §6.4.2) — virtualised resource utilisation (CPU, memory, disk); `DRB.PdcpSduVolumeDL_Filter` (§5.1.2.1) — data volume on target cell; MDT RSRP / RSRQ / SINR (per O‑RAN UC). Full citations: [`docs/scenarios/H-handover-target-saturation.md`](docs/scenarios/H-handover-target-saturation.md).

**Operational significance.** Handover decisions are the highest‑frequency control loop in RAN. Wrong target selection causes drops, ping‑pongs, and SLA violations. The canonical "fast‑loop" forecast where streaming is structurally appropriate and batch is not.

---

## How it works

Each scenario constructs its dataset in two phases:

- **Baseline phase** — produces unperturbed per‑(cell, KPI) time series with realistic diurnal + weekly seasonality, per‑cell heterogeneity, and KPI‑specific clipping/integer rounding.
- **Event‑injection phase** — scenario‑specific helpers mutate KPI series over labelled time intervals and write a parallel `*.events.parquet` ground‑truth sidecar (`event_type`, `start_step`, `end_step`, scenario‑specific metadata).

Output per scenario:

```
scenario_X.parquet           # per‑(cell, KPI, t) telemetry
scenario_X.events.parquet    # labelled event ground‑truth sidecar
scenario_X.manifest.json     # scenario, seed, ranfst version, n_cells, duration_days, n_steps, KPIs
```

KPI configurations use 3GPP TS 28.552 §5.1.1 names verbatim (e.g. `RRU.PrbTotDl`, `MM.HoExeInterReq`, `PEE.AvgPower`). Each KPI declares `base`, `noise_pct`, `envelope_influence`, `clip_min`/`clip_max`, and integer constraint inline next to the cited spec paragraph that motivates it.

Full methodology: [`docs/methodology.md`](docs/methodology.md). KPI catalogue: [`docs/kpi-catalogue.md`](docs/kpi-catalogue.md).

---

## Reproducibility lock

- Every dataset ships with a `*.manifest.json` capturing `(scenario, seed, ranfst version, n_cells, duration_days, n_steps, n_events, KPIs)`.
- Generator versioning follows SemVer: any change altering byte‑level output for a given seed increments the version. The runner refuses silent version drift.
- Each scenario instance holds a single `numpy.random.Generator` derived from the integer seed. All randomness used during generation flows from that generator.

---

## Quick start

```bash
pip install ranfst

# Discover what's available
ranfst list-scenarios

# Read a scenario's description (with citations)
ranfst describe --scenario A

# Generate one scenario's dataset
ranfst generate --scenario A --seed 42 --output ./data/scenario_A.parquet

# Generate every scenario at one seed
for s in S A B C D E F G H; do
    ranfst generate --scenario $s --seed 42 \
        --output ./data/scenario_$s.parquet \
        --n-cells 12 --duration-days 35
done
```

From source:

```bash
git clone https://github.com/thngbk/ran-synthetic-data.git
cd ran-synthetic-data
pip install -e ".[dev]"
pytest
```

---

## Citation

If you use this generator or a dataset produced from it, please cite via [`CITATION.cff`](CITATION.cff).

---

## Author

Roman Ferrando, Thingbook.

---

## Licence

Apache‑2.0 (see [LICENSE](LICENSE)).
