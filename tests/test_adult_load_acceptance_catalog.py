"""Bindings for the unselected adult load-acceptance diagnostic."""
from __future__ import annotations

import json
from pathlib import Path
from dataclasses import replace

import numpy as np
import pytest

from eonwild_motion.factory.animal import (
    apply_uniform_geometry_scale, load_animal_instance,
)
from eonwild_motion.factory.compiler import load_recipe
from eonwild_motion.factory.io import digest
from eonwild_motion.factory.source import geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_position
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.grounded_gait import (
    build_grounded_plan, load_grounded_gait,
)
from eonwild_motion.solve.performance import decorate_plan, load_performance
from eonwild_motion.solve.source_motion_query import SourceMotionQuery


ROOT = Path(__file__).resolve().parents[1]
V9_RECIPE = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v9.json"
V10_RECIPE = ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v10.json"
V8_PERFORMANCE = ROOT / "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v8.json"
V9_PERFORMANCE = ROOT / "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v9.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_load_acceptance_profile_adds_only_the_bounded_body_response():
    before, after = load(V8_PERFORMANCE), load(V9_PERFORMANCE)
    additions = {
        "support_timed_load_acceptance_carrier": True,
        "pelvis_load_acceptance_body_heights": .01,
        "upper_trunk_load_acceptance_pitch_degrees": .35,
    }
    assert set(after["parameters"]) - set(before["parameters"]) == set(additions)
    assert {key: after["parameters"][key] for key in additions} == additions
    assert {key: value for key, value in after["parameters"].items()
            if key not in additions} == before["parameters"]
    assert after["reference"]["load_acceptance_carrier"]["scope"].startswith(
        "Pre-limb-solve body response")
    performance = load_performance(after)
    assert performance.support_timed_load_acceptance_carrier is True
    assert performance.pelvis_load_acceptance_body_heights == pytest.approx(.01)
    assert performance.upper_trunk_load_acceptance_pitch_degrees == pytest.approx(.35)


def test_v10_recipe_changes_only_versioned_metadata_and_performance_binding():
    before, after = load(V9_RECIPE), load(V10_RECIPE)
    assert after["id"] == "heavy-biped.tarbosaurus-pin-552-1-adult-walk.v10"
    assert after["version"] == 10
    assert after["supersedes"] == before["id"]
    for key in set(before) - {
        "id", "version", "supersedes", "description", "performance_profile"
    }:
        assert after[key] == before[key]
    assert after["performance_profile"] == {
        "path": "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v9.json",
        "sha256": digest(V9_PERFORMANCE.read_bytes()),
    }


def test_v10_hash_binds_every_declared_input_and_loads_without_selection():
    recipe = load(V10_RECIPE)
    loaded, paths = load_recipe(V10_RECIPE, ROOT)
    assert loaded == recipe
    for key in (
        "source", "rig", "animal", "program_profile", "contact_profile",
        "performance_profile", "articulation_profile",
    ):
        reference = recipe[key]
        assert paths[key] == (ROOT / reference["path"]).resolve()
        assert digest(paths[key].read_bytes()) == reference["sha256"]
    workflow = (ROOT / ".github/workflows/factory-baseline.yml").read_text()
    verifier = (ROOT / "tools/verify_catalog.py").read_text()
    assert "tarbosaurus-pin-552-1-adult-walk.v10" not in workflow
    assert "tarbosaurus-pin-552-1-adult-walk.v10" not in verifier


def test_source_query_consumes_load_acceptance_at_exact_and_off_grid_times():
    recipe = load(V10_RECIPE)
    source = Glb.from_bytes((ROOT / recipe["source"]["path"]).read_bytes())
    animal = load_animal_instance(
        load(ROOT / recipe["animal"]["path"]),
        source_sha256=recipe["source"]["sha256"],
    )
    apply_uniform_geometry_scale(source, animal["uniform_scale"])
    roles = load(ROOT / recipe["rig"]["path"])["roles"]
    gait = replace(
        load_grounded_gait(load(ROOT / recipe["program_profile"]["path"])),
        sample_hz=24,
    )
    height = geometry_height(source, roles, recipe["up_axis"])
    solver = AirborneGait(
        step_period_s=gait.step_period_s,
        cycles=gait.cycles,
        sample_hz=gait.sample_hz,
        swing_hip_lift_degrees=gait.swing_hip_lift_degrees,
    )

    def query(profile: Path):
        performance = replace(load_performance(load(profile)), skin_refinement=False)
        plan = decorate_plan(build_grounded_plan(gait, height), performance)
        return SourceMotionQuery(
            source,
            semantic_roles=roles,
            solver_gait=solver,
            locomotion_gait=gait,
            plan=plan,
            up_axis=tuple(recipe["up_axis"]),
            forward_axis=tuple(recipe["forward_axis"]),
            legacy_overlay=False,
        )

    before, after = query(V8_PERFORMANCE), query(V9_PERFORMANCE)
    double_support = (gait.duty_factor + .5) * gait.step_period_s
    pelvis = source.name_to_node[roles["pelvis"]]
    up = np.asarray(recipe["up_axis"], dtype=float)
    delta = (
        np.asarray(_world_position(after.evaluate(double_support).worlds[pelvis]))
        - np.asarray(_world_position(before.evaluate(double_support).worlds[pelvis]))
    )
    assert delta @ up == pytest.approx(-.01 * height, abs=1e-10)
    assert after.evaluate(double_support + .00013).status == "AVAILABLE"
