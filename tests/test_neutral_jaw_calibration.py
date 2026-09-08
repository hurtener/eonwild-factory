from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from types import MappingProxyType

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.animal import apply_uniform_geometry_scale, load_animal_instance
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.grounded_gait import build_grounded_plan, load_grounded_gait
from eonwild_motion.planning.jaw_response import load_neutral_jaw_calibration
from eonwild_motion.solve.airborne_gait import solve_airborne_gait
from eonwild_motion.solve.jaw_response import _posed_gap, admit_neutral_jaw
from eonwild_motion.solve.performance import decorate_plan, load_performance
from eonwild_motion.solve.skin_rig import SkinRig
from eonwild_motion.solve.whole_body_gait_transition import _encode


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f"
SOURCE = ROOT / "assets/sha256" / f"{SOURCE_SHA}.glb"
RIG = ROOT / "catalog/rigs/heavy-biped.v9.json"
CONTACT = ROOT / "catalog/contacts/heavy-biped.v10.json"
V6 = ROOT / "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v6.json"
V7 = ROOT / "catalog/performance/heavy-biped.tarbosaurus-adult-walk.v7.json"
PROGRAM = ROOT / "catalog/programs/heavy-biped.tarbosaurus-adult-walk.v4.json"
ANIMAL = ROOT / "catalog/animals/tarbosaurus-bataar-pin-552-1.adult.v2.json"


def document(path: Path) -> dict:
    return json.loads(path.read_text())


def calibration():
    return load_performance(document(V7)).neutral_jaw_calibration


def source_and_roles(*, scaled: bool = False):
    source = Glb.from_bytes(SOURCE.read_bytes())
    roles = document(RIG)["roles"]
    if scaled:
        animal = load_animal_instance(document(ANIMAL), source_sha256=SOURCE_SHA)
        apply_uniform_geometry_scale(source, animal["uniform_scale"])
    return source, roles


def test_profile_is_exactly_source_bound_and_reopens_positive_clearance():
    source, roles = source_and_roles()
    admitted = admit_neutral_jaw(
        source, roles, calibration(), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0))
    assert hashlib.sha256(source.raw).hexdigest() == SOURCE_SHA
    assert admitted.close_degrees == pytest.approx(50.10730272766756, abs=1e-12)
    assert admitted.measured_source_minimum_gap_m == pytest.approx(
        0.0034262633758470606, abs=2e-12)
    assert admitted.current_minimum_gap_m > 0
    assert np.asarray(admitted.local_axis) == pytest.approx([1.0, 0.0, 0.0], abs=2e-7)


def test_v7_performance_adds_only_the_bound_neutral_jaw_calibration():
    before, after = document(V6), document(V7)
    assert set(after["parameters"]) - set(before["parameters"]) == {
        "neutral_jaw_calibration"}
    assert {key: value for key, value in after["parameters"].items()
            if key != "neutral_jaw_calibration"} == before["parameters"]
    assert {key: value for key, value in after["reference"].items()
            if key != "neutral_jaw_calibration"} == before["reference"]
    reference = after["reference"]["neutral_jaw_calibration"]
    assert reference["diagnostic_result_sha256"] == (
        "abd44cbff9a77ffb556764fdb100d58516907fc8314620a515f4e2ba7dee115c")
    assert reference["diagnostic_report_sha256"] == (
        "9d9abfcd7c0b9b10c663b9d952e0e7cbe7e39e011f11cbdec2d1007551171eec")


def test_frozen_mapping_and_sequence_payload_load_and_caller_mutation_isolated():
    raw = document(V7)["parameters"]["neutral_jaw_calibration"]
    frozen = MappingProxyType({
        **raw,
        "joint_accessors": tuple(raw["joint_accessors"]),
        "weight_accessors": tuple(raw["weight_accessors"]),
        "surface_bins": tuple(MappingProxyType({
            key: tuple(value) for key, value in row.items()
        }) for row in raw["surface_bins"]),
    })
    loaded = load_neutral_jaw_calibration(frozen)
    original = loaded.surface_bins[0].lower_vertex_indices
    raw["surface_bins"][0]["lower_vertex_indices"][0] = 999999
    assert loaded.surface_bins[0].lower_vertex_indices == original


