"""Fail-closed tests for optional support/swing articulation guardrails."""
from __future__ import annotations

from copy import deepcopy
import json
import math
import shutil
import struct

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.compiler import compile_recipe, load_recipe, verify_package
from eonwild_motion.factory.quality import emitted_articulation_envelopes
from eonwild_motion.factory.io import bind, digest, write_json
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.grounded_gait import GroundedGait, build_grounded_plan
from eonwild_motion.planning.articulation_profile import (
    ANGLE_CONVENTIONS, CLASSIFICATION, SCHEMA, load_articulation_profile,
)
from eonwild_motion.solve.airborne_gait import solve_airborne_gait
from eonwild_motion.solve.whole_body_gait_transition import _encode
from test_factory import make_recipe
from test_v9_airborne_gait import fixture


def profile_payload() -> dict:
    joint_ranges = {
        "hip_sagittal_degrees": [-90.0, 120.0],
        "knee_interior_degrees": [30.0, 180.0],
        "ankle_interior_degrees": [60.0, 180.0],
    }
    phases = {}
    for phase in ("support", "swing"):
        phases[phase] = {
            joint: {"hard_degrees": limits, "preferred_degrees": limits}
            for joint, limits in joint_ranges.items()
        }
    return {
        "schema": SCHEMA,
        "id": "fixture.engineering-articulation.v1",
        "version": 1,
        "classification": CLASSIFICATION,
        "angle_conventions": dict(ANGLE_CONVENTIONS),
        "evidence": {
            "status": "synthetic_test_only",
            "sources": [{
                "citation": "synthetic fixture",
                "locator": "tests/test_articulation_profile.py",
                "scope": "contract behavior only; no anatomical claim",
            }],
            "limitations": ["scalar sagittal guardrails do not model a 6DoF joint"],
        },
        "envelopes": phases,
    }


def test_profile_reuses_joint_envelopes_and_selects_contact_phase():
    raw = profile_payload()
    raw["envelopes"]["support"]["knee_interior_degrees"] = {
        "hard_degrees": [90, 175], "preferred_degrees": [105, 150],
    }
    profile = load_articulation_profile(raw)
    support = profile.phase(contact=True)["knee_interior_degrees"]
    swing = profile.phase(contact=False)["knee_interior_degrees"]
    assert (support.hard_min_deg, support.preferred_min_deg) == (90, 105)
    assert (support.contraction_per_load_bw, support.contraction_per_speed) == (0, 0)
    assert (swing.hard_min_deg, swing.hard_max_deg) == (30, 180)
    assert profile.receipt()["solver_scope"].startswith("scalar sagittal")
    with pytest.raises(ContractError, match="boolean contact"):
        profile.phase(contact=1)
    # The existing release/approach partition transfers between independently
    # authored phase envelopes without a value, slope, or acceleration corner.
    raw["envelopes"]["swing"]["knee_interior_degrees"] = {
        "hard_degrees": [50, 170], "preferred_degrees": [70, 150]}
    profile = load_articulation_profile(raw)
    def endpoint_curvature(h):
        values = [profile.effective(contact=False, swing_phase=u)["knee_interior_degrees"].hard_min_deg
                  for u in (0, h, 2*h)]
        assert values[0] == pytest.approx(90)
        return abs((values[2] - 2 * values[1] + values[0]) / h**2)
    assert endpoint_curvature(5e-5) < .6 * endpoint_curvature(1e-4)


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(extra=True),
    lambda p: p.__setitem__("classification", "biological_hard_limits"),
    lambda p: p["angle_conventions"].__setitem__("hip_sagittal_degrees", "local Euler"),
    lambda p: p["evidence"].__setitem__("sources", []),
    lambda p: p["evidence"].__setitem__("limitations", []),
    lambda p: p["evidence"].__setitem__("status", "biologically_certified"),
    lambda p: p["envelopes"].pop("support"),
    lambda p: p["envelopes"]["swing"].pop("ankle_interior_degrees"),
    lambda p: p["envelopes"]["swing"]["knee_interior_degrees"].__setitem__("hard_degrees", [120, 80]),
    lambda p: p["envelopes"]["swing"]["ankle_interior_degrees"].__setitem__("hard_degrees", [-1, 180]),
    lambda p: p["envelopes"]["swing"]["hip_sagittal_degrees"].__setitem__("hard_degrees", [False, 90]),
    lambda p: p["envelopes"]["swing"]["hip_sagittal_degrees"].__setitem__("hard_degrees", [math.nan, 90]),
    lambda p: p["envelopes"]["swing"]["hip_sagittal_degrees"].__setitem__("contraction_per_speed", 1),
])
def test_invalid_profiles_fail_closed(mutate):
    raw = profile_payload()
    mutate(raw)
    with pytest.raises(ContractError):
        load_articulation_profile(raw)


