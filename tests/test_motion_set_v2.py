from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.animal import (
    apply_uniform_geometry_scale,
    load_animal_instance,
    scaled_contact_profile,
    verify_source_calibration,
)
from eonwild_motion.factory.compiler import (
    _measure_bound_grounded_touchdown_geometry,
    _verify_motion_set_provenance,
)
from eonwild_motion.factory.io import bind, write_json
from eonwild_motion.factory.motion_set import (
    resolve_motion_set,
    resolve_motion_set_selection,
)
from eonwild_motion.factory.source import geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.articulation_profile import load_articulation_profile
from eonwild_motion.planning.grounded_gait import build_grounded_plan, load_grounded_gait
from eonwild_motion.planning.grounded_intent_resolution import resolve_grounded_intent
from eonwild_motion.solve.gait_response import (
    assemble_baseline_performance,
    resolve_gait_response,
)
from eonwild_motion.solve.locomotion_regime_response import _CARRIER_MAPPING
from eonwild_motion.solve.performance import decorate_plan


ROOT = Path(__file__).resolve().parents[1]


def _airborne_policy():
    return {
        "schema": "eonwild.motion.airborne-body-response.v1",
        "model": "explicit_contact_flight_coordination.v1",
        "carrier_mapping": dict(_CARRIER_MAPPING),
        "forward_speed": {
            "model": "reference_scaled_support_exchange.v1",
            "reference_speed_body_heights_per_s": 2.0,
            "reference_pelvis_forward_velocity_modulation_fraction": 0.08,
        },
    }


def _documents(root: Path):
    for name in (
        "source.glb", "rig.json", "animal.json", "contact.json",
        "articulation.json", "performance.json", "program.json",
    ):
        (root / name).write_text(name)
    (root / "neutral.json").write_bytes(
        (ROOT / "catalog/calibration/tarbosaurus-pin-552-1-adult-neutral.v1.json").read_bytes()
    )
    write_json(
        root / "intent-resolution.json",
        {
            "schema": "eonwild.motion.locomotion-response-policy.v1",
            "id": "family-grounded-reference.v1",
            "version": 1,
            "grounded_intent_resolution": {},
        },
    )
    write_json(
        root / "neutral-support.json",
        {"schema": "eonwild.motion.neutral-support-geometry.v1"},
    )
    response = {
        "schema": "eonwild.motion.motion-set-locomotion-response.v1",
        "regimes": {
            "grounded": {
                "intent_resolution": bind(root, root / "intent-resolution.json"),
                "neutral_support_profile": bind(root, root / "neutral-support.json"),
                "body_response": {
                    "model": "existing_grounded_shared_style.v1",
                    "gait_response": {
                        "schema": "eonwild.motion.gait-response-policy.v1",
                        "model": "reference_scaled_excursion_exchange.v1",
                        "reference": {
                            "step_period_s": 1.23,
                            "step_length_body_heights": 0.6,
                            "pelvis_excursion_body_heights": 0.016,
                            "pelvis_forward_velocity_modulation_fraction": 0.145,
                        },
                    },
                },
            },
            "airborne": {
                "intent_resolution": {
                    "model": "airborne_choreography_passthrough.v1"
                },
                "body_response": _airborne_policy(),
            },
        },
    }
    baseline = {
        "schema": "eonwild.motion.motion-baseline.v2",
        "id": "animal.locomotion.v2",
        "version": 2,
        "family": "portable-biped",
        **{
            key: bind(root, root / name)
            for key, name in {
                "source": "source.glb",
                "rig": "rig.json",
                "animal": "animal.json",
                "contact_profile": "contact.json",
                "articulation_profile": "articulation.json",
                "performance_profile": "performance.json",
                "neutral_pose_profile": "neutral.json",
            }.items()
        },
        "forward_axis": [0.0, 0.0, 1.0],
        "up_axis": [0.0, 1.0, 0.0],
        "supported_programs": ["grounded_gait", "gait_transition", "airborne_gait"],
        "locomotion_response_policy": response,
        "solve_policy": {
            "schema": "eonwild.motion.solve-policy.v1",
            "representation": "CUBICSPLINE",
            "canonical_support_anchors": True,
            "skin_target_law": "canonical_constant_skin_targets.v1",
            "skin_refinement": True,
        },
    }
    intent = {
        "schema": "eonwild.motion.motion-intent.v2",
        "id": "portable-biped.sprint.v2",
        "version": 2,
        "program": "airborne_gait",
        "program_profile": bind(root, root / "program.json"),
        "description": "portable event choreography",
    }
    write_json(root / "baseline.json", baseline)
    write_json(root / "intent.json", intent)
    motion_set = {
        "schema": "eonwild.motion.motion-set.v2",
        "id": "animal.motion-set.v2",
        "version": 2,
        "baseline": bind(root, root / "baseline.json"),
        "motions": [{"name": "sprint", "intent": bind(root, root / "intent.json")}],
    }
    write_json(root / "set.json", motion_set)
    return baseline, intent, motion_set