@pytest.mark.parametrize("mutation", [
    lambda value: value.update(source_geometry_sha256="0" * 64),
    lambda value: value.update(close_degrees=math.nan),
    lambda value: value.update(clearance_body_heights=0),
    lambda value: value.update(axis_frame="world"),
    lambda value: value.update(joint_accessors=[True, 4, 5]),
    lambda value: value["surface_bins"][0].update(
        upper_vertex_indices=value["surface_bins"][0]["lower_vertex_indices"][:3]),
])
def test_stale_or_malformed_calibration_rejects(mutation):
    value = deepcopy(document(V7)["parameters"]["neutral_jaw_calibration"])
    mutation(value)
    if value["source_geometry_sha256"] == "0" * 64:
        parsed = load_neutral_jaw_calibration(value)
        source, roles = source_and_roles()
        with pytest.raises(ContractError, match="stale"):
            admit_neutral_jaw(source, roles, parsed, (0, 0, 1), (0, 1, 0))
    else:
        with pytest.raises(ContractError):
            load_neutral_jaw_calibration(value)


def test_missing_or_forged_semantic_jaw_binding_rejects():
    source, roles = source_and_roles()
    for changed in (
        {key: value for key, value in roles.items() if key != "jaw_lower"},
        {**roles, "jaw_lower": roles["pelvis"]},
        {**roles, "head": roles["pelvis"]},
    ):
        with pytest.raises(ContractError):
            admit_neutral_jaw(source, changed, calibration(), (0, 0, 1), (0, 1, 0))


def test_renamed_rotated_translated_scaled_source_uses_explicit_admitted_frame():
    source, roles = source_and_roles()
    data = deepcopy(source.document)
    head = source.name_to_node[roles["head"]]
    jaw = source.name_to_node[roles["jaw_lower"]]
    data["nodes"][head]["name"] = "semantic-cranium"
    data["nodes"][jaw]["name"] = "semantic-mandible"
    changed_roles = {**roles, "head": "semantic-cranium", "jaw_lower": "semantic-mandible"}
    scene_root = data["scenes"][data.get("scene", 0)]["nodes"][0]
    angle = math.radians(31)
    data["nodes"][scene_root]["rotation"] = [0.0, math.sin(angle / 2), 0.0, math.cos(angle / 2)]
    data["nodes"][scene_root]["translation"] = [3.0, -2.0, 4.0]
    data["nodes"][scene_root]["scale"] = [1.27, 1.27, 1.27]
    changed = Glb.from_bytes(_encode(data, source.binary))
    forward = (math.sin(angle), 0.0, math.cos(angle))
    old = calibration()
    _, _, measured = _posed_gap(changed, changed_roles, old, forward, (0, 1, 0))
    rebound = replace(
        old,
        source_geometry_sha256=hashlib.sha256(changed.raw).hexdigest(),
        measured_body_height_m=measured / old.clearance_body_heights,
        measured_minimum_gap_m=measured,
    )
    admitted = admit_neutral_jaw(changed, changed_roles, rebound, forward, (0, 1, 0))
    assert admitted.current_minimum_gap_m == pytest.approx(measured, abs=2e-12)
    assert admitted.node == jaw


@lru_cache(maxsize=1)
def _actual_plans_and_solve():
    source, roles = source_and_roles(scaled=True)
    grounded = replace(load_grounded_gait(document(PROGRAM)), sample_hz=24)
    gait = AirborneGait(
        step_period_s=grounded.step_period_s, cycles=grounded.cycles,
        sample_hz=grounded.sample_hz, swing_hip_lift_degrees=grounded.swing_hip_lift_degrees,
    )
    plans = []
    for path in (V6, V7):
        performance = replace(load_performance(document(path)), skin_refinement=False)
        plans.append(decorate_plan(build_grounded_plan(grounded, 2.2841755838983118), performance))
    outputs = [solve_airborne_gait(
        source, source_clip=None, semantic_roles=roles, gait=gait,
        up_axis=(0, 1, 0), forward_axis=(0, 0, 1), plan_override=plan,
        legacy_overlay=False,
    ) for plan in plans]
    return source, roles, gait, outputs


