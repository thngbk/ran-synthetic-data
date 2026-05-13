# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Scenario G — Signalling storm / abrupt regime change.

A device population (firmware push, mass-event arrival, IoT botnet) launches a
signalling storm — abrupt non-seasonal spike in ``RRC.ConnEstabAtt`` per cell.
The storm has no representation in last week's training data and unfolds over
seconds to minutes.

See ``docs/scenarios/G-signalling-storm.md``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ranfst.scenarios._common import (
    CORE_KPIS, RRC_ESTAB_ATT, RRC_ESTAB_SUCC,
    ScenarioBuilder, burst_envelope,
)
from ranfst.scenarios.base import Scenario


class SignallingStorm(Scenario):
    ID = "G"
    NAME = "Signalling storm"
    TRIPLY_CITED = True
    DEFAULT_N_CELLS = 30
    DEFAULT_DURATION_DAYS = 14.0
    EVENTS_PER_CELL = 2
    EVENT_TYPES = ("iot_botnet", "firmware_push", "mass_event")

    def generate(self, output: Path) -> None:
        kpis = CORE_KPIS + (RRC_ESTAB_ATT, RRC_ESTAB_SUCC)
        builder = ScenarioBuilder(
            n_cells=self.n_cells,
            duration_days=self.duration_days,
            rng=self.rng,
            kpis=kpis,
        )
        values = builder.generate_baseline()
        n_steps = builder.n_steps
        period = builder.period_minutes

        for cell in builder.cell_ids:
            for _ in range(self.EVENTS_PER_CELL):
                ftype = str(self.rng.choice(self.EVENT_TYPES))
                margin = 12
                onset = int(self.rng.integers(margin, n_steps - margin))
                tail_len = n_steps - onset

                if ftype == "iot_botnet":
                    # 10-50x spike for 1-10 minutes.
                    duration_steps = int(self.rng.integers(2, 11))
                    end = min(onset + duration_steps, n_steps - 1)
                    multiplier = float(self.rng.uniform(10.0, 50.0))
                    burst = burst_envelope(
                        end - onset, peak_at=duration_steps // 2,
                        peak_factor=multiplier, sigma=max(1, duration_steps // 3),
                    )
                    values[f"{cell}|RRC.ConnEstabAtt"][onset:end] *= burst
                    # Success rate drops because of overload.
                    values[f"{cell}|RRC.ConnEstabSucc"][onset:end] *= burst * 0.6

                elif ftype == "firmware_push":
                    # Sustained 3-5x for 1-3 hours.
                    duration_steps = int(self.rng.uniform(12, 36))
                    end = min(onset + duration_steps, n_steps - 1)
                    multiplier = float(self.rng.uniform(3.0, 5.0))
                    values[f"{cell}|RRC.ConnEstabAtt"][onset:end] *= multiplier
                    values[f"{cell}|RRC.ConnEstabSucc"][onset:end] *= multiplier * 0.95
                    values[f"{cell}|RRC.ConnMean"][onset:end] *= 1.0 + 0.5 * (multiplier - 1.0)

                else:  # mass_event
                    # 4-8x for 20-40 minutes.
                    duration_steps = int(self.rng.uniform(4, 9))
                    end = min(onset + duration_steps, n_steps - 1)
                    multiplier = float(self.rng.uniform(4.0, 8.0))
                    burst = burst_envelope(
                        end - onset, peak_at=duration_steps // 2,
                        peak_factor=multiplier, sigma=duration_steps // 2,
                    )
                    values[f"{cell}|RRC.ConnEstabAtt"][onset:end] *= burst
                    values[f"{cell}|RRC.ConnEstabSucc"][onset:end] *= burst * 0.85
                    values[f"{cell}|RRC.ConnMean"][onset:end] *= 1.0 + 0.4 * (burst - 1.0)

                builder.record_event(
                    cell_id=cell, event_type="signalling_storm", sub_type=ftype,
                    start_step=onset, end_step=end,
                    multiplier=multiplier,
                )

        df = builder.to_dataframe(values)
        events_df = builder.events_dataframe()
        self.write_outputs(
            output, df, events_df,
            n_steps=n_steps,
            granularity_minutes=period,
        )
