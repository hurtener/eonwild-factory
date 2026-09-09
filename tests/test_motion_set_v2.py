from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.io import bind, write_json
from eonwild_motion.factory.motion_set import resolve_motion_set
from eonwild_motion.solve.locomotion_regime_response import _CARRIER_MAPPING


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


def test_v2_resolves_airborne_intent_and_retains_one_grounded_policy_snapshot(tmp_path):
    _documents(tmp_path)
    resolved = resolve_motion_set(tmp_path, tmp_path / "set.json", "sprint")
    assert resolved.recipe["program"] == "airborne_gait"
    assert resolved.locomotion_response_bytes == (
        tmp_path / "intent-resolution.json"
    ).read_bytes()
    assert resolved.payloads["locomotion-response-policy.json"] == (
        tmp_path / "intent-resolution.json"
    ).read_bytes()
    assert resolved.payloads["neutral-support-profile.json"] == (
        tmp_path / "neutral-support.json"
    ).read_bytes()


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
    _documents(tmp_path)
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
