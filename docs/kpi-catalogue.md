# KPI catalogue

The synthetic series superset emitted by the generator. Every name is verbatim from 3GPP TS 28.552 (Performance Measurements) or TS 28.554 (KPIs). Citations are at section granularity.

## Conventions

- **Aggregation:** `CC` = Cumulative Counter, `SI` = Status Inspection (gauge/sample), `DER(n=1)` = Discrete Event Registration, `GAUGE` = momentary gauge.
- **Per‑object scope:** the IOC class on which the counter / KPI is observed.
- **Granularity:** typical aggregation period. Generator emits 5‑min slow‑loop and 1‑sec fast‑loop variants where applicable.
- **`.SNSSAI` / `.5QI` qualifiers:** counters with these suffixes fan out per slice / QoS class. Continuous‑flow 5QI set per TS 28.554 §6.5.2.2 is `{1, 2, 65, 66}`. Standard 5QI integers per TS 23.501.

## Radio resource utilisation

| Counter | Source | Object | Unit | Pattern |
|---|---|---|---|---|
| `RRU.PrbTotDl` | TS 28.552 §5.1.1.2.1 | NRCellDU | % | Strong diurnal; spiky at peaks |
| `RRU.PrbTotUl` | TS 28.552 §5.1.1.2.2 | NRCellDU | % | Diurnal; smoother than DL |
| `RRU.PrbTotDlDist.BinX` | TS 28.552 §5.1.1.2.3 | NRCellDU | histogram | DL PRB usage distribution |
| `RRU.PrbTotUlDist.BinX` | TS 28.552 §5.1.1.2.4 | NRCellDU | histogram | UL PRB usage distribution |
| `RRU.PrbUsedDl.SNSSAI` | TS 28.552 §5.1.1.2.5 | NRCellDU + S‑NSSAI | count | Slice‑driven |
| `RRU.PrbAvailDl` | TS 28.552 §5.1.1.2.6 | NRCellDU | count | Static per cell config |
| `RRU.PrbUsedUl.SNSSAI` | TS 28.552 §5.1.1.2.7 | NRCellDU + S‑NSSAI | count | Slice‑driven |
| `RRU.PrbAvailUl` | TS 28.552 §5.1.1.2.8 | NRCellDU | count | Static per cell config |
| `RRC.ConnMean` | TS 28.552 §5.1.1.4.1 | NRCellCU | count | Diurnal; correlated with PrbTot |
| `RRC.ConnMax` | TS 28.552 §5.1.1.4.2 | NRCellCU | count | Burst peaks |
| `RRC.InactiveConnMean` | TS 28.552 §5.1.1.4.3 | NRCellCU | count | Slowly varying |
| `RRC.InactiveConnMax` | TS 28.552 §5.1.1.4.4 | NRCellCU | count | Spiky |
| `RRC.ConnEstabAtt.Cause` | TS 28.552 §5.1.1.15.1 | NRCellCU | count | Bursty by cause |
| `RRC.ConnEstabSucc.Cause` | TS 28.552 §5.1.1.15.2 | NRCellCU | count | ~95–99% of attempts |
| `RACH.PreambleACell` | TS 28.552 §5.1.1.20.1 | NRCellDU | count/s | Diurnal; arrival‑driven |
| `RACH.PreambleBCell` | TS 28.552 §5.1.1.20.1 | NRCellDU | count/s | Diurnal |
| `DRB.MeanActiveUeDl` | TS 28.552 §5.1.1.23.1 | NRCellDU | count | Diurnal |
| `DRB.MaxActiveUeDl` | TS 28.552 §5.1.1.23.2 | NRCellDU | count | Spiky |

## Mobility / handover

| Counter | Source | Object | Pattern |
|---|---|---|---|
| `MM.HoExeInterReq` | TS 28.552 §5.1.1.6.1.7 | NRCellCU | Mobility‑flow driven |
| `MM.HoExeInterSucc` | TS 28.552 §5.1.1.6.1.8 | NRCellCU | 95–99.9% of Req |
| `MM.HoExeInterFail.cause` | TS 28.552 §5.1.1.6.1.9 | NRCellCU + cause | Anomaly target |
| `MM.HoExeIntraReq` | TS 28.552 §5.1.1.6.2.1 | NRCellCU | ~5–10× inter rate |
| `MM.HoExeIntraSucc` | TS 28.552 §5.1.1.6.2.2 | NRCellCU | Stable ratio |
| `MM.HoPrepInterReq` | TS 28.552 §5.1.1.6.1.1 | NRCellCU | Pairs with Exe |
| `MM.HoExeInterReq.TimeMean.SNSSAI` | TS 28.552 §5.1.1.6.1.10 | NRCellCU + S‑NSSAI | Slice SLA signal |
| `HO.IntraSys.TooEarly` | TS 28.552 §5.1.1.25.1 | NRCellCU | MRO event |
| `HO.IntraSys.TooLate` | TS 28.552 §5.1.1.25.1 | NRCellCU | MRO event |
| `HO.IntraSys.ToWrongCell` | TS 28.552 §5.1.1.25.1 | NRCellCU | MRO event |
| `MR.IntraCellSSBSwitchReq` | TS 28.552 §5.1.1.21.1 | Beam | Beam‑mgmt activity |
| `MR.IntrCellSuccSSBSwitch` | TS 28.552 §5.1.1.21.2 | Beam | Beam‑mgmt activity |

