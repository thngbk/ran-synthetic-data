# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Scenario E — Network slice SLA assurance with multi-tenant load mix.

Each cell hosts multiple slices (eMBB diurnal, URLLC flat, mMTC IoT-cyclic).
Three regime-change events: new slice activation, surge on one slice, and
cross-slice contention.

See ``docs/scenarios/E-slice-sla-assurance.md``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ranfst.scenarios._common import KpiConfig, ScenarioBuilder, smooth_step
from ranfst.scenarios.base import Scenario


@dataclass(frozen=True)
class SliceProfile:
    name: str
    base_prb: float
    base_thp: float
    envelope_influence: float


SLICES = (
    SliceProfile("eMBB", base_prb=20.0, base_thp=18_000.0, envelope_influence=1.0),
    SliceProfile("URLLC", base_prb=8.0, base_thp=4_000.0, envelope_influence=0.1),
    SliceProfile("mMTC", base_prb=4.0, base_thp=500.0, envelope_influence=0.4),
)


def _slice_kpis() -> tuple[KpiConfig, ...]:
    cfgs: list[KpiConfig] = []
    for sp in SLICES:
        cfgs.append(KpiConfig(
            f"RRU.PrbUsedDl.{sp.name}", "%", sp.base_prb, 12.0, clip_min=0.0,
            clip_max=100.0, citation="TS 28.552 §5.1.1.2.5",
            envelope_influence=sp.envelope_influence,
        ))
        cfgs.append(KpiConfig(
            f"DRB.UEThpDl.{sp.name}", "kbit/s", sp.base_thp, 12.0, clip_min=0.0,
            citation="TS 28.552 §5.1.1.3.1",
            envelope_influence=sp.envelope_influence,
        ))
        cfgs.append(KpiConfig(
            f"DRB.AirIfDelayDl.{sp.name}", "0.1 ms", 30.0, 25.0, clip_min=0.0,
            citation="TS 28.552 §5.1.1.1.1",
            envelope_influence=0.5,
        ))
    return tuple(cfgs)


SLICE_KPIS: tuple[KpiConfig, ...] = _slice_kpis()


class SliceSlaAssurance(Scenario):
    ID = "E"
    NAME = "Network slice SLA assurance"
    TRIPLY_CITED = True
    DEFAULT_N_CELLS = 30
    DEFAULT_DURATION_DAYS = 14.0

    def generate(self, output: Path) -> None:
        builder = ScenarioBuilder(
            n_cells=self.n_cells,
            duration_days=self.duration_days,
            rng=self.rng,
            kpis=SLICE_KPIS,
        )
        values = builder.generate_baseline()
        n_steps = builder.n_steps

        for cell in builder.cell_ids:
            event_type = str(self.rng.choice(
                ("slice_activation", "embb_surge", "cross_slice_contention")
            ))
            margin = int(0.25 * n_steps)
            onset = int(self.rng.integers(margin, n_steps - margin))
            tail_len = n_steps - onset

            if event_type == "slice_activation":
                # All three slices get a step-up because a fourth slice activated
                # and its UEs spread across the existing tenants' quotas
                # (modelled as a 15-25% step in PRB and inverse step in throughput).
                ramp_steps = 2
                ramp = smooth_step(tail_len, ramp_steps)
                step = float(self.rng.uniform(0.15, 0.25))
                for sp in SLICES:
                    values[f"{cell}|RRU.PrbUsedDl.{sp.name}"][onset:] *= 1.0 + step * ramp
                    values[f"{cell}|DRB.UEThpDl.{sp.name}"][onset:] *= 1.0 - 0.7 * step * ramp
                end = n_steps - 1

            elif event_type == "embb_surge":
                # eMBB load spikes 3x for 30 minutes
                duration_steps = int(self.rng.uniform(4, 9))  # 20-45 min
                end = min(onset + duration_steps, n_steps - 1)
                surge = float(self.rng.uniform(2.5, 3.5))
                window = end - onset
                values[f"{cell}|RRU.PrbUsedDl.eMBB"][onset:end] *= surge
                values[f"{cell}|DRB.UEThpDl.eMBB"][onset:end] *= 1.0 / surge ** 0.5
                # URLLC suffers contention.
                values[f"{cell}|DRB.AirIfDelayDl.URLLC"][onset:end] *= surge

            else:  # cross_slice_contention
                # eMBB consumes URLLC's PRB share; URLLC delay spikes; URLLC throughput drops.
                duration_steps = int(self.rng.uniform(6, 16))
                end = min(onset + duration_steps, n_steps - 1)
                magnitude = float(self.rng.uniform(1.5, 2.5))
                values[f"{cell}|RRU.PrbUsedDl.eMBB"][onset:end] *= magnitude
                values[f"{cell}|RRU.PrbUsedDl.URLLC"][onset:end] *= 0.5
                values[f"{cell}|DRB.AirIfDelayDl.URLLC"][onset:end] *= magnitude * 1.5
                values[f"{cell}|DRB.UEThpDl.URLLC"][onset:end] *= 0.6

            builder.record_event(
                cell_id=cell, event_type="slice_event", sub_type=event_type,
                start_step=int(onset), end_step=int(end),
            )

        df = builder.to_dataframe(values)
        events_df = builder.events_dataframe()
        self.write_outputs(
            output, df, events_df,
            n_steps=n_steps,
            granularity_minutes=builder.period_minutes,
        )