def test_v2_rejects_airborne_until_source_bound_recovery_provider_exists(tmp_path):
    _documents(tmp_path)
    with pytest.raises(ContractError, match="unsupported or repeated capabilities"):
        resolve_motion_set(tmp_path, tmp_path / "set.json", "sprint")


@pytest.mark.parametrize(
    "mutation",
    ["intent-body", "mixed-intent", "mixed-set", "missing-carrier", "changed-model"],
)
def test_v2_rejects_body_override_schema_mix_or_incomplete_response(tmp_path, mutation):
    baseline, intent, motion_set = _documents(tmp_path)
    if mutation == "intent-body":
        intent["performance_profile"] = baseline["performance_profile"]
        write_json(tmp_path / "intent.json", intent)
        motion_set["motions"][0]["intent"] = bind(tmp_path, tmp_path / "intent.json")
    elif mutation == "mixed-intent":
        intent["schema"] = "eonwild.motion.motion-intent.v1"
        write_json(tmp_path / "intent.json", intent)
        motion_set["motions"][0]["intent"] = bind(tmp_path, tmp_path / "intent.json")
    elif mutation == "mixed-set":
        motion_set["schema"] = "eonwild.motion.motion-set.v1"
    elif mutation == "missing-carrier":
        baseline["locomotion_response_policy"]["regimes"]["airborne"][
            "body_response"
        ]["carrier_mapping"].pop("pelvis_roll")
        write_json(tmp_path / "baseline.json", baseline)
        motion_set["baseline"] = bind(tmp_path, tmp_path / "baseline.json")
    else:
        baseline["locomotion_response_policy"]["regimes"]["grounded"][
            "body_response"
        ]["model"] = "changed"
        write_json(tmp_path / "baseline.json", baseline)
        motion_set["baseline"] = bind(tmp_path, tmp_path / "baseline.json")
    write_json(tmp_path / "set.json", motion_set)
    with pytest.raises(ContractError):
        resolve_motion_set(tmp_path, tmp_path / "set.json", "sprint")


def test_v2_returned_policy_and_payload_are_detached(tmp_path):
    baseline, intent, motion_set = _documents(tmp_path)
    baseline["supported_programs"] = ["grounded_gait"]
    intent["program"] = "grounded_gait"
    write_json(tmp_path / "baseline.json", baseline)
    motion_set["baseline"] = bind(tmp_path, tmp_path / "baseline.json")
    write_json(tmp_path / "intent.json", intent)
    motion_set["motions"][0]["intent"] = bind(tmp_path, tmp_path / "intent.json")
    write_json(tmp_path / "set.json", motion_set)
    resolved = resolve_motion_set(tmp_path, tmp_path / "set.json", "sprint")
    policy = resolved.locomotion_response_policy
    assert policy is not None
    changed = deepcopy(policy)
    changed["regimes"]["airborne"]["body_response"]["model"] = "changed"
    assert resolved.locomotion_response_policy["regimes"]["airborne"][
        "body_response"
    ]["model"] == "explicit_contact_flight_coordination.v1"