def test_omitted_profile_preserves_exact_legacy_solver_bytes_and_receipt():
    source, roles = fixture()
    gait = AirborneGait(cycles=1, sample_hz=24,
                       step_length_body_heights=.38,
                       touchdown_reach_body_heights=.17,
                       swing_clearance_body_heights=.18)
    omitted = solve_airborne_gait(source, source_clip="source", semantic_roles=roles, gait=gait)
    explicit = solve_airborne_gait(source, source_clip="source", semantic_roles=roles, gait=gait,
                                   articulation_profile=None)
    assert explicit == omitted


def test_profile_receipt_exposes_phase_and_convention_without_changing_plan():
    source, roles = fixture()
    gait = AirborneGait(cycles=1, sample_hz=24,
                       step_length_body_heights=.38,
                       touchdown_reach_body_heights=.17,
                       swing_clearance_body_heights=.18)
    baseline = solve_airborne_gait(source, source_clip="source", semantic_roles=roles, gait=gait)
    profile = load_articulation_profile(profile_payload())
    _, _, plan, receipt = solve_airborne_gait(
        source, source_clip="source", semantic_roles=roles, gait=gait,
        articulation_profile=profile,
    )
    assert plan == baseline[2]
    assert receipt["articulation_profile"]["angle_conventions"] == ANGLE_CONVENTIONS
    phases = {foot["articulation_phase"]
              for row in receipt["emitted_proxy_samples"] for foot in row["feet"].values()}
    assert phases == {"support", "swing"}
    assert all(set(foot["articulation_angles_degrees"]) == set(ANGLE_CONVENTIONS)
               for row in receipt["emitted_proxy_samples"] for foot in row["feet"].values())


def test_support_preference_changes_loaded_solve_but_not_interior_swing():
    source, roles = fixture()
    gait = AirborneGait(cycles=1, sample_hz=24,
                       step_length_body_heights=.38,
                       touchdown_reach_body_heights=.17,
                       swing_clearance_body_heights=.18)
    broad = profile_payload()
    preferred = profile_payload()
    preferred["envelopes"]["support"]["ankle_interior_degrees"]["preferred_degrees"] = [150, 175]
    solved = [solve_airborne_gait(
        source, source_clip="source", semantic_roles=roles, gait=gait,
        articulation_profile=load_articulation_profile(raw),
    ) for raw in (broad, preferred)]
    receipts = [item[3] for item in solved]
    def pitches(receipt, phase):
        return [foot["solved_foot_pitch_degrees"]
                for row in receipt["emitted_proxy_samples"] for foot in row["feet"].values()
                if foot["articulation_phase"] == phase]
    assert pitches(receipts[0], "support") != pitches(receipts[1], "support")
    # At the middle of swing the C2 phase transfer has fully released support.
    middle = []
    for receipt in receipts:
        middle.append([foot["solved_foot_pitch_degrees"]
                       for row, planned in zip(receipt["emitted_proxy_samples"],
                                               solved[0][2]["samples"])
                       for side, foot in row["feet"].items()
                       if not foot["contact"] and .3 < planned["feet"][side]["swing_phase"] < .7])
    assert middle[0] == middle[1]


