# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Roman Ferrando / Thingbook

"""Scenario registry.

Each scenario is a subclass of :class:`Scenario` registered in :data:`REGISTRY`.
Adding a new scenario is purely additive: write the class in a new module under
``ranfst.scenarios`` and import it here.
"""
from __future__ import annotations

from ranfst.scenarios.base import Scenario
from ranfst.scenarios.scenario_a_energy_sleep import EnergySavingSleep
from ranfst.scenarios.scenario_b_coverage_onset import CoverageProblemOnset
from ranfst.scenarios.scenario_c_mlb import MlbRegimeChange
from ranfst.scenarios.scenario_d_handover_bursts import MroHandoverBursts
from ranfst.scenarios.scenario_e_slice_sla import SliceSlaAssurance
from ranfst.scenarios.scenario_f_failure_prediction import FailurePrediction
from ranfst.scenarios.scenario_g_signalling_storm import SignallingStorm
from ranfst.scenarios.scenario_h_handover_saturation import HandoverTargetSaturation
from ranfst.scenarios.scenario_s_stationary import StationaryControl

REGISTRY: dict[str, type[Scenario]] = {
    "S": StationaryControl,
    "A": EnergySavingSleep,
    "B": CoverageProblemOnset,
    "C": MlbRegimeChange,
    "D": MroHandoverBursts,
    "E": SliceSlaAssurance,
    "F": FailurePrediction,
    "G": SignallingStorm,
    "H": HandoverTargetSaturation,
}

__all__ = ["REGISTRY", "Scenario"]
