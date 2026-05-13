# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""KPI emitter modules.

The kpis package contains shared building blocks used by scenarios to emit
named 3GPP KPIs and PM counters with realistic statistical properties.

Each emitter module covers one of the categories from the catalogue under
``docs/kpi-catalogue.md``:

  - ``radio.py`` — radio quality (RSRP, CQI, MCS, BLER)
  - ``load.py`` — traffic load (PRB, RRC, active UEs)
  - ``throughput.py`` — throughput and data volume (DRB, PDCP, GTP)
  - ``mobility.py`` — handover counts and MRO event counters
  - ``slice_qos.py`` — slice and QoS-flow counters
  - ``energy.py`` — PEE.* counters and transmit power
  - ``signalling.py`` — RRC establishments, paging, RACH preambles

Detailed implementation lands in v0.0.2 alongside Scenarios A and B.
"""
