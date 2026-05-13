# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Scenario A — Energy-saving cell sleep transition.

Cells are organised into clusters of 1 Capacity Booster (CB) + 4 Coverage
neighbours. The CB enters sleep at a randomised time within a configurable
nightly window; on entry, its load drops to ~0 and a fraction of that load is
absorbed by the four neighbours. The neighbours' load distribution shifts
step-wise — exactly the regime-change pattern that makes a weekly retrainer
permanently stale and that streaming forecasters can adapt to in minutes.

See ``docs/scenarios/A-energy-saving-sleep.md``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ranfst.scenarios._common import CORE_KPIS, ScenarioBuilder, schedule_events
from ranfst.scenarios.base import Scenario


class EnergySavingSleep(Scenario):
    ID = "A"
    NAME = "Energy-saving cell sleep transition"
    TRIPLY_CITED = True
    DEFAULT_N_CELLS = 50  # 10 clusters of 5 cells
    DEFAULT_DURATION_DAYS = 14.0
    SLEEP_HOUR_RANGE = (22, 26)  # 22:00 - 02:00 next day (in hours)
    SLEEP_DURATION_HOURS = (4.0, 7.0)
    REDISTRIBUTION = (0.6, 0.8)  # fraction of CB load absorbed by neighbours
    POWER_FLOOR = 0.15  # idle CB consumes 15% of awake power

    def generate(self, output: Path) -> None:
        # Round n_cells up to a multiple of 5 (CB + 4 neighbours).
        n_clusters = max(1, self.n_cells // 5)
        adjusted_n_cells = n_clusters * 5

        builder = ScenarioBuilder(
            n_cells=adjusted_n_cells,
            duration_days=self.duration_days,
            rng=self.rng,
            kpis=CORE_KPIS,
        )
        values = builder.generate_baseline()

        steps_per_day = int(round(24 * 60 / builder.period_minutes))
        sleep_lo_step = int(self.SLEEP_HOUR_RANGE[0] * 60 / builder.period_minutes)
        sleep_hi_step = int(self.SLEEP_HOUR_RANGE[1] * 60 / builder.period_minutes)

        for cluster_idx in range(n_clusters):
            cb_id = builder.cell_ids[cluster_idx * 5]
            neighbours = builder.cell_ids[cluster_idx * 5 + 1 : (cluster_idx + 1) * 5]

            # One sleep transition per night.
            n_days = int(self.duration_days)
            for day in range(n_days):
                day_offset = day * steps_per_day
                # Start of sleep, randomised within the configured window.
                onset_in_window = self.rng.integers(
                    sleep_lo_step, sleep_hi_step
                )
                start = day_offset + int(onset_in_window)
                duration_h = float(self.rng.uniform(*self.SLEEP_DURATION_HOURS))
                duration_steps = int(duration_h * 60 / builder.period_minutes)
                end = min(start + duration_steps, builder.n_steps - 1)
                if start >= builder.n_steps - 1:
                    continue

                # Snapshot CB's load for the sleep window before zeroing.
                cb_load_dl_pre = values[f"{cb_id}|RRU.PrbTotDl"][start:end].copy()
                cb_load_ul_pre = values[f"{cb_id}|RRU.PrbTotUl"][start:end].copy()
                cb_conn_pre = values[f"{cb_id}|RRC.ConnMean"][start:end].copy()
                cb_thp_dl_pre = values[f"{cb_id}|DRB.UEThpDl"][start:end].copy()
                cb_thp_ul_pre = values[f"{cb_id}|DRB.UEThpUl"][start:end].copy()
                cb_ho_pre = values[f"{cb_id}|MM.HoExeInterReq"][start:end].copy()
                cb_hosucc_pre = values[f"{cb_id}|MM.HoExeInterSucc"][start:end].copy()

                # Drop CB load to ~0 (small leakage stays for realism).
                leakage = 0.05
                values[f"{cb_id}|RRU.PrbTotDl"][start:end] = cb_load_dl_pre * leakage
                values[f"{cb_id}|RRU.PrbTotUl"][start:end] = cb_load_ul_pre * leakage
                values[f"{cb_id}|RRC.ConnMean"][start:end] = cb_conn_pre * leakage
                values[f"{cb_id}|RRC.ConnMax"][start:end] *= leakage
                values[f"{cb_id}|DRB.UEThpDl"][start:end] *= leakage
                values[f"{cb_id}|DRB.UEThpUl"][start:end] *= leakage
                values[f"{cb_id}|MM.HoExeInterReq"][start:end] = cb_ho_pre * leakage
                values[f"{cb_id}|MM.HoExeInterSucc"][start:end] = cb_hosucc_pre * leakage
                # Power drops to the configured floor (idle drain).
                values[f"{cb_id}|PEE.AvgPower"][start:end] *= self.POWER_FLOOR

                # Each neighbour absorbs an equal share of the redistributed load.
                fraction = float(self.rng.uniform(*self.REDISTRIBUTION)) / len(neighbours)
                for nb in neighbours:
                    values[f"{nb}|RRU.PrbTotDl"][start:end] += cb_load_dl_pre * fraction
                    values[f"{nb}|RRU.PrbTotUl"][start:end] += cb_load_ul_pre * fraction
                    values[f"{nb}|RRC.ConnMean"][start:end] += cb_conn_pre * fraction
                    values[f"{nb}|RRC.ConnMax"][start:end] *= 1.0 + fraction
                    # Throughput per UE drops slightly under the extra load.
                    values[f"{nb}|DRB.UEThpDl"][start:end] *= 1.0 - 0.20 * fraction
                    values[f"{nb}|DRB.UEThpUl"][start:end] *= 1.0 - 0.20 * fraction
                    values[f"{nb}|MM.HoExeInterReq"][start:end] += cb_ho_pre * fraction
                    values[f"{nb}|MM.HoExeInterSucc"][start:end] += cb_hosucc_pre * fraction
                    values[f"{nb}|PEE.AvgPower"][start:end] *= 1.0 + 0.30 * fraction

                builder.record_event(
                    cell_id=cb_id,
                    event_type="cb_sleep_entry",
                    start_step=start,
                    end_step=end - 1,
                    sub_type="sleep_window",
                    redistribution_fraction=float(self.REDISTRIBUTION[0]
                                                   + (self.REDISTRIBUTION[1] - self.REDISTRIBUTION[0]) / 2),
                    affected_neighbours=";".join(neighbours),
                )

        df = builder.to_dataframe(values)
        events_df = builder.events_dataframe()
        self.write_outputs(
            output, df, events_df,
            n_steps=builder.n_steps,
            granularity_minutes=builder.period_minutes,
            n_clusters=n_clusters,
        )
