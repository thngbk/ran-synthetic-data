# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Base class for all scenarios.

A scenario produces a synthetic dataset for one of the benchmark cases defined
under ``docs/scenarios/``. Subclasses override :meth:`generate` to emit data
into the supplied output path.

The base class encapsulates the reproducibility lock: every scenario instance
holds a single ``numpy.random.Generator`` derived from the integer seed. All
randomness used during generation must come from that generator. This keeps the
output byte-identical for a given (scenario, seed, ranfst version) triple.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

import numpy as np
import pandas as pd

from ranfst import __version__


@dataclass
class Scenario:
    """Abstract base class for a benchmark scenario.

    Subclasses must define the class attributes ``ID`` and ``NAME``, and
    override :meth:`generate`.
    """

    ID: ClassVar[str] = ""
    NAME: ClassVar[str] = ""
    TRIPLY_CITED: ClassVar[bool] = False
    DEFAULT_N_CELLS: ClassVar[int] = 50
    DEFAULT_DURATION_DAYS: ClassVar[float] = 28.0

    seed: int
    n_cells: int | None = None
    duration_days: float | None = None
    granularity: str = "slow"  # "fast" | "slow" | "both"
    rng: np.random.Generator = field(init=False)

    def __post_init__(self) -> None:
        if self.n_cells is None:
            self.n_cells = self.DEFAULT_N_CELLS
        if self.duration_days is None:
            self.duration_days = self.DEFAULT_DURATION_DAYS
        if self.granularity not in {"fast", "slow", "both"}:
            raise ValueError(
                f"granularity must be 'fast', 'slow', or 'both'; got {self.granularity!r}"
            )
        if self.granularity != "slow":
            raise NotImplementedError(
                "Only slow-loop (5-min) emission is implemented in v0.x. "
                "Fast-loop (1-second) emission is a v0.2.x deliverable."
            )
        self.rng = np.random.default_rng(self.seed)

    # ------------------------------------------------------------------ API

    def generate(self, output: Path) -> None:
        """Emit the dataset to ``output``.

        Subclasses must implement this method. The implementation must:
          1. Use ``self.rng`` exclusively for randomness.
          2. Write the dataset to ``output`` as Parquet.
          3. Write the events sidecar at ``output.with_suffix('.events.parquet')``
             (zero-row DataFrame is fine for Scenario S).
          4. Write the manifest sidecar at ``output.with_suffix('.manifest.json')``
             via :meth:`write_manifest`.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------ I/O helpers

    def write_outputs(
        self,
        output: Path,
        df: pd.DataFrame,
        events_df: pd.DataFrame,
        **manifest_extra: object,
    ) -> None:
        """Common output writer used by all concrete scenarios."""
        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output, engine="pyarrow", index=False)
        events_path = output.with_suffix(".events.parquet")
        events_df.to_parquet(events_path, engine="pyarrow", index=False)
        self.write_manifest(
            output,
            n_rows=len(df),
            n_events=len(events_df),
            kpis_emitted=[c for c in df.columns if c not in ("timestamp", "cell_id")],
            **manifest_extra,
        )

    def manifest(self, **extra: object) -> dict[str, object]:
        return {
            "scenario_id": self.ID,
            "scenario_name": self.NAME,
            "seed": self.seed,
            "ranfst_version": __version__,
            "n_cells": self.n_cells,
            "duration_days": self.duration_days,
            "granularity": self.granularity,
            "generated_at": datetime.now(UTC).isoformat(),
            **extra,
        }

    def write_manifest(self, output: Path, **extra: object) -> Path:
        manifest_path = output.with_suffix(".manifest.json")
        manifest_path.write_text(json.dumps(self.manifest(**extra), indent=2))
        return manifest_path