## Throughput and data volume

| Counter | Source | Object | Unit | Pattern |
|---|---|---|---|---|
| `DRB.UEThpDl` (`.QOS`,`.SNSSAI`) | TS 28.552 §5.1.1.3.1 | NRCellDU | kbit/s | Inverse‑correlated with cell load |
| `DRB.UEThpUl` (`.QOS`,`.SNSSAI`) | TS 28.552 §5.1.1.3.3 | NRCellDU | kbit/s | Weaker diurnal |
| `DRB.UEThpDlDist.Bin` | TS 28.552 §5.1.1.3.2 | NRCellDU | histogram | Tail thickens under congestion |
| `DRB.UEUnresVolDl` | TS 28.552 §5.1.1.3.5 | NRCellDU | % | Higher when traffic light |
| `DRB.PdcpSduVolumeDL_Filter` | TS 28.552 §5.1.2.1.1.1 | NRCellCU | Mbit | Diurnal; primary EE input |
| `DRB.PdcpSduVolumeUL_Filter` | TS 28.552 §5.1.2.1.2.1 | NRCellCU | Mbit | Lower than DL |
| `GTP.InDataOctN3UPF.SNSSAI` | TS 28.552 §5.4.1 | EP_N3 + S‑NSSAI | bytes | Drives slice volume |
| `GTP.OutDataOctN3UPF.SNSSAI` | TS 28.552 §5.4.1 | EP_N3 + S‑NSSAI | bytes | Drives slice volume |
| `DRB.AirIfDelayDl` | TS 28.552 §5.1.1.1.1 | NRCellDU | 0.1 ms | Tail under congestion |
| `DRB.AirIfDelayUl` | TS 28.552 §5.1.1.1.3 | NRCellDU | 0.1 ms | Tail under UL load |
| `DRB.RlcDelayUl` | TS 28.552 §5.1.1.1.4 | NRCellDU | 0.1 ms | Pairs with AirIfDelayUl |
| `DRB.PdcpReordDelayUl` | TS 28.552 §5.1.1.1.5 | GNBCUUPFunction | 0.1 ms | Stable except during congestion |
| `DRB.PacketLossRateUl` | TS 28.552 §5.1.3.1.1 | GNBCUUPFunction | PPM | Heavy‑tailed; failure precursor |
| `DRB.F1UpacketLossRateDl` | TS 28.552 §5.1.3.1.3 | NRCellDU | PPM | Transport‑health indicator |
| `DRB.PdcpPacketDropRateDl` | TS 28.552 §5.1.3.2.1 | GNBCUUPFunction | PPM | Rises with overload |

## Quality (CQI / MCS / RSRP / TB)

| Counter | Source | Object | Pattern |
|---|---|---|---|
| `CARR.WBCQIDist.BinX.BinY.BinZ` | TS 28.552 §5.1.1.11.1 | NRCellDU | Shifts left under poor radio |
| `CARR.PDSCHMCSDist.BinX.BinY.BinZ` | TS 28.552 §5.1.1.12.1 | NRCellDU | MCS distribution |
| `CARR.PUSCHMCSDist.BinX.BinY.BinZ` | TS 28.552 §5.1.1.12.2 | NRCellDU | UL MCS distribution |
| `L1M.SS-RSRP.BinX` | TS 28.552 §5.1.1.22.1 | Beam | Coverage / beam‑quality signal |
| `L1M.PHR1.BinX` | TS 28.552 §5.1.1.26.1 | NRCellDU | Power headroom distribution |
| `TB.TotNbrDlInitial` (per modulation) | TS 28.552 §5.1.1.7.1 | NRCellDU | DL initial TBs by modulation |
| `TB.IntialErrNbrDl` (per modulation) | TS 28.552 §5.1.1.7.2 | NRCellDU | Initial‑BLER input |
| `TB.ResidualErrNbrDl` | TS 28.552 §5.1.1.7.5 | NRCellDU | Residual DL TB errors |

## DRB / QoS flow / PDU session

