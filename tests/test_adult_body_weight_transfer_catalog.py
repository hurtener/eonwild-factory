"""Bindings for the unselected adult support-timed body diagnostic."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from eonwild_motion.factory.compiler import load_recipe
from eonwild_motion.planning.grounded_gait import load_grounded_gait
from eonwild_motion.solve.performance import load_performance


ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v3.json"
V4 = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v4.json"
V5 = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v5.json"
V6 = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v6.json"


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


def test_adult_v5_changes_only_restrained_body_response_inputs():
    old, _ = load_recipe(V4, ROOT)
    recipe, _ = load_recipe(V5, ROOT)
    assert recipe["id"] == "heavy-biped.tarbosaurus-pin-552-1-adult-walk.v5"
    assert recipe["version"] == 5
    assert recipe["supersedes"] == old["id"]
    for key in (
        "source",
        "rig",
        "animal",
        "program_profile",
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

    old_performance = read(ROOT / old["performance_profile"]["path"])["parameters"]
    new_performance = read(
        ROOT / recipe["performance_profile"]["path"])["parameters"]
    assert new_performance == {
        **old_performance,
        "pelvis_roll_degrees": 1.5,
        "pelvis_sway_body_heights": .018,
        "upper_trunk_counterroll_degrees": .9,
    }
    performance = load_performance(
        read(ROOT / recipe["performance_profile"]["path"]))
    assert performance.support_directed_pelvis_carrier is True
    assert performance.pelvis_sway_body_heights == .018
    assert performance.pelvis_roll_degrees == 1.5
    assert performance.upper_trunk_counterroll_degrees == .9
    assert performance.pelvis_yaw_degrees == 2
    assert performance.tail_yaw_degrees == 16


def test_adult_v6_changes_only_opt_in_sagittal_body_response_inputs():
    old, _ = load_recipe(V5, ROOT)
    recipe, _ = load_recipe(V6, ROOT)
    assert recipe["id"] == "heavy-biped.tarbosaurus-pin-552-1-adult-walk.v6"
    assert recipe["version"] == 6
    assert recipe["supersedes"] == old["id"]
    for key in (
        "source",
        "rig",
        "animal",
        "program_profile",
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

    old_parameters = read(
        ROOT / old["performance_profile"]["path"])["parameters"]
    new_parameters = read(
        ROOT / recipe["performance_profile"]["path"])["parameters"]
    assert new_parameters == {
        **old_parameters,
        "support_timed_sagittal_carrier": True,
        "pelvis_support_pitch_degrees": 1.2,
        "upper_trunk_counterpitch_degrees": .75,
        "neck_counterpitch_degrees": .45,
        "tail_counterpitch_degrees": 1.5,
    }
    performance = load_performance(
        read(ROOT / recipe["performance_profile"]["path"]))
    assert performance.support_timed_sagittal_carrier is True
    assert performance.pelvis_support_pitch_degrees == 1.2
    assert performance.upper_trunk_counterpitch_degrees == .75
    assert performance.neck_counterpitch_degrees == .45
    assert performance.tail_counterpitch_degrees == 1.5
    assert performance.pelvis_sway_body_heights == .018
    assert performance.pelvis_roll_degrees == 1.5
    assert performance.upper_trunk_counterroll_degrees == .9


def test_adult_body_candidates_are_checked_alongside_v3_in_animal_benchmarks(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tools"))
    spec = importlib.util.spec_from_file_location(
        "verify_catalog", ROOT / "tools/verify_catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.GROUPS["animal-benchmarks"] == [
        "tarbosaurus-pin-552-1-adult-walk.v3",
        "tarbosaurus-pin-552-1-adult-walk.v5",
        "tarbosaurus-pin-552-1-adult-walk.v6",
        "tarbosaurus-pin-552-1-adult-walk.v7",
        "tarbosaurus-pin-552-1-adult-walk.v8",
        "tarbosaurus-pin-552-1-adult-walk.v9",
        "tarbosaurus-pin-552-1-adult-fast-walk-recovery.v3",
    ]
