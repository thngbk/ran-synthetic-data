# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Scenario S — Stationary periodic baseline (control)."""
from __future__ import annotations

from pathlib import Path

from ranfst.scenarios._common import CORE_KPIS, ScenarioBuilder
from ranfst.scenarios.base import Scenario


class StationaryControl(Scenario):
    """Scenario S — stationary periodic baseline.

    Emits the core KPI set with daily + weekly seasonality and Gaussian
    noise. No regime-change events. This is the credibility floor.
    """

    ID = "S"
    NAME = "Stationary periodic baseline (control)"
    TRIPLY_CITED = False
    DEFAULT_N_CELLS = 50
    DEFAULT_DURATION_DAYS = 28.0

    def generate(self, output: Path) -> None:
        builder = ScenarioBuilder(
            n_cells=self.n_cells,
            duration_days=self.duration_days,
            rng=self.rng,
            kpis=CORE_KPIS,
        )
        values = builder.generate_baseline()
        df = builder.to_dataframe(values)
        events_df = builder.events_dataframe()
        self.write_outputs(
            output, df, events_df,
            n_steps=builder.n_steps,
            granularity_minutes=builder.period_minutes,
        )
