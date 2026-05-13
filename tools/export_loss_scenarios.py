# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Export the (scenario, KPI) datasets where DriftMind loses in the v0.0.3
preview run, in a CSV format the binaryDM Java validator can consume.

The preview run identifies six loss-pattern targets (see the v0.0.3 README's
"Where DriftMind loses" inventory). Each one corresponds to a regime where
some baseline beats DriftMind on accuracy, recovery, or both:

  * Scenario S, PEE.AvgPower       — smooth periodic (SlotEWMA wins)
  * Scenario S, RRU.PrbTotDl       — long-horizon load (SlotEWMA wins at h=24)
  * Scenario D, MM.HoExeInterReq   — handover bursts (SlotEWMA / FastNPTS)
  * Scenario G, RRC.ConnEstabAtt   — signalling storm (SlotEWMA)
  * Scenario A, DRB.UEThpDl        — recovery on sleep transition
  * Scenario B, DRB.UEThpDl        — recovery on coverage onset
  * Scenario C, DRB.UEThpDl        — recovery on MLB regime change

For each, this script generates the scenario data with `ranfst`, extracts the
named KPI column, pivots to wide format (one column per cell), and writes a
CSV under ``validation-data/loss-scenarios/<SCENARIO>_<KPI>.csv``. The Java
validator (``LossPatternValidator.java``) consumes those CSVs to compare the
BUCKET vs AR_RLS forecaster strategies on the same observation streams that
produced the original losses.

Reproduce::

    python tools/export_loss_scenarios.py

Defaults: seed=42, n_cells=4, duration_days=10. Override via flags.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Allow running directly from the repo root without installing the package.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_GENERATOR_SRC = _REPO_ROOT / "generator" / "src"
if str(_GENERATOR_SRC) not in sys.path:
    sys.path.insert(0, str(_GENERATOR_SRC))

from ranfst.scenarios import REGISTRY  # noqa: E402


@dataclass(frozen=True)
class LossTarget:
    scenario_id: str
    kpi: str
    note: str


LOSS_TARGETS: tuple[LossTarget, ...] = (
    LossTarget("S", "PEE.AvgPower",      "smooth periodic — SlotEWMA wins"),
    LossTarget("S", "RRU.PrbTotDl",      "long-horizon load — SlotEWMA wins at h=24"),
    LossTarget("D", "MM.HoExeInterReq",  "handover bursts — SlotEWMA / FastNPTS win"),
    LossTarget("G", "RRC.ConnEstabAtt",  "signalling storm — SlotEWMA wins"),
    LossTarget("A", "DRB.UEThpDl",       "recovery on energy-saving sleep — SlotEWMA recovers faster"),
    LossTarget("B", "DRB.UEThpDl",       "recovery on coverage onset — SlotEWMA recovers faster"),
    LossTarget("C", "DRB.UEThpDl",       "recovery on MLB regime change — SlotEWMA recovers faster"),
)


def export_one(target: LossTarget, seed: int, n_cells: int, duration_days: float,
               out_dir: Path, scratch_dir: Path) -> Path:
    scenario_cls = REGISTRY[target.scenario_id]
    scenario = scenario_cls(
        seed=seed,
        n_cells=n_cells,
        duration_days=duration_days,
    )
    parquet_path = scratch_dir / f"{target.scenario_id}.parquet"
    scenario.generate(parquet_path)

    df = pd.read_parquet(parquet_path)
    if target.kpi not in df.columns:
        raise KeyError(
            f"Scenario {target.scenario_id} did not emit KPI {target.kpi!r}. "
            f"Available: {sorted(c for c in df.columns if c not in ('timestamp', 'cell_id'))}"
        )

    wide = df.pivot(index="timestamp", columns="cell_id", values=target.kpi)
    wide = wide.sort_index()

    out_path = out_dir / f"{target.scenario_id}_{target.kpi}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(out_path, index=False)
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-cells", type=int, default=4,
                        help="Cells per scenario (default 4 — fast validation)")
    parser.add_argument("--duration-days", type=float, default=10.0,
                        help="Duration in days at 5-min granularity (default 10)")
    parser.add_argument("--output", type=Path,
                        default=_REPO_ROOT / "validation-data" / "loss-scenarios",
                        help="Output directory for CSV files")
    parser.add_argument("--scratch", type=Path,
                        default=_REPO_ROOT / "validation-data" / "_scratch",
                        help="Temporary parquet directory (deleted after run is OK)")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    args.scratch.mkdir(parents=True, exist_ok=True)

    print(f"Exporting {len(LOSS_TARGETS)} loss-scenario CSVs to {args.output}")
    print(f"  seed={args.seed} n_cells={args.n_cells} duration_days={args.duration_days}")
    print()

    rows: list[dict[str, object]] = []
    for target in LOSS_TARGETS:
        print(f"  [{target.scenario_id}] {target.kpi:<28s} ({target.note})")
        out_path = export_one(
            target, seed=args.seed, n_cells=args.n_cells,
            duration_days=args.duration_days,
            out_dir=args.output, scratch_dir=args.scratch,
        )
        df = pd.read_csv(out_path)
        rows.append({
            "scenario": target.scenario_id,
            "kpi": target.kpi,
            "rows": len(df),
            "cells": len(df.columns),
            "csv": out_path.relative_to(_REPO_ROOT).as_posix(),
        })

    print()
    print(pd.DataFrame(rows).to_string(index=False))
    print()
    print(f"Done. Point the Java validator at: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
