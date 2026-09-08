"""Bindings for the unselected adult support-timed body diagnostic."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from eonwild_motion.factory.compiler import load_recipe
from eonwild_motion.planning.grounded_gait import load_grounded_gait
from eonwild_motion.solve.performance import load_performance


ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v3.json"
V4 = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v4.json"


def read(path):
    return json.loads(path.read_text())


def test_adult_v4_changes_only_opt_in_body_coordination_inputs():
    old = read(V3)
    recipe, _ = load_recipe(V4, ROOT)
    assert recipe["id"] == "heavy-biped.tarbosaurus-pin-552-1-adult-walk.v4"
    assert recipe["version"] == 4
    assert recipe["supersedes"] == old["id"]
    for key in (
        "source",
        "rig",
        "animal",
        "contact_profile",
        "articulation_profile",
        "forward_axis",
        "up_axis",
    ):
        assert recipe[key] == old[key]
    for binding in recipe.values():
        if isinstance(binding, dict) and {"path", "sha256"} <= set(binding):
            actual = hashlib.sha256((ROOT / binding["path"]).read_bytes()).hexdigest()
            assert actual == binding["sha256"]

    old_gait = read(ROOT / old["program_profile"]["path"])["parameters"]
    new_gait = read(ROOT / recipe["program_profile"]["path"])["parameters"]
    assert new_gait == {**old_gait, "pelvis_height_carrier": "stance_vault_proxy"}
    gait = load_grounded_gait(read(ROOT / recipe["program_profile"]["path"]))
    assert gait.pelvis_height_carrier == "stance_vault_proxy"
    assert gait.cycles == 1

    old_performance = read(ROOT / old["performance_profile"]["path"])["parameters"]
    new_performance = read(ROOT / recipe["performance_profile"]["path"])["parameters"]
    assert new_performance == {
        **old_performance,
        "support_directed_pelvis_carrier": True,
    }
    performance = load_performance(
        read(ROOT / recipe["performance_profile"]["path"]))
    assert performance.support_directed_pelvis_carrier is True
    assert performance.pelvis_sway_body_heights == .006
    assert performance.pelvis_roll_degrees == .6
    assert performance.pelvis_yaw_degrees == 2
    assert performance.tail_yaw_degrees == 16
