"""Acquired-reference ownership and fail-closed package inputs."""
from __future__ import annotations

import json
from copy import deepcopy

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.acquired_reference import (
    AcquiredReferenceInputs,
    resolve_reference,
    validate_clearance_policy,
)
from eonwild_motion.factory.compiler import (
    _expected_motion_set_provenance_files,
    _grounded_source_query_plan,
    compile_recipe,
)
from eonwild_motion.factory.io import bind, json_bytes, write_json
from eonwild_motion.factory.motion_set import resolve_motion_set
from eonwild_motion.solve.authored_material_contact import AuthoredMaterialContactAdapter
from eonwild_motion.solve.source_motion_query import _thaw
from eonwild_motion.solve.source_motion_query import SourceMotionQuery
from eonwild_motion.solve.performance import Performance
from test_authored_material_contact import _capsule
from test_constant_skin_targets import _inputs
from test_motion_set import _documents
from test_motion_set_v2 import _documents as _documents_v2


def _reference(root):
    (root / "raw.fbx").write_bytes(b"licensed raw source")
    capsule = root / "capsule.json"
    write_json(capsule, {"schema": "eonwild.motion.authored-material-path.v1"})
    descriptor = root / "reference.json"
    write_json(descriptor, {
        "schema": "eonwild.motion.authored-material-reference.v1",
        "id": "publisher.clip.v1",
        "version": 1,
        "source": bind(root, root / "raw.fbx"),
        "capsule": bind(root, capsule),
        "adapter": {
            "model": "authored_material_contact.v1",
            "version": 1,
            "retime_policy": "phase_preserving.v1",
        },
    })
    return descriptor


def test_clearance_policy_rejects_nonfinite_amount():
    policy = {
        "schema": "eonwild.motion.authored-material-clearance-policy.v1",
        "id": "test-clearance.v1",
        "version": 1,
        "model": "body_height_fraction.v1",
        "maximum_clearance_body_heights": float("inf"),
        "classification": "source_backed_engineering_candidate",
    }
    with pytest.raises(ContractError, match="unsupported"):
        validate_clearance_policy(policy)


def test_grounded_intent_packages_detached_acquired_reference(tmp_path):
    baseline, intent, motion_set = _documents_v2(tmp_path)
    baseline["supported_programs"] = ["grounded_gait"]
    policy = tmp_path / "clearance.json"
    write_json(policy, {
        "schema": "eonwild.motion.authored-material-clearance-policy.v1",
        "id": "test-clearance.v1", "version": 1,
        "model": "body_height_fraction.v1",
        "maximum_clearance_body_heights": 0.125,
        "classification": "source_backed_engineering_candidate",
    })
    baseline["locomotion_response_policy"]["regimes"]["grounded"][
        "authored_material_clearance"
    ] = bind(tmp_path, policy)
    write_json(tmp_path / "baseline.json", baseline)
    motion_set["baseline"] = bind(tmp_path, tmp_path / "baseline.json")
    intent["program"] = "grounded_gait"
    descriptor = _reference(tmp_path)
    intent["authored_material_reference"] = bind(tmp_path, descriptor)
    write_json(tmp_path / "intent.json", intent)
    motion_set["motions"][0]["intent"] = bind(tmp_path, tmp_path / "intent.json")
    write_json(tmp_path / "set.json", motion_set)
    resolved = resolve_motion_set(tmp_path, tmp_path / "set.json", "sprint")
    assert resolved.lock["authored_material_reference"]["source_sha256"] == bind(
        tmp_path, tmp_path / "raw.fbx"
    )["sha256"]
    assert set(resolved.payloads) >= {
        "authored-material-reference.json",
        "authored-material-source.bin",
        "authored-material-path.json",
    }
    (tmp_path / "raw.fbx").write_bytes(b"changed")
    assert resolved.payloads["authored-material-source.bin"] == b"licensed raw source"
    write_json(tmp_path / "direct-recipe.json", resolved.recipe)
    with pytest.raises(ContractError, match="requires compile-set provenance"):
        compile_recipe(
            tmp_path / "direct-recipe.json",
            root=tmp_path,
            output=tmp_path / "output",
            interpolation="CUBICSPLINE",
        )


def test_baseline_clearance_policy_is_packaged_without_acquired_intent(tmp_path):
    baseline, intent, motion_set = _documents_v2(tmp_path)
    baseline["supported_programs"] = ["grounded_gait"]
    policy = tmp_path / "clearance.json"
    write_json(policy, {
        "schema": "eonwild.motion.authored-material-clearance-policy.v1",
        "id": "test-clearance.v1", "version": 1,
        "model": "body_height_fraction.v1",
        "maximum_clearance_body_heights": 0.125,
        "classification": "source_backed_engineering_candidate",
    })
    baseline["locomotion_response_policy"]["regimes"]["grounded"][
        "authored_material_clearance"
    ] = bind(tmp_path, policy)
    intent["program"] = "grounded_gait"
    write_json(tmp_path / "baseline.json", baseline)
    write_json(tmp_path / "intent.json", intent)
    motion_set["baseline"] = bind(tmp_path, tmp_path / "baseline.json")
    motion_set["motions"][0]["intent"] = bind(tmp_path, tmp_path / "intent.json")
    write_json(tmp_path / "set.json", motion_set)
    resolved = resolve_motion_set(tmp_path, tmp_path / "set.json", "sprint")
    assert "authored-material-clearance-policy.json" in resolved.payloads
    assert "authored_material_reference" not in resolved.lock


