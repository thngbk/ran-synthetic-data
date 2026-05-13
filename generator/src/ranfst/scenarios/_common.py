# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Shared building blocks for scenario generators.

Every scenario uses the same primitives:

  - a timestamp index at slow-loop granularity (5 minutes by default)
  - a diurnal+weekly seasonal envelope to modulate KPI values over time
  - a per-cell scale factor so cells are heterogeneous
  - a list of named 3GPP KPIs (verbatim names from TS 28.552 / TS 28.554)
    each with its baseline magnitude, noise level, and clamping rule

Scenarios A-H additionally inject labelled events on top of this baseline.
The shared :class:`ScenarioBuilder` handles the boilerplate so each scenario
class can focus on event injection.

KPI configurations are defined here once and reused across scenarios.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd

# --------------------------------------------------------------------- KPI configs


@dataclass(frozen=True)
class KpiConfig:
    """One KPI emitter: name, unit, baseline magnitude, noise %, clamp range."""

    name: str
    unit: str
    base: float
    noise_pct: float
    clip_min: float | None = 0.0
    clip_max: float | None = None
    integer: bool = False
    citation: str = ""
    envelope_influence: float = 1.0
    """How strongly the diurnal envelope modulates the baseline.
    1.0 = full daily/weekly cycle (load-correlated KPIs). 0.0 = constant
    baseline (signal-quality KPIs that don't follow traffic)."""
    noise_mode: str = "multiplicative"
    """'multiplicative' = noise std proportional to current signal;
    'absolute' = noise std proportional to baseline (used for dB-scaled
    or temperature-style KPIs whose variability is roughly constant)."""


# Core KPI set used across all scenarios. Each scenario can override or
# extend this list (e.g. Scenario E adds per-slice KPIs, Scenario F adds
# thermal/loss KPIs).
CORE_KPIS: tuple[KpiConfig, ...] = (
    KpiConfig("RRU.PrbTotDl", "%", 40.0, 8.0, clip_min=0.0, clip_max=100.0,
              citation="TS 28.552 §5.1.1.2.1"),
    KpiConfig("RRU.PrbTotUl", "%", 25.0, 8.0, clip_min=0.0, clip_max=100.0,
              citation="TS 28.552 §5.1.1.2.2"),
    KpiConfig("RRC.ConnMean", "count", 300.0, 10.0, clip_min=0.0,
              citation="TS 28.552 §5.1.1.4.1"),
    KpiConfig("RRC.ConnMax", "count", 450.0, 12.0, clip_min=0.0,
              citation="TS 28.552 §5.1.1.4.2"),
    KpiConfig("DRB.UEThpDl", "kbit/s", 25_000.0, 10.0, clip_min=0.0,
              citation="TS 28.552 §5.1.1.3.1"),
    KpiConfig("DRB.UEThpUl", "kbit/s", 8_000.0, 10.0, clip_min=0.0,
              citation="TS 28.552 §5.1.1.3.3"),
    KpiConfig("MM.HoExeInterReq", "count", 120.0, 15.0, clip_min=0.0, integer=True,
              citation="TS 28.552 §5.1.1.6.1.7"),
    KpiConfig("MM.HoExeInterSucc", "count", 118.0, 15.0, clip_min=0.0, integer=True,
              citation="TS 28.552 §5.1.1.6.1.8"),
    KpiConfig("PEE.AvgPower", "W", 1_400.0, 5.0, clip_min=0.0,
              citation="TS 28.552 §5.1.1.19.2.1"),
)


# Extended KPIs used by specific scenarios. RSRP and Temperature use absolute
# noise mode; RSRP has near-zero envelope influence (signal quality is roughly
# fixed unless coverage changes).
RSRP_MEAN = KpiConfig(
    "L1M.SS-RSRP.mean", "dBm", -90.0, 2.0,
    clip_min=-140.0, clip_max=-40.0,
    citation="TS 28.552 §5.1.1.22.1",
    envelope_influence=0.05, noise_mode="absolute",
)
TEMPERATURE = KpiConfig(
    "PEE.AvgTemperature", "°C", 35.0, 4.0,
    clip_min=10.0, clip_max=85.0,
    citation="TS 28.552 §5.1.1.19.4.1",
    envelope_influence=0.3, noise_mode="absolute",
)
PACKET_LOSS_UL = KpiConfig(
    "DRB.PacketLossRateUl", "PPM", 50.0, 25.0, clip_min=0.0,
    citation="TS 28.552 §5.1.3.1.1",
    envelope_influence=0.4,
)
RRC_ESTAB_ATT = KpiConfig(
    "RRC.ConnEstabAtt", "count", 200.0, 12.0, clip_min=0.0, integer=True,
    citation="TS 28.552 §5.1.1.15.1",
)
RRC_ESTAB_SUCC = KpiConfig(
    "RRC.ConnEstabSucc", "count", 195.0, 12.0, clip_min=0.0, integer=True,
    citation="TS 28.552 §5.1.1.15.2",
)
HO_TOO_LATE = KpiConfig(
    "HO.IntraSys.TooLate", "count", 1.0, 80.0, clip_min=0.0, integer=True,
    citation="TS 28.552 §5.1.1.25.1",
    envelope_influence=0.6,
)
HO_TOO_EARLY = KpiConfig(
    "HO.IntraSys.TooEarly", "count", 1.0, 80.0, clip_min=0.0, integer=True,
    citation="TS 28.552 §5.1.1.25.1",
    envelope_influence=0.6,
)
TX_POWER = KpiConfig(
    "CARR.MeanTxPwr", "dBm", 43.0, 1.0,
    clip_min=20.0, clip_max=49.0,
    citation="TS 28.552 §5.1.1.29.2",
    envelope_influence=0.05, noise_mode="absolute",
)


