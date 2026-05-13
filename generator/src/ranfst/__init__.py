# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""ranfst — RAN synthetic telemetry generator.

Emits per-(cell, KPI) synthetic time series for the benchmark scenarios
documented under ``docs/scenarios/``. Every dataset is byte-identical
reproducible from a ``(scenario, seed, ranfst version)`` triple.
"""

__version__ = "0.0.5"

__all__ = ["__version__"]