def test_recipe_hash_binds_profile_and_supported_actions_reject_it(tmp_path, monkeypatch):
    recipe_path = make_recipe(tmp_path)
    write_json(tmp_path / "articulation.json", profile_payload())
    recipe = json.loads(recipe_path.read_text())
    recipe["articulation_profile"] = bind(tmp_path, tmp_path / "articulation.json")
    write_json(recipe_path, recipe)
    _, paths = load_recipe(recipe_path, tmp_path)
    assert paths["articulation_profile"] == tmp_path / "articulation.json"
    out = tmp_path / "candidate"
    compile_recipe(recipe_path, root=tmp_path, output=out)
    lock = json.loads((out / "inputs.lock.json").read_text())
    runtime = json.loads((out / "runtime.json").read_text())
    validation = json.loads((out / "validation.json").read_text())
    assert lock["inputs"]["articulation_profile"] == recipe["articulation_profile"]
    assert runtime["articulation_profile"]["id"] == profile_payload()["id"]
    assert {row["status"] for row in validation["articulation_envelopes"].values()} == {"PASS"}
    assert (out / "articulation-profile.json").read_bytes() == (tmp_path / "articulation.json").read_bytes()
    assert verify_package(out)["integrity"] == "PASS"

    # Exercise the package verifier's combined key plus midpoint authority.
    # A midpoint failure is a reachable BLOCKED package and must not be
    # mistaken for either a PASS or inconsistent evidence.
    cubic = tmp_path / "cubic-midpoint-blocked"
    shutil.copytree(out, cubic)
    cubic_runtime = json.loads((cubic / "runtime.json").read_text())
    cubic_runtime["interpolation"] = "CUBICSPLINE"
    write_json(cubic / "runtime.json", cubic_runtime)
    key_plan = json.loads((cubic / "plan.json").read_text())
    midpoint_plan = deepcopy(key_plan)
    midpoint_plan["samples"] = [
        item
        for left, right in zip(key_plan["samples"][:-1], key_plan["samples"][1:])
        for item in (
            deepcopy(left),
            {
                **deepcopy(left),
                "time_s": (left["time_s"] + right["time_s"]) / 2,
            },
        )
    ] + [deepcopy(key_plan["samples"][-1])]
    write_json(cubic / "cubic-midpoint-plan.json", midpoint_plan)
    profile_receipt = load_articulation_profile(profile_payload()).receipt()
    passed = {"status": "PASS", "profile": profile_receipt}
    failed = {"status": "FAIL", "profile": profile_receipt,
              "witness": {"sample_index": 1}}
    cubic_validation = json.loads((cubic / "validation.json").read_text())
    cubic_validation["technical_status"] = "BLOCKED"
    cubic_validation["articulation_envelopes"] = {
        "root_motion": passed, "in_place": passed,
    }
    cubic_validation["cubic_midpoint_articulation_envelopes"] = {
        "root_motion": failed, "in_place": failed,
    }
    cubic_validation["cubic_midpoint_skinned_contact"] = {
        "root_motion": {"verdict": "PASS"},
        "in_place": {"verdict": "PASS"},
    }
    write_json(cubic / "validation.json", cubic_validation)
    cubic_receipt = json.loads((cubic / "solver-receipt.json").read_text())
    cubic_receipt["final_emitted_articulation_gate"] = "FAIL"
    write_json(cubic / "solver-receipt.json", cubic_receipt)
    cubic_lock = json.loads((cubic / "inputs.lock.json").read_text())
    cubic_lock["emission"] = {
        "interpolation": "CUBICSPLINE",
        "source_tangent_stencil_s": 0.001,
        "convergence_stencil_s": 0.0005,
    }
    write_json(cubic / "inputs.lock.json", cubic_lock)
    cubic_manifest = json.loads((cubic / "manifest.json").read_text())
    cubic_manifest["technical_status"] = "BLOCKED"
    cubic_manifest["files"]["cubic-midpoint-plan.json"] = digest(
        (cubic / "cubic-midpoint-plan.json").read_bytes()
    )
    for filename in (
        "runtime.json", "validation.json", "solver-receipt.json", "inputs.lock.json"
    ):
        cubic_manifest["files"][filename] = digest((cubic / filename).read_bytes())
    write_json(cubic / "manifest.json", cubic_manifest)
    with monkeypatch.context() as local:
        local.setattr(
            "eonwild_motion.factory.compiler.emitted_articulation_envelopes",
            lambda *args, sample_times=None, **kwargs: (
                failed if sample_times is not None else passed
            ),
        )
        assert verify_package(cubic) == {
            "integrity": "PASS",
            "technical_status": "BLOCKED",
            "visual_review": "PENDING",
            "unity_parity": "NOT_RUN",
            "production_approved": False,
        }

    altered = tmp_path / "altered-angle"
    shutil.copytree(out, altered)
    filename = "root_motion.glb"
    glb = Glb.from_bytes((altered / filename).read_bytes())
    clip = glb.document["animations"][0]["name"]
    ankle = runtime["rig_roles"]["legs"]["right"]["contactChain"][2]
    accessor = glb.rotation_accessors(clip)[ankle]
    offset, count, stride = glb.accessor_region(accessor)
    binary = bytearray(glb.binary)
    for index in range(count):
        struct.pack_into("<4f", binary, offset + index * stride, 0.0, 0.0, 0.0, 1.0)
    (altered / filename).write_bytes(_encode(glb.document, bytes(binary)))
    altered_manifest = json.loads((altered / "manifest.json").read_text())
    altered_manifest["files"][filename] = digest((altered / filename).read_bytes())
    write_json(altered / "manifest.json", altered_manifest)
    with pytest.raises(ContractError, match="articulation profile provenance"):
        verify_package(altered)

    # Even with a self-consistent file hash inventory, provenance divergence
    # between the receipt and runtime fails closed.
    runtime["articulation_profile"]["evidence_status"] = "forged"
    write_json(out / "runtime.json", runtime)
    manifest = json.loads((out / "manifest.json").read_text())
    manifest["files"]["runtime.json"] = digest((out / "runtime.json").read_bytes())
    write_json(out / "manifest.json", manifest)
    with pytest.raises(ContractError, match="provenance"):
        verify_package(out)

    # The external profile itself remains immutable through its recipe hash.
    mutated = profile_payload()
    mutated["evidence"]["status"] = "changed"
    write_json(tmp_path / "articulation.json", mutated)
    with pytest.raises(ContractError, match="hash mismatch"):
        compile_recipe(recipe_path, root=tmp_path, output=tmp_path / "changed-input")

    action = deepcopy(recipe)
    action["program"] = "supported_action"
    write_json(tmp_path / "action-recipe.json", action)
    with pytest.raises(ContractError, match="retain their own support limits"):
        load_recipe(tmp_path / "action-recipe.json", tmp_path)


