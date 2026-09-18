"""Bindings for the unselected adult biomechanical-recovery candidate."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from eonwild_motion.factory.compiler import load_recipe
from eonwild_motion.planning.articulation_profile import (
    ANGLE_CONVENTIONS, CLASSIFICATION, load_articulation_profile,
)
from eonwild_motion.planning.grounded_gait import load_grounded_gait
from eonwild_motion.solve.performance import load_performance


ROOT = Path(__file__).resolve().parents[1]
RECIPE = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v3.json"


def read(path):
    return json.loads((ROOT / path).read_text())


def test_adult_v3_binds_exact_unselected_recovery_inputs():
    recipe, paths = load_recipe(RECIPE, ROOT)
    assert recipe["supersedes"] == "heavy-biped.tarbosaurus-pin-552-1-adult-walk.v2"
    assert recipe["version"] == 3
    for binding in recipe.values():
        if isinstance(binding, dict) and {"path", "sha256"} <= set(binding):
            assert hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest() == binding["sha256"]

    gait = load_grounded_gait(read(recipe["program_profile"]["path"]))
    assert gait.cycles == 1
    assert gait.step_period_s == 1.23
    assert gait.duty_factor == .62
    assert gait.step_length_body_heights == .6
    assert gait.touchdown_reach_body_heights == .25
    assert gait.pelvis_crouch_body_heights == 0
    assert gait.swing_clearance_body_heights == .22
    assert gait.foot_recovery_pitch_degrees == 0
    assert gait.metatarsal_recovery_world_degrees_from_down == -20
    assert gait.metatarsal_recovery_release_fraction == .8
    assert gait.pad_recovery_pitch_degrees == 35
    assert gait.toe_flex_degrees == 25
    assert gait.rounded_swing_peak_fraction == .42
    assert gait.toe_recovery_peak_fraction == .42

    performance = load_performance(read(recipe["performance_profile"]["path"]))
    assert performance.center_lanes_on_bilateral_hip_midpoint is True
    assert performance.skin_refinement is True

    profile_raw = read(recipe["articulation_profile"]["path"])
    profile = load_articulation_profile(profile_raw)
    assert profile.classification == CLASSIFICATION
    assert profile.angle_conventions == ANGLE_CONVENTIONS
    assert profile.evidence["status"] == "comparative_anatomy_informed"
    assert profile.support == profile.swing
    assert profile.swing["hip_sagittal_degrees"].hard_min_deg == -45
    assert profile.swing["hip_sagittal_degrees"].hard_max_deg == 80
    assert profile.swing["knee_interior_degrees"].hard_min_deg == 65
    assert profile.swing["knee_interior_degrees"].hard_max_deg == 180
    assert profile.swing["ankle_interior_degrees"].hard_min_deg == 90
    assert profile.swing["ankle_interior_degrees"].hard_max_deg == 180
    assert any("No measured Tarbosaurus" in item for item in profile.evidence["limitations"])
    assert any("prior unbound diagnostic used a 178 degree" in item
               for item in profile.evidence["limitations"])