def test_real_v2_grounded_sets_share_inputs_without_changing_v1_recipe():
    tarbo_v1 = resolve_motion_set(
        ROOT,
        ROOT / "catalog/motion-sets/tarbosaurus-pin-552-1-adult-grounded.v1.json",
        "walk",
    )
    tarbo_v2 = resolve_motion_set(
        ROOT,
        ROOT / "catalog/motion-sets/tarbosaurus-pin-552-1-adult-locomotion.v2.json",
        "walk",
    )
    allo_v2 = resolve_motion_set(
        ROOT,
        ROOT / "catalog/motion-sets/allosaurus-engineering-locomotion.v2.json",
        "walk-diagnostic",
    )
    for field in (
        "source", "rig", "animal", "contact_profile", "articulation_profile",
        "performance_profile", "program_profile",
    ):
        assert tarbo_v2.recipe[field] == tarbo_v1.recipe[field]
    assert tarbo_v1.recipe == resolve_motion_set(
        ROOT,
        ROOT / "catalog/motion-sets/tarbosaurus-pin-552-1-adult-grounded.v1.json",
        "walk",
    ).recipe
    assert tarbo_v2.neutral_support_bytes != allo_v2.neutral_support_bytes
    assert (
        tarbo_v2.locomotion_response_bytes
        == allo_v2.locomotion_response_bytes
    )
    assert json.loads(tarbo_v2.baseline_bytes)["supported_programs"] == [
        "grounded_gait", "gait_transition"
    ]


def test_allosaurus_acquired_fast_walk_changes_only_portable_gait_intent():
    motion_set = (
        ROOT
        / "catalog/motion-sets/allosaurus-engineering-acquired-fast-walk-diagnostic.v1.json"
    )
    walk, fast = resolve_motion_set_selection(
        ROOT, motion_set, ["walk", "fast-walk"]
    )
    assert walk.baseline_bytes == fast.baseline_bytes
    assert walk.baseline_binding == fast.baseline_binding
    for field in (
        "source",
        "rig",
        "animal",
        "contact_profile",
        "articulation_profile",
        "performance_profile",
    ):
        assert walk.recipe[field] == fast.recipe[field]
    assert walk.acquired_reference is not None
    assert fast.acquired_reference is not None
    assert walk.acquired_reference.binding == fast.acquired_reference.binding
    assert set(json.loads(fast.intent_bytes)) == {
        "schema",
        "id",
        "version",
        "program",
        "program_profile",
        "authored_material_reference",
        "description",
    }
    gait = load_grounded_gait(json.loads(fast.program_profile_bytes))
    assert gait.step_period_s == 0.8
    assert gait.duty_factor == 0.62
    assert gait.step_length_body_heights == 0.6
    assert gait.pelvis_height_carrier == "stance_vault_proxy"