def test_final_envelope_check_rejects_invalid_axes_and_impossible_reopened_angle():
    source, roles = fixture()
    gait = AirborneGait(cycles=1, sample_hz=24,
                       step_length_body_heights=.38,
                       touchdown_reach_body_heights=.17,
                       swing_clearance_body_heights=.18)
    raw, _, plan, _ = solve_airborne_gait(source, source_clip="source", semantic_roles=roles, gait=gait)
    glb = Glb.from_bytes(raw)
    profile = load_articulation_profile(profile_payload())
    with pytest.raises(ContractError, match="axes"):
        emitted_articulation_envelopes(glb, semantic_roles=roles, plan=plan,
            profile=profile, forward_axis=[0, 0, 0], up_axis=[0, 1, 0])
    with pytest.raises(ContractError, match="axes"):
        emitted_articulation_envelopes(glb, semantic_roles=roles, plan=plan,
            profile=profile, forward_axis=[0, 0, 1e-8], up_axis=[0, 0, 2e-8])
    impossible = profile_payload()
    impossible["envelopes"]["support"]["knee_interior_degrees"] = {
        "hard_degrees": [179, 180], "preferred_degrees": [179, 180]}
    impossible = load_articulation_profile(impossible)
    result = emitted_articulation_envelopes(glb, semantic_roles=roles, plan=plan,
        profile=impossible, forward_axis=[0, 0, 1], up_axis=[0, 1, 0])
    assert result["status"] == "FAIL"
    assert result["witness"]["joint"] == "knee_interior_degrees"
    assert result["observed_degrees"]["support"]["knee_interior_degrees"][1] < 179


@pytest.mark.parametrize(
    ("program", "locomotion_program"),
    [("grounded_gait", None), ("gait_transition", "grounded_gait")],
)
def test_final_grounded_envelope_check_fails_when_a_leg_has_no_swing_observation(
    program, locomotion_program,
):
    source, roles = fixture()
    gait = GroundedGait(cycles=1, sample_hz=24)
    plan = build_grounded_plan(gait, 2.)
    raw, _, _, _ = solve_airborne_gait(
        source,
        source_clip="source",
        semantic_roles=roles,
        gait=AirborneGait(),
        plan_override=plan,
        articulation_profile=load_articulation_profile(profile_payload()),
    )
    corrupted = deepcopy(plan)
    corrupted["program"] = program
    if locomotion_program is not None:
        corrupted["locomotion_program"] = locomotion_program
    for row in corrupted["samples"]:
        row["feet"]["left"]["contact"] = True
    result = emitted_articulation_envelopes(
        Glb.from_bytes(raw),
        semantic_roles=roles,
        plan=corrupted,
        profile=load_articulation_profile(profile_payload()),
        forward_axis=[0, 0, 1],
        up_axis=[0, 1, 0],
    )
    assert result["status"] == "FAIL"
    assert result["missing_phase_samples"] == ["left:swing"]

    if locomotion_program is not None:
        return
    supported = deepcopy(corrupted)
    supported["program"] = "supported_action"
    result = emitted_articulation_envelopes(
        Glb.from_bytes(raw),
        semantic_roles=roles,
        plan=supported,
        profile=load_articulation_profile(profile_payload()),
        forward_axis=[0, 0, 1],
        up_axis=[0, 1, 0],
    )
    assert result["status"] == "PASS"
    assert "missing_phase_samples" not in result
