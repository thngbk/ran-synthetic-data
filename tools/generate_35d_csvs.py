"""Generate 35-day scenario datasets (parquet + CSV) for the v3.0.0 gate validation.

The original v0.0.5-14d-run was 14 days — exactly the warmup the
WeeklySeasonalityGate needs before its first Pearson, so the gate never
actually engaged on those datasets. 35 days gives the gate ~3 full weeks
of post-warmup operation.

Output layout (mirrors v0.0.5-14d-run):
    results/v0.0.5-35d-run/datasets/scenario_<ID>.parquet
    results/v0.0.5-35d-run/csv/scenario_<ID>.csv

CSV is long format (timestamp, cell_id, KPI columns) — same shape that
RAN_TEST.java's FileDataLoader expects.

Reproduce::
    python tools/generate_35d_csvs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GENERATOR_SRC = _REPO_ROOT / "generator" / "src"
if str(_GENERATOR_SRC) not in sys.path:
    sys.path.insert(0, str(_GENERATOR_SRC))

from ranfst.scenarios import REGISTRY  # noqa: E402

SEED = 42
N_CELLS = 50
DURATION_DAYS = 35.0

OUTPUT_ROOT = _REPO_ROOT / "results" / "v0.0.5-35d-run"
PARQUET_DIR = OUTPUT_ROOT / "datasets"
CSV_DIR     = OUTPUT_ROOT / "csv"


def main() -> int:
    PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    CSV_DIR.mkdir(parents=True, exist_ok=True)

    scenarios = sorted(REGISTRY)
    print(f"Generating {len(scenarios)} scenarios at duration_days={DURATION_DAYS}, n_cells={N_CELLS}")
    print(f"  parquet -> {PARQUET_DIR}")
    print(f"  csv     -> {CSV_DIR}")
    print()

    for sid in scenarios:
        cls = REGISTRY[sid]
        parquet_path = PARQUET_DIR / f"scenario_{sid}.parquet"
        csv_path     = CSV_DIR     / f"scenario_{sid}.csv"

        if parquet_path.exists():
            print(f"  [{sid}] parquet exists, reusing: {parquet_path.name}")
        else:
            print(f"  [{sid}] generating ({cls.NAME})...")
            instance = cls(seed=SEED, n_cells=N_CELLS, duration_days=DURATION_DAYS)
            instance.generate(parquet_path)

        df = pd.read_parquet(parquet_path)
        df.to_csv(csv_path, index=False)
        print(f"  [{sid}] csv: {csv_path.name}  (rows={len(df):,}, cells={df['cell_id'].nunique()})")

    print()
    print(f"Done. Point RAN_TEST.java's file list at: {CSV_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
