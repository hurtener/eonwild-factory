"""Bindings and derivation for the bounded adult pelvis-speed diagnostic."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from eonwild_motion.factory.io import digest
from eonwild_motion.solve.performance import load_performance


ROOT = Path(__file__).resolve().parents[1]
V6_RECIPE = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v6.json"
V7_RECIPE = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v7.json"
V5_PERFORMANCE = ROOT / "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v5.json"
V6_PERFORMANCE = ROOT / "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v6.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_v7_binds_only_the_new_versioned_performance_input():
    before, after = load(V6_RECIPE), load(V7_RECIPE)
    assert after["id"] == "heavy-biped.tarbosaurus-pin-552-1-adult-walk.v7"
    assert after["version"] == 7
    assert after["supersedes"] == before["id"]
    for key in ("source", "rig", "animal", "program_profile",
                "contact_profile", "articulation_profile",
                "forward_axis", "up_axis", "program", "family"):
        assert after[key] == before[key]
    reference = after["performance_profile"]
    assert reference["path"] == str(V6_PERFORMANCE.relative_to(ROOT))
    assert reference["sha256"] == digest(V6_PERFORMANCE.read_bytes())


def test_v6_performance_changes_only_the_pelvis_speed_proxy():
    before, after = load(V5_PERFORMANCE), load(V6_PERFORMANCE)
    old_parameters = before["parameters"]
    new_parameters = dict(after["parameters"])
    coefficient = new_parameters.pop(
        "pelvis_forward_velocity_modulation_fraction")
    assert new_parameters == old_parameters
    assert coefficient == pytest.approx(.14519967609352594, abs=1e-16)
    assert load_performance(after).pelvis_forward_velocity_modulation_fraction == coefficient


def test_pelvis_speed_coefficient_replays_recorded_first_order_analogy():
    performance = load(V6_PERFORMANCE)
    derivation = performance["reference"]["carrier_derivation"]
    expected = (derivation["gravitational_acceleration_mps2"]
                * (derivation["pelvis_excursion_m"] / 2)
                / derivation["mean_forward_velocity_mps"] ** 2)
    assert expected == pytest.approx(derivation["result"], abs=1e-16)
    assert derivation["result"] == pytest.approx(
        performance["parameters"][
            "pelvis_forward_velocity_modulation_fraction"], abs=1e-16)
    assert derivation["pelvis_excursion_m"] == pytest.approx(
        derivation["pelvis_excursion_body_heights"]
        * derivation["body_height_m"], abs=1e-16)
    assert derivation["mass_cancels"] is True
    assert math.isfinite(expected) and 0 < expected < 1