def test_v2_provenance_remeasures_touchdown_geometry_from_source(tmp_path):
    resolution = resolve_motion_set(
        ROOT,
        ROOT / "catalog/motion-sets/allosaurus-engineering-locomotion.v2.json",
        "walk-diagnostic",
    )
    baseline = json.loads(resolution.baseline_bytes)
    source_bytes = (ROOT / baseline["source"]["path"]).read_bytes()
    rig_bytes = (ROOT / baseline["rig"]["path"]).read_bytes()
    contact_bytes = (ROOT / baseline["contact_profile"]["path"]).read_bytes()
    animal_bytes = (ROOT / baseline["animal"]["path"]).read_bytes()
    articulation_bytes = (
        ROOT / baseline["articulation_profile"]["path"]
    ).read_bytes()
    style_bytes = (ROOT / baseline["performance_profile"]["path"]).read_bytes()
    source = Glb.from_bytes(source_bytes)
    roles = json.loads(rig_bytes)["roles"]
    contact = json.loads(contact_bytes)
    animal = load_animal_instance(
        json.loads(animal_bytes),
        source_sha256=resolution.recipe["source"]["sha256"],
    )
    forward = np.asarray((0.0, 0.0, 1.0))
    up = np.asarray((0.0, 1.0, 0.0))
    verify_source_calibration(animal, source, roles, contact, forward, up)
    apply_uniform_geometry_scale(source, animal["uniform_scale"])
    contact = scaled_contact_profile(contact, animal["uniform_scale"])
    height = geometry_height(source, roles, up)
    authored = load_grounded_gait(json.loads(resolution.program_profile_bytes))
    performance, assembly = assemble_baseline_performance(
        json.loads(style_bytes), json.loads(resolution.neutral_pose_bytes)
    )
    grounded_policy = baseline["locomotion_response_policy"]["regimes"]["grounded"]
    geometry = _measure_bound_grounded_touchdown_geometry(
        source,
        roles=roles,
        contact_profile=contact,
        locomotion_gait=authored,
        articulation_profile=load_articulation_profile(
            json.loads(articulation_bytes)
        ),
        performance=performance,
        gait_response_policy=grounded_policy["body_response"]["gait_response"],
        source_geometry_sha256=resolution.recipe["source"]["sha256"],
        body_height_m=height,
        up=up,
        forward=forward,
    )
    support = json.loads(resolution.neutral_support_bytes)
    policy = json.loads(resolution.locomotion_response_bytes)

    def package_state(touchdown_geometry):
        resolved = resolve_grounded_intent(
            authored,
            body_height_m=height,
            animal_hindlimb_length_m=animal["hindlimb_length_m"],
            source_geometry_sha256=resolution.recipe["source"]["sha256"],
            neutral_support_geometry=support,
            family_policy=policy,
            touchdown_geometry=touchdown_geometry,
        )
        effective, gait_receipt = resolve_gait_response(
            performance,
            resolved.gait,
            grounded_policy["body_response"]["gait_response"],
        )
        solve = baseline["solve_policy"]
        effective = replace(
            effective,
            canonical_support_anchors=solve["canonical_support_anchors"],
            skin_refinement=solve["skin_refinement"],
        )
        plan = decorate_plan(build_grounded_plan(resolved.gait, height), effective)
        plan["solve_policy"] = solve
        receipt = {
            "solve_policy": solve,
            "baseline_performance_resolution": {
                "assembly": assembly,
                "gait_response": gait_receipt,
                "grounded_intent": resolved.receipt(),
            },
        }
        return json.loads(json.dumps(plan)), receipt

    for name, raw in {
        **resolution.payloads,
        "performance-profile.json": style_bytes,
        "neutral-pose-profile.json": resolution.neutral_pose_bytes,
        "source.glb": source_bytes,
        "rig.json": rig_bytes,
        "contact-profile.json": contact_bytes,
        "animal.json": animal_bytes,
        "articulation-profile.json": articulation_bytes,
    }.items():
        (tmp_path / name).write_bytes(raw)
    (tmp_path / "grounded-touchdown-geometry.json").write_text(
        json.dumps(geometry)
    )
    plan, receipt = package_state(geometry)
    common = {
        "recipe": resolution.recipe,
        "lock": {"motion_set_resolution": resolution.lock},
        "runtime": {
            "motion_set": resolution.lock["identities"],
            "solve_policy": baseline["solve_policy"],
        },
    }
    _verify_motion_set_provenance(
        tmp_path, receipt=receipt, plan=plan, **common
    )
    altered = deepcopy(geometry)
    altered["sides"]["right"]["zero_step_ankle_from_hip_m"][2] += 0.02
    (tmp_path / "grounded-touchdown-geometry.json").write_text(
        json.dumps(altered)
    )
    altered_plan, altered_receipt = package_state(altered)
    with pytest.raises(ContractError, match="source authority"):
        _verify_motion_set_provenance(
            tmp_path,
            receipt=altered_receipt,
            plan=altered_plan,
            **common,
        )
