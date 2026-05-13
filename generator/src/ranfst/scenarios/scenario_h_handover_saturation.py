# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Scenario H — Handover-target resource saturation.

Cluster of cells sharing O-Cloud infrastructure. Inject sibling-tenant surges,
auto-scale events, and restarts. Per-handover decisions need a forecast of
target-cell PRB at sub-minute granularity; week-old PRB baselines are
unreliable when these events happen.

See ``docs/scenarios/H-handover-target-saturation.md``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ranfst.scenarios._common import CORE_KPIS, ScenarioBuilder
from ranfst.scenarios.base import Scenario


class HandoverTargetSaturation(Scenario):
    ID = "H"
    NAME = "Handover-target resource saturation"
    TRIPLY_CITED = False  # 3GPP-explicit (TS 28.104 §7.2.5.2)
    DEFAULT_N_CELLS = 25
    DEFAULT_DURATION_DAYS = 7.0
    EVENTS_PER_CELL = 4
    EVENT_TYPES = ("sibling_surge", "autoscale", "restart")

    def generate(self, output: Path) -> None:
        builder = ScenarioBuilder(
            n_cells=self.n_cells,
            duration_days=self.duration_days,
            rng=self.rng,
            kpis=CORE_KPIS,
        )
        values = builder.generate_baseline()
        n_steps = builder.n_steps
        period = builder.period_minutes

        for cell in builder.cell_ids:
            for _ in range(self.EVENTS_PER_CELL):
                ftype = str(self.rng.choice(self.EVENT_TYPES))
                margin = 6
                onset = int(self.rng.integers(margin, n_steps - margin))

                if ftype == "sibling_surge":
                    duration_steps = int(self.rng.uniform(6, 18))
                    end = min(onset + duration_steps, n_steps - 1)
                    factor = float(self.rng.uniform(1.4, 2.2))
                    values[f"{cell}|RRU.PrbTotDl"][onset:end] = np.minimum(
                        values[f"{cell}|RRU.PrbTotDl"][onset:end] * factor, 100.0
                    )
                    values[f"{cell}|RRU.PrbTotUl"][onset:end] = np.minimum(
                        values[f"{cell}|RRU.PrbTotUl"][onset:end] * factor, 100.0
                    )

                elif ftype == "autoscale":
                    # vCPU halves for 2-5 minutes -> PRB available halves -> PrbTot
                    # appears to double in percent (same load, half the denominator).
                    duration_steps = int(self.rng.uniform(1, 4))
                    end = min(onset + duration_steps, n_steps - 1)
                    factor = float(self.rng.uniform(1.6, 2.0))
                    values[f"{cell}|RRU.PrbTotDl"][onset:end] = np.minimum(
                        values[f"{cell}|RRU.PrbTotDl"][onset:end] * factor, 100.0
                    )
                    # Throughput is squeezed.
                    values[f"{cell}|DRB.UEThpDl"][onset:end] *= 0.5

                else:  # restart
                    duration_steps = int(self.rng.uniform(1, 5))
                    end = min(onset + duration_steps, n_steps - 1)
                    # Cell briefly unavailable, then bounces back imbalanced.
                    values[f"{cell}|RRU.PrbTotDl"][onset:end] = 0.0
                    values[f"{cell}|RRU.PrbTotUl"][onset:end] = 0.0
                    values[f"{cell}|RRC.ConnMean"][onset:end] = 0.0
                    values[f"{cell}|MM.HoExeInterReq"][onset:end] = 0.0
                    values[f"{cell}|MM.HoExeInterSucc"][onset:end] = 0.0
                    values[f"{cell}|DRB.UEThpDl"][onset:end] = 0.0
                    values[f"{cell}|DRB.UEThpUl"][onset:end] = 0.0
                    # Brief overshoot after restart as queued UEs reattach.
                    rebound_end = min(end + 4, n_steps - 1)
                    values[f"{cell}|RRC.ConnMean"][end:rebound_end] *= 1.4
                    values[f"{cell}|MM.HoExeInterReq"][end:rebound_end] *= 1.6

                builder.record_event(
                    cell_id=cell, event_type="saturation_event", sub_type=ftype,
                    start_step=int(onset), end_step=int(end),
                )

        df = builder.to_dataframe(values)
        events_df = builder.events_dataframe()
        self.write_outputs(
            output, df, events_df,
            n_steps=n_steps,
            granularity_minutes=period,
        )
