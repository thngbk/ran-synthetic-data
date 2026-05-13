# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Scenario C — Mobility load balancing (MLB) regime change.

Operator pushes a configuration change at a labelled timestamp: CIO adjustment,
neighbour maintenance window, or sector split / capacity expansion. Traffic
redistributes across the affected cell set within minutes; the new equilibrium
does not match last week's training data.

See ``docs/scenarios/C-mlb-regime-change.md``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ranfst.scenarios._common import CORE_KPIS, ScenarioBuilder, smooth_step
from ranfst.scenarios.base import Scenario


class MlbRegimeChange(Scenario):
    ID = "C"
    NAME = "MLB regime change"
    TRIPLY_CITED = True
    DEFAULT_N_CELLS = 50  # ten clusters of 5 cells
    DEFAULT_DURATION_DAYS = 14.0
    EVENT_TYPES = ("cio_adjust", "neighbour_maintenance", "sector_split")

    def generate(self, output: Path) -> None:
        n_clusters = max(1, self.n_cells // 5)
        adjusted = n_clusters * 5
        builder = ScenarioBuilder(
            n_cells=adjusted,
            duration_days=self.duration_days,
            rng=self.rng,
            kpis=CORE_KPIS,
        )
        values = builder.generate_baseline()
        n_steps = builder.n_steps

        for cluster_idx in range(n_clusters):
            cells = builder.cell_ids[cluster_idx * 5 : (cluster_idx + 1) * 5]
            event_type = str(self.rng.choice(self.EVENT_TYPES))
            margin = int(0.25 * n_steps)
            onset = int(self.rng.integers(margin, n_steps - margin))
            tail_len = n_steps - onset

            if event_type == "cio_adjust":
                # 15-30% of source's load shifts to target over 1-5 min ramp.
                source, target = cells[0], cells[1]
                ramp_steps = int(self.rng.integers(2, 6))
                fraction = float(self.rng.uniform(0.15, 0.30))
                ramp = smooth_step(tail_len, ramp_steps)
                shift_dl = values[f"{source}|RRU.PrbTotDl"][onset:].copy() * fraction * ramp
                shift_ul = values[f"{source}|RRU.PrbTotUl"][onset:].copy() * fraction * ramp
                shift_conn = values[f"{source}|RRC.ConnMean"][onset:].copy() * fraction * ramp
                shift_ho = values[f"{source}|MM.HoExeInterReq"][onset:].copy() * fraction * ramp
                values[f"{source}|RRU.PrbTotDl"][onset:] -= shift_dl
                values[f"{source}|RRU.PrbTotUl"][onset:] -= shift_ul
                values[f"{source}|RRC.ConnMean"][onset:] -= shift_conn
                values[f"{source}|MM.HoExeInterReq"][onset:] -= shift_ho
                values[f"{target}|RRU.PrbTotDl"][onset:] += shift_dl
                values[f"{target}|RRU.PrbTotUl"][onset:] += shift_ul
                values[f"{target}|RRC.ConnMean"][onset:] += shift_conn
                values[f"{target}|MM.HoExeInterReq"][onset:] += shift_ho
                end = n_steps - 1
                builder.record_event(
                    cell_id=source, event_type="mlb_event", sub_type=event_type,
                    start_step=onset, end_step=end,
                    fraction=float(fraction), other_cells=target,
                )
                builder.record_event(
                    cell_id=target, event_type="mlb_event", sub_type=event_type + "_target",
                    start_step=onset, end_step=end,
                    fraction=float(fraction), other_cells=source,
                )

            elif event_type == "neighbour_maintenance":
                # cells[0] goes offline, full load redistributes to remaining 4.
                offline = cells[0]
                others = cells[1:]
                ramp_steps = int(self.rng.integers(6, 24))  # 30-120 minutes
                duration_steps = int(self.rng.uniform(12, 96))  # 1-8 hours
                end = min(onset + duration_steps, n_steps - 1)
                window_len = end - onset
                ramp = smooth_step(window_len, ramp_steps)
                # Save then transfer.
                pre_dl = values[f"{offline}|RRU.PrbTotDl"][onset:end].copy()
                pre_ul = values[f"{offline}|RRU.PrbTotUl"][onset:end].copy()
                pre_conn = values[f"{offline}|RRC.ConnMean"][onset:end].copy()
                pre_ho = values[f"{offline}|MM.HoExeInterReq"][onset:end].copy()
                values[f"{offline}|RRU.PrbTotDl"][onset:end] *= 1.0 - ramp
                values[f"{offline}|RRU.PrbTotUl"][onset:end] *= 1.0 - ramp
                values[f"{offline}|RRC.ConnMean"][onset:end] *= 1.0 - ramp
                values[f"{offline}|MM.HoExeInterReq"][onset:end] *= 1.0 - ramp
                values[f"{offline}|MM.HoExeInterSucc"][onset:end] *= 1.0 - ramp
                values[f"{offline}|PEE.AvgPower"][onset:end] *= 0.10  # almost off
                share = 1.0 / len(others)
                for nb in others:
                    values[f"{nb}|RRU.PrbTotDl"][onset:end] += pre_dl * ramp * share
                    values[f"{nb}|RRU.PrbTotUl"][onset:end] += pre_ul * ramp * share
                    values[f"{nb}|RRC.ConnMean"][onset:end] += pre_conn * ramp * share
                    values[f"{nb}|MM.HoExeInterReq"][onset:end] += pre_ho * ramp * share
                builder.record_event(
                    cell_id=offline, event_type="mlb_event", sub_type=event_type,
                    start_step=onset, end_step=end,
                    fraction=1.0, other_cells=";".join(others),
                )
                for nb in others:
                    builder.record_event(
                        cell_id=nb, event_type="mlb_event", sub_type=event_type + "_target",
                        start_step=onset, end_step=end,
                        fraction=share, other_cells=offline,
                    )

            else:  # sector_split
                # cells[0]'s load halves over 5-10 min as a new sister cell takes half.
                source = cells[0]
                ramp_steps = int(self.rng.integers(10, 21))
                ramp = smooth_step(tail_len, ramp_steps)
                values[f"{source}|RRU.PrbTotDl"][onset:] *= 1.0 - 0.5 * ramp
                values[f"{source}|RRU.PrbTotUl"][onset:] *= 1.0 - 0.5 * ramp
                values[f"{source}|RRC.ConnMean"][onset:] *= 1.0 - 0.5 * ramp
                values[f"{source}|MM.HoExeInterReq"][onset:] *= 1.0 - 0.5 * ramp
                # The other half goes to a virtual cell — we model this on cells[2]
                # to keep the cluster topology simple.
                target = cells[2]
                source_pre_dl = values[f"{source}|RRU.PrbTotDl"][onset:].copy() / np.maximum(1.0 - 0.5 * ramp, 1e-3)
                values[f"{target}|RRU.PrbTotDl"][onset:] += source_pre_dl * 0.5 * ramp
                end = n_steps - 1
                builder.record_event(
                    cell_id=source, event_type="mlb_event", sub_type=event_type,
                    start_step=onset, end_step=end,
                    fraction=0.5, other_cells=target,
                )

        df = builder.to_dataframe(values)
        events_df = builder.events_dataframe()
        self.write_outputs(
            output, df, events_df,
            n_steps=n_steps,
            granularity_minutes=builder.period_minutes,
            n_clusters=n_clusters,
        )
