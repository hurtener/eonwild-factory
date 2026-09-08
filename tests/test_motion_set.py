"""Shared motion-set binding and reconstruction contracts."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
import json

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.io import bind, json_bytes, write_json
from eonwild_motion.factory.motion_set import (
    reconstruct_motion_set,
    resolve_motion_set,
    resolve_motion_set_selection,
)
from eonwild_motion.factory.handoff import require_shared_motion_baseline
from eonwild_motion.factory.compiler import _verify_motion_set_provenance, compile_recipe
from eonwild_motion.factory.__main__ import main as factory_main
from eonwild_motion.planning.grounded_gait import build_grounded_plan, load_grounded_gait
from eonwild_motion.planning.gait_transition import (
    build_transition_plan,
    load_gait_transition,
)
from eonwild_motion.solve.gait_response import (
    assemble_baseline_performance,
    resolve_gait_response,
)
from eonwild_motion.solve.performance import decorate_plan, load_performance


ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def _documents(root):
    for name in (
        "source.glb", "rig.json", "animal.json", "contact.json",
        "articulation.json", "performance.json", "program.json",
    ):
        (root / name).write_text(name)
    (root / "neutral.json").write_bytes(
        (ROOT / "catalog/calibration/tarbosaurus-pin-552-1-adult-neutral.v1.json").read_bytes()
    )
    baseline = {
        "schema": "eonwild.motion.motion-baseline.v1",
        "id": "animal.grounded.v1",
        "version": 1,
        "family": "portable-biped",
        "source": bind(root, root / "source.glb"),
        "rig": bind(root, root / "rig.json"),
        "animal": bind(root, root / "animal.json"),
        "contact_profile": bind(root, root / "contact.json"),
        "articulation_profile": bind(root, root / "articulation.json"),
        "performance_profile": bind(root, root / "performance.json"),
        "neutral_pose_profile": bind(root, root / "neutral.json"),
        "forward_axis": [0, 0, 1],
        "up_axis": [0, 1, 0],
        "supported_programs": ["grounded_gait", "gait_transition"],
        "gait_response_policy": {
            "schema": "eonwild.motion.gait-response-policy.v1",
            "model": "reference_scaled_excursion_exchange.v1",
            "reference": {
                "step_period_s": 1.23,
                "step_length_body_heights": 0.6,
                "pelvis_excursion_body_heights": 0.016,
                "pelvis_forward_velocity_modulation_fraction": 0.145,
            },
        },
        "solve_policy": {
            "schema": "eonwild.motion.solve-policy.v1",
            "representation": "CUBICSPLINE",
            "canonical_support_anchors": True,
            "grounded_transition_clearance": "material_floor_scaled_excess.v1",
            "skin_target_law": "canonical_constant_skin_targets.v1",
            "skin_refinement": True,
        },
    }
    intent = {
        "schema": "eonwild.motion.motion-intent.v1",
        "id": "portable-biped.walk.v1",
        "version": 1,
        "program": "grounded_gait",
        "program_profile": bind(root, root / "program.json"),
        "description": "portable timing intent",
    }
    write_json(root / "baseline.json", baseline)
    write_json(root / "intent.json", intent)
    motion_set = {
        "schema": "eonwild.motion.motion-set.v1",
        "id": "animal.motion-set.v1",
        "version": 1,
        "baseline": bind(root, root / "baseline.json"),
        "motions": [{"name": "walk", "intent": bind(root, root / "intent.json")}],
    }
    write_json(root / "set.json", motion_set)
    return baseline, intent, motion_set


def test_one_baseline_resolves_a_canonical_flat_recipe(tmp_path):
    baseline, intent, _ = _documents(tmp_path)
    resolved = resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")
    assert resolved.recipe == {
        "schema": "eonwild.motion.factory-recipe.v1",
        "id": intent["id"],
        "version": intent["version"],
        "family": baseline["family"],
        "program": intent["program"],
        **{
            key: baseline[key]
            for key in (
                "source", "rig", "animal", "contact_profile",
                "articulation_profile", "performance_profile",
            )
        },
        "program_profile": intent["program_profile"],
        "forward_axis": baseline["forward_axis"],
        "up_axis": baseline["up_axis"],
        "description": intent["description"],
    }
    assert "neutral_pose_profile" not in resolved.recipe
    assert reconstruct_motion_set(
        set_bytes=resolved.set_bytes,
        baseline_bytes=resolved.baseline_bytes,
        intent_bytes=resolved.intent_bytes,
        resolution_lock=resolved.lock,
    ) == resolved.recipe


def test_transition_clearance_policy_is_additive_and_strict(tmp_path):
    baseline, _, motion_set = _documents(tmp_path)
    baseline["solve_policy"].pop("grounded_transition_clearance")
    write_json(tmp_path / "baseline.json", baseline)
    motion_set["baseline"] = bind(tmp_path, tmp_path / "baseline.json")
    write_json(tmp_path / "set.json", motion_set)
    resolved = resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")
    assert "grounded_transition_clearance" not in resolved.solve_policy

    baseline["solve_policy"]["grounded_transition_clearance"] = "unknown"
    write_json(tmp_path / "baseline.json", baseline)
    motion_set["baseline"] = bind(tmp_path, tmp_path / "baseline.json")
    write_json(tmp_path / "set.json", motion_set)
    with pytest.raises(ContractError, match="supported explicit solve policy"):
        resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")


@pytest.mark.parametrize(
    "field",
    [
        "source", "rig", "animal", "contact_profile", "articulation_profile",
        "performance_profile", "neutral_pose_profile", "forward_axis",
        "up_axis", "gait_response_policy", "solve_policy",
    ],
)
def test_intent_cannot_override_shared_baseline_fields(tmp_path, field):
    _, intent, motion_set = _documents(tmp_path)
    intent[field] = "override"
    write_json(tmp_path / "intent.json", intent)
    motion_set["motions"][0]["intent"] = bind(tmp_path, tmp_path / "intent.json")
    write_json(tmp_path / "set.json", motion_set)
    with pytest.raises(ContractError, match="unknown fields"):
        resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")


def test_airborne_and_supported_intents_fail_before_input_resolution(tmp_path):
    _, intent, motion_set = _documents(tmp_path)
    for program in ("airborne_gait", "supported_action"):
        intent["program"] = program
        write_json(tmp_path / "intent.json", intent)
        motion_set["motions"][0]["intent"] = bind(tmp_path, tmp_path / "intent.json")
        write_json(tmp_path / "set.json", motion_set)
        with pytest.raises(ContractError, match="outside baseline capabilities"):
            resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")


@pytest.mark.parametrize("snapshot", ["set", "baseline", "intent"])
def test_reconstruction_rejects_rehashed_snapshot_substitution(tmp_path, snapshot):
    _documents(tmp_path)
    resolved = resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")
    values = {
        "set": resolved.set_bytes,
        "baseline": resolved.baseline_bytes,
        "intent": resolved.intent_bytes,
    }
    document = json.loads(values[snapshot])
    document["id"] += ".other"
    values[snapshot] = json_bytes(document)
    lock = deepcopy(resolved.lock)
    if snapshot == "set":
        lock["set"]["sha256"] = __import__("hashlib").sha256(values[snapshot]).hexdigest()
    with pytest.raises(ContractError, match="identit|differs"):
        reconstruct_motion_set(
            set_bytes=values["set"], baseline_bytes=values["baseline"],
            intent_bytes=values["intent"], resolution_lock=lock,
        )


def test_transition_requires_locked_gait_profile(tmp_path):
    _, intent, motion_set = _documents(tmp_path)
    intent["program"] = "gait_transition"
    write_json(tmp_path / "intent.json", intent)
    motion_set["motions"][0]["intent"] = bind(tmp_path, tmp_path / "intent.json")
    write_json(tmp_path / "set.json", motion_set)
    with pytest.raises(ContractError, match="gait-transition"):
        resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")


def test_one_baseline_change_rebinds_every_selected_intent(tmp_path):
    baseline, intent, motion_set = _documents(tmp_path)
    second = {**intent, "id": "portable-biped.fast-walk.v1"}
    write_json(tmp_path / "fast.json", second)
    motion_set["motions"].append(
        {"name": "fast-walk", "intent": bind(tmp_path, tmp_path / "fast.json")}
    )
    write_json(tmp_path / "set.json", motion_set)
    before_values = resolve_motion_set_selection(
        tmp_path, tmp_path / "set.json", ["walk", "fast-walk"]
    )
    before = {value.motion: value for value in before_values}
    assert before_values[0].baseline_bytes is before_values[1].baseline_bytes
    baseline["family"] = "portable-biped-revised"
    write_json(tmp_path / "baseline.json", baseline)
    motion_set["baseline"] = bind(tmp_path, tmp_path / "baseline.json")
    write_json(tmp_path / "set.json", motion_set)
    after = {
        value.motion: value
        for value in resolve_motion_set_selection(
            tmp_path, tmp_path / "set.json", ["walk", "fast-walk"]
        )
    }
    assert {value.baseline_binding["sha256"] for value in before.values()} == {
        before["walk"].baseline_binding["sha256"]
    }
    assert {value.baseline_binding["sha256"] for value in after.values()} == {
        after["walk"].baseline_binding["sha256"]
    }
    assert before["walk"].baseline_binding != after["walk"].baseline_binding
    assert {value.recipe["family"] for value in after.values()} == {
        "portable-biped-revised"
    }


def test_packaged_snapshots_reconstruct_after_repository_inputs_change(tmp_path):
    _documents(tmp_path)
    resolved = resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")
    for name in ("set.json", "baseline.json", "intent.json"):
        (tmp_path / name).write_text("repository no longer available")
    assert reconstruct_motion_set(
        set_bytes=resolved.set_bytes,
        baseline_bytes=resolved.baseline_bytes,
        intent_bytes=resolved.intent_bytes,
        resolution_lock=resolved.lock,
    ) == resolved.recipe


def test_handoff_rejects_different_shared_baselines(tmp_path):
    baseline, _, _ = _documents(tmp_path)
    resolved = resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")
    packages = []
    for index in range(2):
        package = tmp_path / f"package-{index}"
        package.mkdir()
        (package / "motion-set.json").write_bytes(resolved.set_bytes)
        (package / "motion-intent.json").write_bytes(resolved.intent_bytes)
        (package / "motion-baseline.json").write_bytes(resolved.baseline_bytes)
        write_json(
            package / "inputs.lock.json",
            {"motion_set_resolution": resolved.lock},
        )
        packages.append(package)
    assert require_shared_motion_baseline(packages) is not None
    baseline["family"] = "other"
    write_json(packages[1] / "motion-baseline.json", baseline)
    with pytest.raises(ContractError, match="differ in shared motion baseline"):
        require_shared_motion_baseline(packages)


def test_real_shared_walk_preserves_v10_effective_body_parameters():
    resolution = resolve_motion_set(
        ROOT,
        ROOT / "catalog/motion-sets/tarbosaurus-pin-552-1-adult-grounded.v1.json",
        "walk",
    )
    baseline = json.loads(resolution.baseline_bytes)
    style = json.loads(
        (ROOT / baseline["performance_profile"]["path"]).read_text()
    )
    neutral = json.loads(resolution.neutral_pose_bytes)
    performance, _ = assemble_baseline_performance(style, neutral)
    gait = load_grounded_gait(
        json.loads((ROOT / resolution.recipe["program_profile"]["path"]).read_text())
    )
    performance, gait_receipt = resolve_gait_response(
        performance, gait, baseline["gait_response_policy"]
    )
    solve = baseline["solve_policy"]
    performance = replace(
        performance,
        canonical_support_anchors=solve["canonical_support_anchors"],
        skin_refinement=solve["skin_refinement"],
    )
    legacy_recipe = json.loads(
        (ROOT / "recipes/heavy-biped/tarbosaurus-pin-552-1-adult-walk.v10.json").read_text()
    )
    legacy = load_performance(
        json.loads((ROOT / legacy_recipe["performance_profile"]["path"]).read_text())
    )
    legacy = replace(legacy, canonical_support_anchors=True, skin_refinement=True)
    assert asdict(performance) == asdict(legacy)
    assert gait_receipt["resolved_pelvis_forward_velocity_modulation_fraction"] == (
        legacy.pelvis_forward_velocity_modulation_fraction
    )
    assert "program-profile.json" in resolution.payloads
    assert "gait-profile.json" not in resolution.payloads


def test_real_fast_intent_uses_same_baseline_with_gait_derived_response():
    set_path = ROOT / "catalog/motion-sets/tarbosaurus-pin-552-1-adult-grounded.v1.json"
    walk, fast = resolve_motion_set_selection(
        ROOT, set_path, ["walk", "fast-walk"]
    )
    assert walk.baseline_binding == fast.baseline_binding
    baseline = json.loads(fast.baseline_bytes)
    performance, _ = assemble_baseline_performance(
        json.loads((ROOT / baseline["performance_profile"]["path"]).read_text()),
        json.loads(fast.neutral_pose_bytes),
    )
    gait = load_grounded_gait(
        json.loads((ROOT / fast.recipe["program_profile"]["path"]).read_text())
    )
    resolved, receipt = resolve_gait_response(
        performance, gait, baseline["gait_response_policy"]
    )
    assert gait.pelvis_height_carrier == "stance_vault_proxy"
    assert resolved.pelvis_forward_velocity_modulation_fraction == pytest.approx(
        0.06142361867926274, abs=1e-15
    )
    assert receipt["target"]["step_period_s"] == 0.8
    original = json.loads((
        ROOT / "catalog/programs/heavy-biped.tarbosaurus-adult-fast-walk-recovery.v3.json"
    ).read_text())["parameters"]
    selected = json.loads((ROOT / fast.recipe["program_profile"]["path"]).read_text())[
        "parameters"
    ]
    assert {key: value for key, value in selected.items() if key != "pelvis_height_carrier"} == original
    transition = resolve_motion_set(ROOT, set_path, "walk-start")
    assert set(transition.payloads) >= {"program-profile.json", "gait-profile.json"}


def test_motion_set_cli_rejects_unsupported_representation_before_output(tmp_path):
    output = tmp_path / "must-not-exist"
    assert factory_main([
        "compile-set",
        "--motion-set",
        str(ROOT / "catalog/motion-sets/tarbosaurus-pin-552-1-adult-grounded.v1.json"),
        "--motions",
        "walk",
        "--root",
        str(ROOT),
        "--output",
        str(output),
        "--interpolation",
        "LINEAR",
    ]) == 1
    assert not output.exists()


def test_motion_set_rejects_path_name_before_output_creation(tmp_path):
    _, _, motion_set = _documents(tmp_path)
    motion_set["motions"][0]["name"] = "../escaped-package"
    write_json(tmp_path / "set.json", motion_set)
    output = tmp_path / "output"
    assert factory_main([
        "compile-set", "--motion-set", str(tmp_path / "set.json"),
        "--motions", "../escaped-package", "--root", str(tmp_path),
        "--output", str(output),
    ]) == 1
    assert not output.exists()


def test_motion_set_rejects_numeric_string_axes(tmp_path):
    baseline, _, motion_set = _documents(tmp_path)
    baseline["forward_axis"] = ["0", "0", "1"]
    write_json(tmp_path / "baseline.json", baseline)
    motion_set["baseline"] = bind(tmp_path, tmp_path / "baseline.json")
    write_json(tmp_path / "set.json", motion_set)
    with pytest.raises(ContractError, match="finite numeric vector"):
        resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")


def test_package_local_snapshots_rebuild_effective_performance(tmp_path):
    resolution = resolve_motion_set(
        ROOT,
        ROOT / "catalog/motion-sets/tarbosaurus-pin-552-1-adult-grounded.v1.json",
        "walk",
    )
    baseline = json.loads(resolution.baseline_bytes)
    style_bytes = (ROOT / baseline["performance_profile"]["path"]).read_bytes()
    performance, assembly = assemble_baseline_performance(
        json.loads(style_bytes), json.loads(resolution.neutral_pose_bytes)
    )
    gait = load_grounded_gait(
        json.loads((ROOT / resolution.recipe["program_profile"]["path"]).read_text())
    )
    performance, gait_receipt = resolve_gait_response(
        performance, gait, baseline["gait_response_policy"]
    )
    solve = baseline["solve_policy"]
    performance = replace(
        performance,
        canonical_support_anchors=solve["canonical_support_anchors"],
        skin_refinement=solve["skin_refinement"],
    )
    plan = decorate_plan(build_grounded_plan(gait, 2.0), performance)
    plan["solve_policy"] = solve
    for name, raw in {
        **resolution.payloads,
        "performance-profile.json": style_bytes,
        "neutral-pose-profile.json": resolution.neutral_pose_bytes,
    }.items():
        (tmp_path / name).write_bytes(raw)
    lock = {"motion_set_resolution": resolution.lock}
    runtime = {
        "motion_set": resolution.lock["identities"], "solve_policy": solve
    }
    receipt = {
        "solve_policy": solve,
        "baseline_performance_resolution": {
            "assembly": assembly, "gait_response": gait_receipt,
        },
    }
    plan = json.loads(json_bytes(plan))
    _verify_motion_set_provenance(
        tmp_path, recipe=resolution.recipe, lock=lock,
        runtime=runtime, receipt=receipt, plan=plan,
    )
    corrupted = deepcopy(plan)
    corrupted["performance"]["pelvis_yaw_degrees"] += 0.1
    with pytest.raises(ContractError, match="solve policy provenance"):
        _verify_motion_set_provenance(
            tmp_path, recipe=resolution.recipe, lock=lock,
            runtime=runtime, receipt=receipt, plan=corrupted,
        )
    corrupted = deepcopy(plan)
    corrupted["performance"]["neutral_jaw_calibration"][
        "joint_accessors"
    ][0] += 1
    with pytest.raises(ContractError, match="solve policy provenance"):
        _verify_motion_set_provenance(
            tmp_path, recipe=resolution.recipe, lock=lock,
            runtime=runtime, receipt=receipt, plan=corrupted,
        )
    fast = resolve_motion_set(
        ROOT,
        ROOT / "catalog/motion-sets/tarbosaurus-pin-552-1-adult-grounded.v1.json",
        "fast-walk",
    )
    fast_gait = load_grounded_gait(json.loads(fast.program_profile_bytes))
    substituted, substituted_response = resolve_gait_response(
        assemble_baseline_performance(
            json.loads(style_bytes), json.loads(resolution.neutral_pose_bytes)
        )[0],
        fast_gait,
        baseline["gait_response_policy"],
    )
    substituted = replace(
        substituted,
        canonical_support_anchors=True,
        skin_refinement=True,
    )
    substituted_plan = decorate_plan(
        build_grounded_plan(fast_gait, 2.0), substituted
    )
    substituted_plan["solve_policy"] = solve
    substituted_receipt = deepcopy(receipt)
    substituted_receipt["baseline_performance_resolution"][
        "gait_response"
    ] = substituted_response
    with pytest.raises(ContractError, match="bound gait snapshot"):
        _verify_motion_set_provenance(
            tmp_path, recipe=resolution.recipe, lock=lock,
            runtime=runtime, receipt=substituted_receipt,
            plan=substituted_plan,
        )


@pytest.mark.parametrize("motion", ["walk-start", "walk-stop"])
def test_transition_plan_is_bound_to_packaged_program_snapshot(tmp_path, motion):
    resolution = resolve_motion_set(
        ROOT,
        ROOT / "catalog/motion-sets/tarbosaurus-pin-552-1-adult-grounded.v1.json",
        motion,
    )
    baseline = json.loads(resolution.baseline_bytes)
    style_bytes = (ROOT / baseline["performance_profile"]["path"]).read_bytes()
    performance, assembly = assemble_baseline_performance(
        json.loads(style_bytes), json.loads(resolution.neutral_pose_bytes)
    )
    gait = load_grounded_gait(json.loads(resolution.gait_profile_bytes))
    transition = load_gait_transition(json.loads(resolution.program_profile_bytes))
    performance, gait_receipt = resolve_gait_response(
        performance, gait, baseline["gait_response_policy"]
    )
    solve = baseline["solve_policy"]
    performance = replace(
        performance,
        canonical_support_anchors=solve["canonical_support_anchors"],
        skin_refinement=solve["skin_refinement"],
    )
    plan = decorate_plan(build_transition_plan(transition, gait, 2.0), performance)
    plan["solve_policy"] = solve
    for name, raw in {
        **resolution.payloads,
        "performance-profile.json": style_bytes,
        "neutral-pose-profile.json": resolution.neutral_pose_bytes,
    }.items():
        (tmp_path / name).write_bytes(raw)
    lock = {"motion_set_resolution": resolution.lock}
    runtime = {"motion_set": resolution.lock["identities"], "solve_policy": solve}
    receipt = {
        "solve_policy": solve,
        "baseline_performance_resolution": {
            "assembly": assembly,
            "gait_response": gait_receipt,
        },
    }
    plan = json.loads(json_bytes(plan))
    _verify_motion_set_provenance(
        tmp_path,
        recipe=resolution.recipe,
        lock=lock,
        runtime=runtime,
        receipt=receipt,
        plan=plan,
    )
    substitutions = {
        "kind": "stop" if transition.kind == "start" else "start",
        "ramp_cycles": 3 if transition.ramp_cycles != 3 else 4,
        "anticipation_seconds": 1.5,
    }
    for field, value in substitutions.items():
        altered = deepcopy(plan)
        altered["transition_parameters"][field] = value
        with pytest.raises(ContractError, match="bound program snapshot"):
            _verify_motion_set_provenance(
                tmp_path,
                recipe=resolution.recipe,
                lock=lock,
                runtime=runtime,
                receipt=receipt,
                plan=altered,
            )
    missing = deepcopy(plan)
    del missing["transition_parameters"]
    with pytest.raises(ContractError, match="bound program snapshot"):
        _verify_motion_set_provenance(
            tmp_path,
            recipe=resolution.recipe,
            lock=lock,
            runtime=runtime,
            receipt=receipt,
            plan=missing,
        )


def test_mutated_returned_resolution_cannot_reach_compilation(tmp_path):
    resolution = resolve_motion_set(
        ROOT,
        ROOT / "catalog/motion-sets/tarbosaurus-pin-552-1-adult-grounded.v1.json",
        "walk",
    )
    resolution.recipe["forward_axis"][0] += 0.1
    with pytest.raises(ContractError, match="mutated before compilation"):
        compile_recipe(
            None,
            root=ROOT,
            output=tmp_path / "candidate",
            interpolation="CUBICSPLINE",
            _motion_set_resolution=resolution,
        )
