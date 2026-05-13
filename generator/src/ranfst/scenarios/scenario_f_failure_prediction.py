# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Scenario F — Failure prediction from KPI degradation trends.

Network elements degrade gradually before failing. Pre-failure KPI signatures
are subtle, multivariate, and rare in historical training data — exactly the
case where a model that adapts to the developing signature in real time can
warn earlier than one that waits for the next retrain.

See ``docs/scenarios/F-failure-prediction.md``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ranfst.scenarios._common import (
    CORE_KPIS, PACKET_LOSS_UL, TEMPERATURE, TX_POWER,
    ScenarioBuilder,
)
from ranfst.scenarios.base import Scenario


class FailurePrediction(Scenario):
    ID = "F"
    NAME = "Failure prediction from KPI degradation"
    TRIPLY_CITED = True
    DEFAULT_N_CELLS = 30
    DEFAULT_DURATION_DAYS = 14.0
    FAILURE_FRACTION = 0.5
    FAILURE_TYPES = ("pa_degradation", "fronthaul_jitter", "rrc_instability")

    def generate(self, output: Path) -> None:
        kpis = CORE_KPIS + (TEMPERATURE, PACKET_LOSS_UL, TX_POWER)
        builder = ScenarioBuilder(
            n_cells=self.n_cells,
            duration_days=self.duration_days,
            rng=self.rng,
            kpis=kpis,
        )
        values = builder.generate_baseline()
        n_steps = builder.n_steps
        period = builder.period_minutes
        steps_per_hour = int(60 / period)

        n_failures = max(1, int(self.FAILURE_FRACTION * self.n_cells))
        failure_cells = self.rng.choice(builder.cell_ids, size=n_failures, replace=False)

        for cell in failure_cells:
            ftype = str(self.rng.choice(self.FAILURE_TYPES))
            # Failure happens in the second half of the run so there's a clear
            # pre-failure signature to detect.
            failure_step = int(self.rng.integers(int(0.5 * n_steps), int(0.95 * n_steps)))

            if ftype == "pa_degradation":
                # Temperature trend rises gradually for 12-24 hours then PA goes
                # into thermal protection: TX power capped, throughput drops, BLER up.
                pre_hours = float(self.rng.uniform(12, 24))
                pre_steps = int(pre_hours * steps_per_hour)
                pre_start = max(0, failure_step - pre_steps)
                temp_climb = np.linspace(0, 12.0, pre_steps)
                values[f"{cell}|PEE.AvgTemperature"][pre_start:failure_step] += temp_climb[:failure_step - pre_start]
                # Throughput declines slightly during the pre-failure window.
                thp_decline = np.linspace(0, 0.10, pre_steps)
                values[f"{cell}|DRB.UEThpDl"][pre_start:failure_step] *= 1.0 - thp_decline[:failure_step - pre_start]
                # After failure: TX power capped, throughput halves.
                values[f"{cell}|PEE.AvgTemperature"][failure_step:] += 15.0
                values[f"{cell}|CARR.MeanTxPwr"][failure_step:] -= 6.0
                values[f"{cell}|DRB.UEThpDl"][failure_step:] *= 0.5
                values[f"{cell}|DRB.UEThpUl"][failure_step:] *= 0.5
                pre_window_start = pre_start

            elif ftype == "fronthaul_jitter":
                # Packet loss climbs from baseline to 5000 PPM over 30-60 min before failure.
                pre_minutes = float(self.rng.uniform(30, 60))
                pre_steps = int(pre_minutes / period)
                pre_start = max(0, failure_step - pre_steps)
                loss_climb = np.linspace(0, 5000.0, pre_steps)
                values[f"{cell}|DRB.PacketLossRateUl"][pre_start:failure_step] += loss_climb[:failure_step - pre_start]
                # During failure: total link drop, throughput collapses.
                values[f"{cell}|DRB.PacketLossRateUl"][failure_step:] += 8000.0
                values[f"{cell}|DRB.UEThpUl"][failure_step:] *= 0.05
                values[f"{cell}|DRB.UEThpDl"][failure_step:] *= 0.20
                pre_window_start = pre_start

            else:  # rrc_instability
                # RRC.ConnMax rises 5x over 10 minutes preceding mass disconnect.
                pre_minutes = 10.0
                pre_steps = max(2, int(pre_minutes / period))
                pre_start = max(0, failure_step - pre_steps)
                ramp = np.linspace(1.0, 5.0, pre_steps)
                values[f"{cell}|RRC.ConnMax"][pre_start:failure_step] *= ramp[:failure_step - pre_start]
                # During failure: RRC connections collapse.
                values[f"{cell}|RRC.ConnMean"][failure_step:] *= 0.10
                values[f"{cell}|RRC.ConnMax"][failure_step:] *= 0.10
                values[f"{cell}|MM.HoExeInterReq"][failure_step:] *= 0.10
                pre_window_start = pre_start

            builder.record_event(
                cell_id=cell, event_type="pre_failure",
                sub_type=ftype,
                start_step=int(pre_window_start),
                end_step=int(failure_step - 1),
            )
            builder.record_event(
                cell_id=cell, event_type="failure",
                sub_type=ftype,
                start_step=int(failure_step),
                end_step=n_steps - 1,
            )

        df = builder.to_dataframe(values)
        events_df = builder.events_dataframe()
        self.write_outputs(
            output, df, events_df,
            n_steps=n_steps,
            granularity_minutes=period,
        )