| Counter | Source | Object | Pattern |
|---|---|---|---|
| `DRB.EstabAtt.5QI` (`.SNSSAI`) | TS 28.552 §5.1.1.10.1 | NRCellCU | Bursty |
| `DRB.EstabSucc.5QI` (`.SNSSAI`) | TS 28.552 §5.1.1.10.2 | NRCellCU | ~98–99.9% of attempts |
| `DRB.RelActNbr.5QI` (`.SNSSAI`) | TS 28.552 §5.1.1.10.3 | NRCellCU | Sparse; drives DRBRetain |
| `DRB.SessionTime.5QI` (`.SNSSAI`) | TS 28.552 §5.1.1.10.4 | NRCellCU | Trends with active UE count |
| `QF.RelActNbr.QoS` | TS 28.552 §5.1.1.13.1.1 | NRCellCU | Drives QoSRetain |
| `QF.SessionTimeQoS.QoS` | TS 28.552 §5.1.1.13.2 | NRCellCU | Pairs for retainability |
| `SM.PDUSessionSetupReq.SNSSAI` | TS 28.552 §5.1.1.5.1 | NRCellCU | Slice setup activity |
| `SM.PDUSessionSetupSucc.SNSSAI` | TS 28.552 §5.1.1.5.2 | NRCellCU | Pairs with Req |

## Energy efficiency

| Counter | Source | Object | Unit | Pattern |
|---|---|---|---|---|
| `PEE.AvgPower` | TS 28.552 §5.1.1.19.2.1 | ManagedElement | W | Tracks load; floor at sleep |
| `PEE.MinPower` | TS 28.552 §5.1.1.19.2.2 | ManagedElement | W | Min within period |
| `PEE.MaxPower` | TS 28.552 §5.1.1.19.2.3 | ManagedElement | W | Max within period |
| `PEE.Energy` | TS 28.552 §5.1.1.19.3 | ManagedElement | kWh | Cumulative |
| `PEE.AvgTemperature` | TS 28.552 §5.1.1.19.4.1 | ManagedElement | °C | Lagged correlation with power |
| `PEE.Voltage` | TS 28.552 §5.1.1.19.5 | ManagedElement | V | Slowly varying |
| `PEE.Current` | TS 28.552 §5.1.1.19.6 | ManagedElement | A | Tracks load |
| `CARR.MeanTxPwr` | TS 28.552 §5.1.1.29.2 | NRCellDU | dBm | Drops in sleep modes |
| `CARR.MaxTxPwr` | TS 28.552 §5.1.1.29.1 | NRCellDU | dBm | Static config max |

## Composite KPIs (TS 28.554)

| KPI | Source | Scope | Formula sketch |
|---|---|---|---|
| `DRBAccessibility.5QI` | TS 28.554 §6.2.4 | NRCellCU | RRC × NG signalling × DRB success rates × 100 |
| `RSR_Type` | TS 28.554 §6.2.3 | NetworkSlice | Reg success / reg attempts × 100 |
| `DLLat_gNB-DU` | TS 28.554 §6.3.1.1 | NRCellDU | Mean of `DRB.RlcSduLatencyDl` |
| `DLDelay_NR_SNw` | TS 28.554 §6.3.1.2.1 | SubNetwork | Sum of CU‑UP and DU delays |
| `DlUeThroughput_Cell` | TS 28.554 §6.3.6.3 | NRCellDU | Mean `DRB.UEThpDl` |
| `UTSNSI` / `DTSNSI` | TS 28.554 §6.3.2/3 | NetworkSlice | Throughput at N3 per slice |
| `GRANHOSR` | TS 28.554 §6.6.1 | NRCellCU | Composite HO success rate × 100 |
| `EEMN,DV` | TS 28.554 §6.7.1 | SubNetwork | PDCP volume / `PEE.Energy`, in bit/J |

## Failure cause encodings

Failure subcounters with `.cause` qualifier follow:
- **NGAP causes:** TS 38.413 §9.3.1.2 (radio‑link, transport, NAS, protocol, miscellaneous)
- **XnAP causes:** TS 38.423 (radio‑network, transport, protocol, miscellaneous)

Generator emits failure events with realistic cause distributions per scenario (e.g. radio‑link failures dominate during coverage events; transport failures dominate during fronthaul issues).

## Notes

- All RAN counters can be reported per granularity period (typ. 5 / 15 / 60 min). Sub‑second NR L2 measurements per TS 38.314.
- Counters with `.SNSSAI` / `.5QI` qualifiers expand to per‑slice / per‑QoS series in the dataset.
- KPIs at aggregator level (SubNetwork, NetworkSliceSubnet) are computed by weighted means over constituent cells (weight = DL/UL volume or packet count). The generator emits per‑cell counters; KPIs are reconstructed downstream by `evaluation/`.
