# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Event injection primitives.

Shared building blocks for the regime-change events that scenarios A through H
inject into their baseline series:

  - ``sleep.py`` — cell sleep / wake transitions (Scenario A)
  - ``coverage.py`` — antenna tilt, mast outage, slow drift (Scenario B)
  - ``mlb.py`` — CIO adjustments, maintenance windows (Scenario C)
  - ``mobility.py`` — commute peaks, event egress, train passage (Scenario D)
  - ``slice.py`` — slice activation, surge, contention (Scenario E)
  - ``failure.py`` — PA degradation, fronthaul jitter, RRC instability (Scenario F)
  - ``storm.py`` — IoT botnet, firmware push, mass arrival (Scenario G)
  - ``saturation.py`` — sibling surge, auto-scale, restart (Scenario H)

Detailed implementation lands as each scenario is added.
"""
