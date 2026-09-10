"""Factory contracts and adversarial regressions; not visual acceptance."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import math

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.compiler import compile_recipe, verify_package, validate_plan, event_track
from eonwild_motion.factory.io import bind, confined, digest, frame_axes, locked_file, signed_heading_degrees, write_json
from eonwild_motion.factory.source import admit_geometry
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.grounded_gait import (
    GroundedGait,
    build_grounded_plan,
    require_grounded_phase_coverage,
    sample_grounded_gait,
)
from eonwild_motion.solve.whole_body_gait_transition import _append_accessor, _encode
from test_v9_airborne_gait import fixture

ROOT = Path(__file__).resolve().parents[1]


def _midpoint_contact_result(verdict: str, sample_count: int) -> dict:
    return {
        "verdict": verdict,
        "authority": {
            "per_foot": {
                side: {"verdict": verdict, "phases": [], "reasons": []}
                for side in ("left", "right")
            }
        },
        "maximum_penetration_m": 1.0 if verdict == "FAIL" else 0.0,
        "maximum_stance_gap_m": 0.0001,
        "ground_level_m": 0.0,
        "sample_count": sample_count,
        "classification": (
            "final serialized skin, fixed floor, full multi-influence weights, "
            "unchanged engineering thresholds"
        ),
    }


def make_recipe(root: Path, *, prefix="fixture", scale=1.0, program="grounded_gait") -> Path:
    source, roles = fixture(prefix, scale, upper_body=True)
    raw, geometry = admit_geometry(source, roles, reference_clip="source")
    (root / "geometry.glb").write_bytes(raw)
    write_json(root / "rig.json", {"roles": roles})
    if program == "grounded_gait":
        profile = {"schema": "eonwild.motion.v9.grounded-gait.v1", "parameters": {"cycles": 1, "sample_hz": 24}}
    else:
        profile = {"schema": "eonwild.motion.v9.airborne-gait.v1", "program": "airborne_gait", "body_branching": False,
            "parameters": {"cycles": 1, "sample_hz": 24, "step_length_body_heights": .38,
                           "touchdown_reach_body_heights": .17, "swing_clearance_body_heights": .18}}
    write_json(root / "program.json", profile)
    recipe = {"schema": "eonwild.motion.factory-recipe.v1", "id": "fixture." + program, "version": 1,
        "family": "digitigrade-biped", "program": program,
        "source": bind(root, root / "geometry.glb"), "rig": bind(root, root / "rig.json"),
        "program_profile": bind(root, root / "program.json"),
        "forward_axis": geometry["forward_axis"], "up_axis": geometry["up_axis"]}
    write_json(root / "recipe.json", recipe)
    return root / "recipe.json"


def test_reverse_walk_has_double_support_and_signed_travel():
    gait = GroundedGait()
    rows = [sample_grounded_gait(gait, (i + .5) / 10000, 2.) for i in range(16000)]
    assert all(not row["flight"] for row in rows)
    assert {row["support_count"] for row in rows} == {1, 2}
    assert sum(row["feet"]["left"]["contact"] for row in rows) / len(rows) == pytest.approx(.72, abs=1e-4)
    assert rows[-1]["root_forward_m"] < rows[0]["root_forward_m"]
    values = [sample_grounded_gait(gait, t, 2.)["feet"]["left"]["forward_m"] for t in (.05, .15, .5)]
    assert max(values) == min(values)


def test_grounded_contact_boundaries_are_continuous():
    gait = GroundedGait()
    period = 2 * gait.step_period_s
    for boundary in (period * gait.duty_factor, period):
        h = 1e-5
        rows = [sample_grounded_gait(gait, boundary + delta, 2.) for delta in (-h, 0, h)]
        for field in ("forward_m", "height_m"):
            v = [row["feet"]["left"][field] for row in rows]
            assert abs((v[1]-v[0])/h - (v[2]-v[1])/h) < .001


def test_grounded_plan_rejects_clock_that_never_observes_swing():
    gait = GroundedGait(
        step_period_s=.06,
        duty_factor=.999,
        cycles=1,
        sample_hz=24,
    )
    raw_samples = [
        sample_grounded_gait(gait, time_s, 1.)
        for time_s in (0., .04, .08, .12)
    ]
    assert all(row["support_count"] == 2 for row in raw_samples)
    with pytest.raises(ContractError, match="left:swing, right:swing"):
        require_grounded_phase_coverage(raw_samples)
    with pytest.raises(ContractError, match="observe support and swing"):
        build_grounded_plan(gait, 1.)


@pytest.mark.parametrize("change", [{"duty_factor": .475}, {"cycles": True}, {"step_period_s": 0}, {"step_length_body_heights": 0}, {"sample_hz": 23}, {"pelvis_crouch_body_heights": math.nan},
    {"handoff_phase_fraction": -.01, "handoff_sample_hz": 960},
    {"handoff_phase_fraction": .26, "handoff_sample_hz": 960},
    {"handoff_phase_fraction": .125, "handoff_sample_hz": 23},
    {"handoff_phase_fraction": .125, "handoff_sample_hz": None},
    {"handoff_phase_fraction": None, "handoff_sample_hz": 960}])
def test_grounded_invalid_parameters_fail_closed(change):
    with pytest.raises(ContractError):
        GroundedGait(**change)


def test_signed_heading_distinguishes_opposite_yaws():
    headings = [signed_heading_degrees([math.sin(math.radians(a)), 0, math.cos(math.radians(a))], [0, 0, 1], [0, 1, 0]) for a in (20, -20)]
    assert headings == pytest.approx([20, -20])
    assert abs(headings[0] - headings[1]) == pytest.approx(40)


def test_input_escape_corruption_and_bad_axes_reject(tmp_path):
    with pytest.raises(ContractError): confined(tmp_path, "../escape")
    with pytest.raises(ContractError): confined(tmp_path, "/absolute")
    with pytest.raises(ContractError): frame_axes([0, 1, 0], [0, 1, 0])
    p = tmp_path / "data.json"
    p.write_text("original")
    ref = bind(tmp_path, p)
    p.write_text("changed")
    with pytest.raises(ContractError): locked_file(tmp_path, ref)


def test_geometry_has_no_choreography_and_requires_explicit_frame():
    source, roles = fixture()
    raw, metadata = admit_geometry(source, roles, reference_clip="source")
    neutral = Glb.from_bytes(raw)
    assert not neutral.document.get("animations")
    assert metadata["forward_axis"] == pytest.approx([0, 0, 1])
    with pytest.raises(ContractError): admit_geometry(neutral, roles)


def test_plan_rejects_inconsistent_support_and_no_spawn_impact():
    plan = build_grounded_plan(GroundedGait(), 2.)
    validate_plan(plan, "grounded_gait")
    assert all(event["time_s"] > 0 for event in event_track(plan))
    plan["samples"][0]["flight"] = True
    with pytest.raises(ContractError): validate_plan(plan, "grounded_gait")


@pytest.mark.parametrize("program", ["grounded_gait", "airborne_gait"])
def test_repeat_compile_is_exact_and_reopened_receipts_are_bound(tmp_path, program):
    recipe = make_recipe(tmp_path, program=program)
    a, b = tmp_path / "first", tmp_path / "second"
    one = compile_recipe(recipe, root=tmp_path, output=a)
    two = compile_recipe(recipe, root=tmp_path, output=b)
    assert one == two
    for name in one["files"]:
        assert (a / name).read_bytes() == (b / name).read_bytes()
    assert verify_package(a)["integrity"] == "PASS"
    assert verify_package(a)["production_approved"] is False
    assert verify_package(a)["technical_status"] == "BLOCKED"  # no skin fixture
    validation = json.loads((a / "validation.json").read_text())
    assert validation["outputs"]["root_motion"]["checks"]["root_matches_plan"]
    assert validation["outputs"]["in_place"]["checks"]["root_matches_plan"]
    with pytest.raises(ContractError): compile_recipe(recipe, root=tmp_path, output=a)
    (a / "root_motion.glb").write_bytes((a / "root_motion.glb").read_bytes() + b"tamper")
    with pytest.raises(ContractError): verify_package(a)


def test_profile_free_cubic_metadata_and_midpoint_verdict_are_bound(
    tmp_path, monkeypatch
):
    recipe = make_recipe(tmp_path)
    output = tmp_path / "candidate"
    compile_recipe(recipe, root=tmp_path, output=output)
    runtime = json.loads((output / "runtime.json").read_text())
    runtime["interpolation"] = "CUBICSPLINE"
    write_json(output / "runtime.json", runtime)
    lock = json.loads((output / "inputs.lock.json").read_text())
    lock["emission"] = {
        "interpolation": "CUBICSPLINE",
        "source_tangent_stencil_s": 0.001,
        "convergence_stencil_s": 0.0005,
    }
    write_json(output / "inputs.lock.json", lock)
    manifest = json.loads((output / "manifest.json").read_text())
    for filename in ("runtime.json", "inputs.lock.json"):
        manifest["files"][filename] = digest((output / filename).read_bytes())
    write_json(output / "manifest.json", manifest)
    monkeypatch.setattr(
        "eonwild_motion.factory.compiler._serialized_interpolation",
        lambda glb: "CUBICSPLINE",
    )
    with pytest.raises(ContractError, match="lacks midpoint plan evidence"):
        verify_package(output)

    plan = json.loads((output / "plan.json").read_text())
    midpoint = deepcopy(plan)
    midpoint["samples"] = [
        item
        for left, right in zip(plan["samples"][:-1], plan["samples"][1:])
        for item in (
            deepcopy(left),
            {**deepcopy(left), "time_s": (left["time_s"] + right["time_s"]) / 2},
        )
    ] + [deepcopy(plan["samples"][-1])]
    write_json(output / "cubic-midpoint-plan.json", midpoint)
    validation = json.loads((output / "validation.json").read_text())
    validation["technical_status"] = "PASS"
    validation["cubic_midpoint_skinned_contact"] = {
        "root_motion": _midpoint_contact_result("FAIL", len(midpoint["samples"])),
        "in_place": _midpoint_contact_result("PASS", len(midpoint["samples"])),
    }
    write_json(output / "validation.json", validation)
    manifest["technical_status"] = "PASS"
    for filename in ("cubic-midpoint-plan.json", "validation.json"):
        manifest["files"][filename] = digest((output / filename).read_bytes())
    write_json(output / "manifest.json", manifest)
    bare = deepcopy(validation)
    bare["cubic_midpoint_skinned_contact"] = {
        "root_motion": {"verdict": "PASS"},
        "in_place": {"verdict": "PASS"},
    }
    write_json(output / "validation.json", bare)
    manifest["files"]["validation.json"] = digest(
        (output / "validation.json").read_bytes()
    )
    write_json(output / "manifest.json", manifest)
    with pytest.raises(ContractError, match="result shape is invalid"):
        verify_package(output)
    write_json(output / "validation.json", validation)
    manifest["files"]["validation.json"] = digest(
        (output / "validation.json").read_bytes()
    )
    write_json(output / "manifest.json", manifest)
    with pytest.raises(ContractError, match="ignores midpoint contact failure"):
        verify_package(output)
    validation["technical_status"] = "BLOCKED"
    write_json(output / "validation.json", validation)
    manifest["technical_status"] = "BLOCKED"
    manifest["files"]["validation.json"] = digest(
        (output / "validation.json").read_bytes()
    )
    write_json(output / "manifest.json", manifest)
    assert verify_package(output)["technical_status"] == "BLOCKED"


def test_source_cubic_checkpoint_runtime_is_hash_bound_and_reviewable(tmp_path):
    source_recipe = json.loads(
        (
            ROOT
            / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v10.json"
        ).read_text()
    )
    recipe = dict(source_recipe)
    for key in (
        "source",
        "rig",
        "animal",
        "contact_profile",
        "performance_profile",
        "program_profile",
        "articulation_profile",
    ):
        source_path = ROOT / source_recipe[key]["path"]
        target_path = tmp_path / source_recipe[key]["path"]
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(source_path.read_bytes())
        if key == "program_profile":
            program = json.loads(target_path.read_text())
            # A short source clock keeps this contract test focused on the
            # checkpoint payload while retaining the real skinned source and
            # all existing contact/semantic bindings.
            program["parameters"]["sample_hz"] = 24
            write_json(target_path, program)
        recipe[key] = bind(tmp_path, target_path)
    recipe["id"] = "checkpoint-review.tarbosaurus.v1"
    recipe_path = tmp_path / "recipe.json"
    write_json(recipe_path, recipe)

    output = tmp_path / "candidate"
    checkpoint = tmp_path / "checkpoint"
    compile_recipe(
        recipe_path,
        root=tmp_path,
        output=output,
        interpolation="CUBICSPLINE",
        emission_checkpoint=checkpoint,
    )

    manifest = json.loads((checkpoint / "manifest.json").read_text())
    runtime = json.loads((checkpoint / "runtime.json").read_text())
    plan = json.loads((checkpoint / "plan.json").read_text())
    contact = json.loads(
        (tmp_path / source_recipe["contact_profile"]["path"]).read_text()
    )
    animal = json.loads(
        (tmp_path / source_recipe["animal"]["path"]).read_text()
    )
    rig = json.loads((tmp_path / source_recipe["rig"]["path"]).read_text())

    assert manifest["schema"] == "eonwild.motion.source-cubic-emission-checkpoint.v1"
    assert manifest["kind"] == "pre_gate_source_cubic_diagnostic"
    assert manifest["status"] == "DIAGNOSTIC"
    assert manifest["technical_status"] == "NOT_EVALUATED"
    assert manifest["production_approved"] is False
    assert manifest["visual_review"] == "PENDING"
    assert manifest["unity_parity"] == "NOT_RUN"
    assert manifest["claims"] == {
        "physical": False,
        "scientific": False,
        "biological": False,
    }
    assert manifest["files"]["runtime.json"] == digest(
        (checkpoint / "runtime.json").read_bytes()
    )
    assert runtime["duration_s"] == plan["samples"][-1]["time_s"]
    assert runtime["plan_sha256"] == digest((checkpoint / "plan.json").read_bytes())
    assert runtime["forward_axis"] == recipe["forward_axis"]
    assert runtime["up_axis"] == recipe["up_axis"]
    assert runtime["rig_roles"]["root"] == rig["roles"]["root"]
    assert runtime["ground_plane"]["up_axis"] == "Y"
    assert runtime["ground_plane"]["level_m"] == pytest.approx(
        contact["geometry"]["ground"]["level_m"]
        * runtime["animal"]["uniform_geometry_scale"]
    )
    assert runtime["body_height_m"] == runtime["animal"][
        "semantic_pelvis_to_toe_plane_m"
    ]
    assert runtime["body_height_m"] == pytest.approx(plan["body_height_m"])
    assert runtime["interpolation"] == "CUBICSPLINE"


def test_serialized_cubic_exports_cannot_be_declared_linear(tmp_path):
    recipe = make_recipe(tmp_path)
    output = tmp_path / "candidate"
    compile_recipe(recipe, root=tmp_path, output=output)
    for mode in ("root_motion", "in_place"):
        path = output / f"{mode}.glb"
        glb = Glb.from_bytes(path.read_bytes())
        binary = bytearray(glb.binary)
        animation = glb.document["animations"][0]
        for channel in animation["channels"]:
            sampler = animation["samplers"][channel["sampler"]]
            values = np.asarray(glb.accessor_values(sampler["output"]), dtype=float)
            records = np.stack(
                (np.zeros_like(values), values, np.zeros_like(values)), axis=1
            )
            sampler["output"] = _append_accessor(
                glb.document,
                binary,
                records.reshape((-1, values.shape[1])),
                {3: "VEC3", 4: "VEC4"}[values.shape[1]],
            )
            sampler["interpolation"] = "CUBICSPLINE"
        glb.document["buffers"][0]["byteLength"] = len(binary)
        path.write_bytes(_encode(glb.document, binary))
    manifest = json.loads((output / "manifest.json").read_text())
    for mode in ("root_motion", "in_place"):
        filename = f"{mode}.glb"
        manifest["files"][filename] = digest((output / filename).read_bytes())
    write_json(output / "manifest.json", manifest)
    with pytest.raises(ContractError, match="declaration differs from serialized"):
        verify_package(output)


@pytest.mark.parametrize("prefix,scale", [("renamed_", 1.), ("another_rig_", 1.6)])
def test_grounded_recipe_emits_renamed_scaled_body_without_code_branch(tmp_path, prefix, scale):
    recipe = make_recipe(tmp_path, prefix=prefix, scale=scale)
    out = tmp_path / "candidate"
    compile_recipe(recipe, root=tmp_path, output=out)
    plan = json.loads((out / "plan.json").read_text())
    assert plan["program"] == "grounded_gait"
    assert all(row["support_count"] >= 1 for row in plan["samples"])
    runtime = json.loads((out / "runtime.json").read_text())
    assert runtime["rig_roles"]["root"].startswith(prefix)


def test_factory_code_does_not_import_generated_experiments():
    root = Path(__file__).parents[1] / "src/eonwild_motion/factory"
    for file in root.glob("*.py"):
        text = file.read_text()
        assert "sys.path.insert" not in text
        assert "spec_from_file_location" not in text
        assert "build/V9-" not in text