def test_actual_rig_solve_changes_only_jaw_local_rotation_and_keeps_unweighted_skin():
    source, roles, _, outputs = _actual_plans_and_solve()
    glbs = [Glb.from_bytes(value[0]) for value in outputs]
    jaw = source.name_to_node[roles["jaw_lower"]]
    tracks = [_clip_state(glb, glb.document["animations"][0]["name"])[0] for glb in glbs]
    assert tracks[0].keys() == tracks[1].keys()
    changed = []
    for key in tracks[0]:
        equal = np.array_equal(np.asarray(tracks[0][key]), np.asarray(tracks[1][key]))
        if not equal:
            changed.append(key)
    assert changed == [(roles["jaw_lower"], "rotation")]

    contact = document(CONTACT)
    rigs = [SkinRig(glb, roles, [0, 0, 1], [0, 1, 0], contact, oral=True) for glb in glbs]
    poses = [_pose(glb, track, 0) for glb, track in zip(glbs, tracks)]
    points = [rig.skin(np.asarray(_world_matrices(glb, *pose)))
              for glb, rig, pose in zip(glbs, rigs, poses)]
    jaw_descendants = sorted(rigs[0].descendants(jaw))
    jaw_weight = (rigs[0].weights * np.isin(rigs[0].node_ids, jaw_descendants)).sum(axis=1)
    assert np.max(np.linalg.norm(points[1][jaw_weight == 0] - points[0][jaw_weight == 0], axis=1)) == 0
    assert outputs[1][3]["neutral_jaw_calibration"]["admitted_geometry_minimum_gap_m"] > 0


def test_neutral_and_breathing_compose_once_on_actual_rig():
    source, roles, gait, outputs = _actual_plans_and_solve()
    neutral_glb = Glb.from_bytes(outputs[1][0])
    neutral_track, _ = _clip_state(neutral_glb, neutral_glb.document["animations"][0]["name"])
    breathing_gait = replace(gait, jaw_breathing_min_degrees=2.0,
                             jaw_breathing_max_degrees=4.0)
    breathing = solve_airborne_gait(
        source, source_clip=None, semantic_roles=roles, gait=breathing_gait,
        up_axis=(0, 1, 0), forward_axis=(0, 0, 1),
        plan_override=outputs[1][2], legacy_overlay=False)[0]
    breathing_glb = Glb.from_bytes(breathing)
    breathing_track, _ = _clip_state(
        breathing_glb, breathing_glb.document["animations"][0]["name"])
    neutral_q = np.asarray(neutral_track[roles["jaw_lower"], "rotation"][0])
    breathing_q = np.asarray(breathing_track[roles["jaw_lower"], "rotation"][0])
    dot = abs(float(np.dot(neutral_q, breathing_q)
                    / (np.linalg.norm(neutral_q) * np.linalg.norm(breathing_q))))
    assert math.degrees(2 * math.acos(min(1.0, dot))) == pytest.approx(2.0, abs=2e-5)


def test_omitted_and_zero_calibration_preserve_plan_identity():
    base = load_performance(document(V6))
    zero = replace(base, neutral_jaw_calibration=replace(calibration(), close_degrees=0.0))
    plan = build_grounded_plan(replace(load_grounded_gait(document(PROGRAM)), sample_hz=24), 2.0)
    omitted = decorate_plan(plan, base)
    explicit_zero = decorate_plan(plan, zero)
    assert omitted == explicit_zero

    source, roles, gait, _ = _actual_plans_and_solve()
    root, in_place, _, _ = solve_airborne_gait(
        source, source_clip=None, semantic_roles=roles, gait=gait,
        up_axis=(0, 1, 0), forward_axis=(0, 0, 1),
        plan_override=explicit_zero, legacy_overlay=False)
    # The short identity plan above is independent of the production-profile
    # baseline, so compare it to the same omitted plan rather than to V6.
    omitted_outputs = solve_airborne_gait(
        source, source_clip=None, semantic_roles=roles, gait=gait,
        up_axis=(0, 1, 0), forward_axis=(0, 0, 1),
        plan_override=omitted, legacy_overlay=False)
    assert (root, in_place) == omitted_outputs[:2]