# --------------------------------------------------------------------- envelope


def diurnal_envelope(timestamps: pd.DatetimeIndex) -> np.ndarray:
    """Daily + weekly seasonal envelope applied to all KPIs.

    Mean ~1.0, with a daytime peak around 09:00, a secondary peak at 20:00,
    a trough at 04:00, and a 35% weekend dip. Used to multiply the per-KPI
    baseline so every KPI inherits the same operational rhythm.
    """
    hours = timestamps.hour.to_numpy() + timestamps.minute.to_numpy() / 60.0
    day_of_week = timestamps.dayofweek.to_numpy()
    weekday_factor = np.where(day_of_week < 5, 1.0, 0.65)
    diurnal = (
        0.6
        + 0.30 * np.sin(2 * np.pi * (hours - 9) / 24)
        + 0.15 * np.sin(2 * np.pi * (hours - 20) / 24)
    )
    return diurnal * weekday_factor


def time_index(duration_days: float, period_minutes: int = 5,
               start: str = "2026-01-01T00:00:00Z") -> pd.DatetimeIndex:
    """Build a UTC timestamp index for a scenario run."""
    n_steps = int(round(duration_days * 24 * 60 / period_minutes))
    return pd.date_range(start=start, periods=n_steps, freq=f"{period_minutes}min")


# --------------------------------------------------------------------- builder


