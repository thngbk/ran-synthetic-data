# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Tests covering all 9 scenarios end-to-end.

Each scenario is exercised with a small (n_cells, duration) configuration to
keep the suite fast. The tests verify:

  - the scenario is registered under its expected ID
  - generation produces a non-empty Parquet + manifest + events sidecar
  - reproducibility (same seed → byte-identical output)
  - basic shape and KPI naming sanity
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from ranfst.scenarios import REGISTRY


SMALL_KWARGS = dict(n_cells=5, duration_days=1.5)


@pytest.mark.parametrize("sid", sorted(REGISTRY))
def test_scenario_generates(sid: str, tmp_path: Path) -> None:
    cls = REGISTRY[sid]
    out = tmp_path / f"{sid}.parquet"
    instance = cls(seed=42, **SMALL_KWARGS)
    instance.generate(out)

    assert out.exists(), f"{sid}: parquet not written"
    manifest_path = out.with_suffix(".manifest.json")
    events_path = out.with_suffix(".events.parquet")
    assert manifest_path.exists(), f"{sid}: manifest missing"
    assert events_path.exists(), f"{sid}: events sidecar missing"

    manifest = json.loads(manifest_path.read_text())
    assert manifest["scenario_id"] == sid
    assert manifest["seed"] == 42
    assert manifest["n_steps"] > 0

    df = pd.read_parquet(out)
    assert len(df) > 0
    assert {"timestamp", "cell_id"}.issubset(df.columns)
    # KPI columns should follow 3GPP-style naming (contain a dot).
    kpi_cols = [c for c in df.columns if c not in ("timestamp", "cell_id")]
    assert kpi_cols, f"{sid}: no KPI columns"
    for c in kpi_cols:
        assert "." in c, f"{sid}: KPI column {c!r} doesn't look 3GPP-named"

    # Events sidecar: scenario S has 0 events, others should have at least 1.
    events = pd.read_parquet(events_path)
    if sid == "S":
        assert len(events) == 0
    else:
        assert len(events) > 0, f"{sid}: expected at least one event"
        assert {"cell_id", "event_type", "start_step", "end_step"}.issubset(events.columns)


@pytest.mark.parametrize("sid", ["S", "A", "B", "F", "G"])
def test_scenario_reproducible(sid: str, tmp_path: Path) -> None:
    """Same seed produces byte-identical parquet output."""
    cls = REGISTRY[sid]
    out_a = tmp_path / "a.parquet"
    out_b = tmp_path / "b.parquet"
    cls(seed=7, **SMALL_KWARGS).generate(out_a)
    cls(seed=7, **SMALL_KWARGS).generate(out_b)
    pd.testing.assert_frame_equal(pd.read_parquet(out_a), pd.read_parquet(out_b))


def test_scenario_seeds_diverge(tmp_path: Path) -> None:
    """Different seeds produce different output for at least one scenario."""
    cls = REGISTRY["A"]
    out_a = tmp_path / "a.parquet"
    out_b = tmp_path / "b.parquet"
    cls(seed=1, **SMALL_KWARGS).generate(out_a)
    cls(seed=2, **SMALL_KWARGS).generate(out_b)
    df_a = pd.read_parquet(out_a)
    df_b = pd.read_parquet(out_b)
    assert df_a.shape == df_b.shape
    # KPI values must differ somewhere.
    assert not (df_a.drop(columns=["timestamp", "cell_id"]).values
                == df_b.drop(columns=["timestamp", "cell_id"]).values).all()


def test_scenario_a_sleep_drops_power(tmp_path: Path) -> None:
    """During CB-sleep events, PEE.AvgPower drops below pre-event baseline."""
    out = tmp_path / "A.parquet"
    REGISTRY["A"](seed=42, n_cells=10, duration_days=2.0).generate(out)
    df = pd.read_parquet(out)
    events = pd.read_parquet(out.with_suffix(".events.parquet"))
    sleep_events = events[events["event_type"] == "cb_sleep_entry"]
    assert len(sleep_events) > 0

    # For at least one event, mean power during the window should be much
    # lower than overall mean.
    seen_drop = False
    for _, ev in sleep_events.iterrows():
        cell_df = df[df.cell_id == ev["cell_id"]]
        cell_power = cell_df["PEE.AvgPower"].to_numpy()
        win = cell_power[int(ev["start_step"]) : int(ev["end_step"]) + 1]
        if len(win) and win.mean() < 0.5 * cell_power.mean():
            seen_drop = True
            break
    assert seen_drop, "Expected a PEE.AvgPower drop during a sleep window"


def test_scenario_g_storm_spikes_estab(tmp_path: Path) -> None:
    """Signalling storm events spike RRC.ConnEstabAtt above baseline."""
    out = tmp_path / "G.parquet"
    REGISTRY["G"](seed=42, n_cells=5, duration_days=2.0).generate(out)
    df = pd.read_parquet(out)
    events = pd.read_parquet(out.with_suffix(".events.parquet"))
    assert len(events) > 0
    # For at least one event, the in-window mean exceeds the cell baseline.
    seen_spike = False
    for _, ev in events.iterrows():
        cell_df = df[df.cell_id == ev["cell_id"]]
        s = cell_df["RRC.ConnEstabAtt"].to_numpy()
        if int(ev["start_step"]) >= len(s) or int(ev["end_step"]) >= len(s):
            continue
        win = s[int(ev["start_step"]) : int(ev["end_step"]) + 1]
        baseline_mean = s.mean()
        if len(win) and win.mean() > 1.5 * baseline_mean:
            seen_spike = True
            break
    assert seen_spike