def test_reference_rejects_changed_source_and_unknown_adapter(tmp_path):
    descriptor = _reference(tmp_path)
    binding = bind(tmp_path, descriptor)
    (tmp_path / "raw.fbx").write_bytes(b"changed")
    with pytest.raises(ContractError, match="hash mismatch"):
        resolve_reference(tmp_path, binding)
    _reference(tmp_path)
    value = json.loads(descriptor.read_text())
    value["adapter"]["retime_policy"] = "fit-output.v1"
    write_json(descriptor, value)
    with pytest.raises(ContractError, match="unsupported"):
        resolve_reference(tmp_path, bind(tmp_path, descriptor))


def test_packaged_reference_rejects_descriptor_payload_split(tmp_path):
    descriptor = _reference(tmp_path)
    with pytest.raises(ContractError, match="descriptor snapshot"):
        AcquiredReferenceInputs(
            descriptor_bytes=descriptor.read_bytes(),
            source_bytes=b"substituted source",
            capsule_bytes=(tmp_path / "capsule.json").read_bytes(),
        )


def test_transition_cannot_silently_drop_acquired_reference(tmp_path):
    _, intent, motion_set = _documents(tmp_path)
    intent.update({
        "program": "gait_transition",
        "gait_profile": bind(tmp_path, tmp_path / "program.json"),
        "authored_material_reference": bind(tmp_path, _reference(tmp_path)),
    })
    write_json(tmp_path / "intent.json", intent)
    motion_set["motions"][0]["intent"] = bind(tmp_path, tmp_path / "intent.json")
    write_json(tmp_path / "set.json", motion_set)
    with pytest.raises(ContractError, match="only for steady grounded gait"):
        resolve_motion_set(tmp_path, tmp_path / "set.json", "walk")


def test_adapter_binding_is_detached_json_payload():
    inputs = _inputs()
    policy = {
        "schema": "eonwild.motion.authored-material-clearance-policy.v1",
        "id": "test-clearance.v1", "version": 1,
        "model": "body_height_fraction.v1",
        "maximum_clearance_body_heights": 0.125,
        "classification": "source_backed_engineering_candidate",
    }
    adapter = AuthoredMaterialContactAdapter.build(
        inputs["query"], _capsule(), authored_source=b"source",
        body_height_m=inputs["query"]._context.body_height,
        material_clearance_policy=policy,
    )
    payload = _thaw(adapter.binding())
    assert json.loads(json_bytes(payload))["material_clearance_policy"] == policy


def test_original_query_plan_replays_independently_of_emitted_rows():
    inputs = _inputs()
    solve_policy = {
        "schema": "eonwild.motion.solve-policy.v1",
        "representation": "CUBICSPLINE",
        "canonical_support_anchors": True,
        "skin_target_law": "canonical_constant_skin_targets.v1",
        "skin_refinement": True,
    }
    kwargs = dict(
        gait=inputs["locomotion_gait"],
        body_height_m=inputs["query"]._context.body_height,
        performance=Performance(canonical_support_anchors=True),
        roles=inputs["semantic_roles"],
        contact_profile=inputs["contact_profile"],
        forward=inputs["forward_axis"], up=inputs["up_axis"],
        solve_policy=solve_policy,
    )
    original = _grounded_source_query_plan(inputs["source"], **kwargs)
    emitted = deepcopy(original)
    emitted["samples"][1]["feet"]["left"]["height_m"] += 0.01
    replay = _grounded_source_query_plan(inputs["source"], **kwargs)
    assert replay == original
    assert replay != emitted
    query_kwargs = dict(
        semantic_roles=inputs["semantic_roles"],
        solver_gait=inputs["solver_gait"],
        locomotion_gait=inputs["locomotion_gait"],
        plan=original,
        contact_profile=inputs["contact_profile"],
        up_axis=inputs["up_axis"], forward_axis=inputs["forward_axis"],
    )
    original_query = SourceMotionQuery(inputs["source"], **query_kwargs)
    replay_query = SourceMotionQuery(inputs["source"], **dict(query_kwargs, plan=replay))
    policy = {
        "schema": "eonwild.motion.authored-material-clearance-policy.v1",
        "id": "test-clearance.v1", "version": 1,
        "model": "body_height_fraction.v1",
        "maximum_clearance_body_heights": 0.125,
        "classification": "source_backed_engineering_candidate",
    }
    adapter = AuthoredMaterialContactAdapter.build(
        original_query, _capsule(), authored_source=b"source",
        body_height_m=inputs["query"]._context.body_height,
        material_clearance_policy=policy,
    )
    adapter.validate_for_query(replay_query)
    with pytest.raises(ContractError, match="differs from the bound source program"):
        SourceMotionQuery(inputs["source"], **dict(query_kwargs, plan=emitted))


def test_baseline_owned_clearance_policy_is_expected_package_provenance(tmp_path):
    baseline = {
        "schema": "eonwild.motion.motion-baseline.v2",
        "locomotion_response_policy": {"regimes": {"grounded": {
            "authored_material_clearance": {"path": "policy.json", "sha256": "0" * 64}
        }}},
    }
    files = _expected_motion_set_provenance_files(
        tmp_path, baseline, {"program": "grounded_gait"}
    )
    assert "authored-material-clearance-policy.json" in files
    assert "authored-material-reference.json" not in files
