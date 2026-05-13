# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Scenario B — Coverage problem onset.

Inject one of three classes of coverage event per cell: an antenna tilt change
(gradual RSRP drop over 10-60 s), a mast outage (abrupt 8-15 dB drop over a
few seconds), or a slow seasonal drift (~0.05 dB/day for many days). RSRP
moves down, CQI distribution shifts left, throughput drops, handover failures
spike — non-seasonal regime change with no representation in last week's
training data.

See ``docs/scenarios/B-coverage-problem-onset.md``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ranfst.scenarios._common import CORE_KPIS, RSRP_MEAN, ScenarioBuilder, smooth_step
from ranfst.scenarios.base import Scenario


class CoverageProblemOnset(Scenario):
    ID = "B"
    NAME = "Coverage problem onset"
    TRIPLY_CITED = True
    DEFAULT_N_CELLS = 50
    DEFAULT_DURATION_DAYS = 14.0
    EVENT_TYPES = ("antenna_tilt", "mast_outage", "slow_drift")
    EVENT_FRACTION = 0.6  # fraction of cells receiving an event

    def generate(self, output: Path) -> None:
        kpis = CORE_KPIS + (RSRP_MEAN,)
        builder = ScenarioBuilder(
            n_cells=self.n_cells,
            duration_days=self.duration_days,
            rng=self.rng,
            kpis=kpis,
        )
        values = builder.generate_baseline()
        n_steps = builder.n_steps

        n_events = max(1, int(self.EVENT_FRACTION * self.n_cells))
        event_cells = self.rng.choice(builder.cell_ids, size=n_events, replace=False)

        for cell in event_cells:
            event_type = str(self.rng.choice(self.EVENT_TYPES))
            # Place event in the middle 60% of the run so there's runway on both
            # sides for evaluation windows.
            margin = int(0.2 * n_steps)
            onset = int(self.rng.integers(margin, n_steps - margin))

            if event_type == "antenna_tilt":
                ramp_steps = int(self.rng.integers(2, 12))  # 10-60 minutes
                magnitude_db = float(self.rng.uniform(2.0, 6.0))
                tail_len = n_steps - onset
                ramp = smooth_step(tail_len, ramp_steps)
                values[f"{cell}|L1M.SS-RSRP.mean"][onset:] -= magnitude_db * ramp
                # Throughput follows RSRP via a soft mapping (~5% per dB lost).
                thp_factor = 1.0 - 0.05 * magnitude_db * ramp
                values[f"{cell}|DRB.UEThpDl"][onset:] *= np.maximum(thp_factor, 0.4)
                values[f"{cell}|DRB.UEThpUl"][onset:] *= np.maximum(thp_factor, 0.4)
                # Handover failures — fewer successes per attempt under poor coverage.
                fail_rate = 0.01 + 0.04 * magnitude_db
                values[f"{cell}|MM.HoExeInterSucc"][onset:] *= 1.0 - fail_rate
                end = n_steps - 1

            elif event_type == "mast_outage":
                ramp_steps = int(self.rng.integers(1, 3))
                magnitude_db = float(self.rng.uniform(8.0, 15.0))
                tail_len = n_steps - onset
                ramp = smooth_step(tail_len, ramp_steps)
                # Persists to end of run unless we add recovery; for simplicity
                # mast_outage events persist (operator hasn't fixed it yet).
                values[f"{cell}|L1M.SS-RSRP.mean"][onset:] -= magnitude_db * ramp
                thp_factor = np.maximum(1.0 - 0.06 * magnitude_db * ramp, 0.10)
                values[f"{cell}|DRB.UEThpDl"][onset:] *= thp_factor
                values[f"{cell}|DRB.UEThpUl"][onset:] *= thp_factor
                # PRB usage actually drops because UEs can't be served.
                values[f"{cell}|RRU.PrbTotDl"][onset:] *= np.maximum(1.0 - 0.04 * magnitude_db * ramp, 0.30)
                values[f"{cell}|RRU.PrbTotUl"][onset:] *= np.maximum(1.0 - 0.04 * magnitude_db * ramp, 0.30)
                values[f"{cell}|MM.HoExeInterSucc"][onset:] *= np.maximum(1.0 - 0.08 * magnitude_db * ramp, 0.50)
                end = n_steps - 1

            else:  # slow_drift
                # 0.04-0.08 dB per day of drift, persistent for the rest of the run.
                drift_per_day = float(self.rng.uniform(0.04, 0.08))
                steps_per_day = int(24 * 60 / builder.period_minutes)
                tail_len = n_steps - onset
                drift = drift_per_day * np.arange(tail_len) / steps_per_day
                values[f"{cell}|L1M.SS-RSRP.mean"][onset:] -= drift
                values[f"{cell}|DRB.UEThpDl"][onset:] *= np.maximum(1.0 - 0.04 * drift, 0.5)
                values[f"{cell}|DRB.UEThpUl"][onset:] *= np.maximum(1.0 - 0.04 * drift, 0.5)
                magnitude_db = float(drift[-1])
                end = n_steps - 1

            builder.record_event(
                cell_id=cell,
                event_type="coverage_event",
                sub_type=event_type,
                start_step=int(onset),
                end_step=int(end),
                magnitude_db=float(magnitude_db),
            )

        df = builder.to_dataframe(values)
        events_df = builder.events_dataframe()
        self.write_outputs(
            output, df, events_df,
            n_steps=n_steps,
            granularity_minutes=builder.period_minutes,
        )
