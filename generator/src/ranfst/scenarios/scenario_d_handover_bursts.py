# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Scenario D — MRO handover anomaly bursts.

Cells along a "mobility corridor" experience event-driven handover bursts —
event egress, train passage — that produce non-stationary regimes in the
handover counters and per-beam SSB switching activity. Daily commute peaks
also exist (recurring pattern), and seasonal lookups should pick those up;
the test is whether forecasters track the *non-recurring* event bursts.

See ``docs/scenarios/D-mro-handover-bursts.md``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ranfst.scenarios._common import (
    CORE_KPIS, HO_TOO_EARLY, HO_TOO_LATE,
    ScenarioBuilder, burst_envelope,
)
from ranfst.scenarios.base import Scenario


class MroHandoverBursts(Scenario):
    ID = "D"
    NAME = "MRO handover anomaly bursts"
    TRIPLY_CITED = True
    DEFAULT_N_CELLS = 30
    DEFAULT_DURATION_DAYS = 14.0
    EVENTS_PER_CELL = 2  # event egress events per cell over the run
    TRAINS_PER_DAY = 4

    def generate(self, output: Path) -> None:
        kpis = CORE_KPIS + (HO_TOO_LATE, HO_TOO_EARLY)
        builder = ScenarioBuilder(
            n_cells=self.n_cells,
            duration_days=self.duration_days,
            rng=self.rng,
            kpis=kpis,
        )
        values = builder.generate_baseline()
        n_steps = builder.n_steps
        period = builder.period_minutes

        # Daily commute peaks already in the diurnal envelope.

        # Event egress bursts (one-off, not seasonal).
        for cell in builder.cell_ids:
            for _ in range(self.EVENTS_PER_CELL):
                margin = 24
                onset = int(self.rng.integers(margin, n_steps - margin))
                width_steps = int(self.rng.integers(4, 9))  # 20-45 min
                peak_factor = float(self.rng.uniform(6.0, 12.0))
                # Apply burst envelope around the onset
                tail_len = n_steps - onset
                burst = burst_envelope(tail_len, peak_at=width_steps,
                                        peak_factor=peak_factor, sigma=width_steps // 2)
                values[f"{cell}|MM.HoExeInterReq"][onset:] *= burst
                values[f"{cell}|MM.HoExeInterSucc"][onset:] *= burst * 0.95
                values[f"{cell}|HO.IntraSys.TooLate"][onset:] += (
                    np.maximum(burst - 1.0, 0.0) * 4.0
                )
                values[f"{cell}|HO.IntraSys.TooEarly"][onset:] += (
                    np.maximum(burst - 1.0, 0.0) * 2.5
                )
                # Active UE counts spike too.
                values[f"{cell}|RRC.ConnMean"][onset:] *= 1.0 + 0.5 * (burst - 1.0)
                end = min(onset + 6 * width_steps, n_steps - 1)
                builder.record_event(
                    cell_id=cell, event_type="ho_burst", sub_type="event_egress",
                    start_step=onset, end_step=end,
                    peak_factor=peak_factor,
                )

        # Train passage: a moving hot-spot crosses a sequence of cells.
        n_days = int(self.duration_days)
        steps_per_day = int(24 * 60 / period)
        # Pick a contiguous sequence of cells to act as the "corridor".
        corridor_len = min(8, self.n_cells)
        corridor = builder.cell_ids[:corridor_len]
        n_trains = int(n_days * self.TRAINS_PER_DAY)
        for _ in range(n_trains):
            day = int(self.rng.integers(0, n_days))
            tod_step = int(self.rng.integers(int(6 * 60 / period), int(22 * 60 / period)))
            base_step = day * steps_per_day + tod_step
            cell_dwell = int(self.rng.integers(2, 5))  # 10-25 minutes per cell
            peak_factor = float(self.rng.uniform(3.0, 6.0))
            for i, cell in enumerate(corridor):
                onset = base_step + i * cell_dwell
                if onset >= n_steps - cell_dwell:
                    break
                end = min(onset + cell_dwell, n_steps - 1)
                burst = burst_envelope(end - onset, peak_at=cell_dwell // 2,
                                        peak_factor=peak_factor, sigma=cell_dwell // 2)
                values[f"{cell}|MM.HoExeInterReq"][onset:end] *= burst
                values[f"{cell}|RRC.ConnMean"][onset:end] *= 1.0 + 0.6 * (burst - 1.0)
                builder.record_event(
                    cell_id=cell, event_type="ho_burst", sub_type="train_passage",
                    start_step=onset, end_step=end - 1,
                    peak_factor=peak_factor,
                )

        df = builder.to_dataframe(values)
        events_df = builder.events_dataframe()
        self.write_outputs(
            output, df, events_df,
            n_steps=n_steps,
            granularity_minutes=period,
        )