@dataclass
class ScenarioBuilder:
    """Convenience helper that wraps the per-cell × per-KPI generation loop.

    A scenario subclass typically:
      1. Constructs a :class:`ScenarioBuilder`.
      2. Calls :meth:`generate_baseline` to get a long-form DataFrame.
      3. Optionally calls :meth:`inject_event` (or scenario-specific helpers)
         to mutate KPI columns over labelled time intervals.
      4. Records each event in ``self.events`` so the output sidecar carries
         ground truth.
    """

    n_cells: int
    duration_days: float
    rng: np.random.Generator
    period_minutes: int = 5
    kpis: tuple[KpiConfig, ...] = CORE_KPIS
    cell_id_format: str = "NRCell-{:04d}"
    timestamps: pd.DatetimeIndex = field(init=False)
    envelope: np.ndarray = field(init=False)
    cell_ids: list[str] = field(init=False)
    cell_scales: dict[str, float] = field(init=False)
    events: list[dict] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.timestamps = time_index(self.duration_days, self.period_minutes)
        self.envelope = diurnal_envelope(self.timestamps)
        self.cell_ids = [self.cell_id_format.format(i) for i in range(self.n_cells)]
        self.cell_scales = {
            cid: float(np.clip(1.0 + self.rng.normal(0.0, 0.15), 0.6, 1.6))
            for cid in self.cell_ids
        }

    @property
    def n_steps(self) -> int:
        return len(self.timestamps)

    # ------------------------------------------------------------ baseline

    def generate_baseline(self) -> dict[str, np.ndarray]:
        """Build the unperturbed per-(cell, KPI) value matrix.

        Returns a dict keyed by ``f"{cell_id}|{kpi_name}"`` to allow scenario
        subclasses to mutate specific (cell, KPI) series in place before
        assembling into a long-form DataFrame.
        """
        out: dict[str, np.ndarray] = {}
        env_mean = float(self.envelope.mean())
        zero_mean_env = self.envelope / env_mean - 1.0
        for cid in self.cell_ids:
            scale = self.cell_scales[cid]
            for kpi in self.kpis:
                modulator = 1.0 + kpi.envelope_influence * zero_mean_env
                signal = kpi.base * scale * modulator
                if kpi.noise_mode == "absolute":
                    noise_std = abs(kpi.base) * (kpi.noise_pct / 100.0)
                    noise = self.rng.normal(0.0, noise_std, size=len(signal))
                else:
                    noise = self.rng.normal(0.0, np.abs(signal) * (kpi.noise_pct / 100.0))
                values = signal + noise
                out[f"{cid}|{kpi.name}"] = values
        return out

    def clip_and_round(self, kpi: KpiConfig, values: np.ndarray) -> np.ndarray:
        """Apply the KPI's clamp and integer-rounding rules."""
        if kpi.clip_min is not None or kpi.clip_max is not None:
            values = np.clip(values, kpi.clip_min, kpi.clip_max)
        if kpi.integer:
            values = np.rint(values)
        return values

    def to_dataframe(self, value_matrix: dict[str, np.ndarray]) -> pd.DataFrame:
        """Assemble the ``{cell|kpi: values}`` matrix into a long-form DataFrame."""
        rows: list[pd.DataFrame] = []
        kpi_names = [k.name for k in self.kpis]
        kpi_by_name = {k.name: k for k in self.kpis}

        for cid in self.cell_ids:
            data: dict[str, np.ndarray] = {}
            for name in kpi_names:
                values = value_matrix[f"{cid}|{name}"]
                data[name] = self.clip_and_round(kpi_by_name[name], values)
            df = pd.DataFrame(data)
            df.insert(0, "timestamp", self.timestamps)
            df.insert(1, "cell_id", cid)
            rows.append(df)
        return pd.concat(rows, ignore_index=True)

    # ------------------------------------------------------------ event log

    def record_event(self, **fields: object) -> None:
        """Append an event row to ``self.events``.

        Each event must include at minimum: cell_id, event_type, start_step,
        end_step. Scenarios add scenario-specific fields (event subtype,
        magnitude, etc.).
        """
        self.events.append(fields)

    def events_dataframe(self) -> pd.DataFrame:
        """Build the events sidecar DataFrame."""
        if not self.events:
            return pd.DataFrame(
                columns=["cell_id", "event_type", "start_step", "end_step",
                         "start_time", "end_time"]
            )
        df = pd.DataFrame(self.events)
        # Add wall-clock timestamps for convenience.
        if "start_step" in df.columns:
            df["start_time"] = self.timestamps[df["start_step"].astype(int)]
        if "end_step" in df.columns:
            ends = df["end_step"].astype(int).clip(upper=self.n_steps - 1)
            df["end_time"] = self.timestamps[ends]
        return df


# --------------------------------------------------------------------- helpers


def schedule_events(
    rng: np.random.Generator,
    n_events: int,
    n_steps: int,
    min_gap: int = 1,
    margin_start: int = 0,
    margin_end: int = 0,
) -> list[int]:
    """Pick ``n_events`` event indices with a minimum gap between them."""
    lo = margin_start
    hi = max(lo + 1, n_steps - margin_end)
    if hi - lo < n_events * min_gap:
        # Fewer events than capacity — just sample uniformly.
        return sorted(int(x) for x in rng.choice(np.arange(lo, hi), size=n_events, replace=False))
    candidates = sorted(int(x) for x in rng.choice(np.arange(lo, hi), size=n_events, replace=False))
    # Greedy gap enforcement.
    out: list[int] = []
    for c in candidates:
        if not out or c - out[-1] >= min_gap:
            out.append(c)
    # If we lost too many to the gap rule, pad by re-sampling.
    while len(out) < n_events:
        c = int(rng.integers(lo, hi))
        if all(abs(c - x) >= min_gap for x in out):
            out.append(c)
    return sorted(out)


def smooth_step(n: int, ramp_steps: int) -> np.ndarray:
    """A piecewise-linear ramp from 0 to 1 over ``ramp_steps`` followed by 1s.

    Used to model gradual transitions (antenna tilt, traffic redistribution).
    """
    out = np.ones(n, dtype=float)
    if ramp_steps > 0:
        ramp = np.linspace(0.0, 1.0, min(ramp_steps, n))
        out[: len(ramp)] = ramp
    return out


def burst_envelope(n: int, peak_at: int, peak_factor: float, sigma: int) -> np.ndarray:
    """A Gaussian-like burst centred at ``peak_at`` with ``peak_factor``.

    Returns a multiplicative envelope (1.0 outside the burst, peaking at
    ``peak_factor``). Used by scenarios D and G for handover and signalling
    bursts.
    """
    x = np.arange(n)
    bell = np.exp(-0.5 * ((x - peak_at) / max(sigma, 1)) ** 2)
    return 1.0 + (peak_factor - 1.0) * bell


__all__ = [
    "CORE_KPIS",
    "KpiConfig",
    "ScenarioBuilder",
    "burst_envelope",
    "diurnal_envelope",
    "schedule_events",
    "smooth_step",
    "time_index",
]
