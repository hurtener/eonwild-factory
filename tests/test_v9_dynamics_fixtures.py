"""V9 dynamics slice on REAL fixture profiles (no 2-segment toys).

Proves the centroidal / ballistic / capacity path on the admitted fixture
documents:

* ``profiles/v9/synthetic-heavy-biped.json`` — absolute, 1500 kg,
  ``fixture_absolute_allowed``.
* ``profiles/v9/tarbosaurus-provisional.json`` — normalized, physics
  unevaluated.
* Rig ``catalog/rigs/hero-theropod-v8_3.semantic-rig.json`` (fallback
  ``profiles/v9/rig.airborne-jaw-breathing.json``) supplies Bone names only;
  the segment-role -> node binding is explicit data below (no species
  branching).

Deterministic: no randomness, no timestamps.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.contracts.v9_models import BodyInstanceProfile
from eonwild_motion.dynamics.capacity import CapacityProfile
from eonwild_motion.dynamics.centroidal import (
    bind_profile_segments,
    compute_centroidal_series,
    fk_world_frames,
)
from eonwild_motion.dynamics.contact_authority import evaluate_contact_authority
from eonwild_motion.planning.power_attack import PowerAttackRequest, plan_power_attack
from eonwild_motion.solve.airborne_gait import evaluate_airborne_skin

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_PATH = REPO_ROOT / "profiles/v9/synthetic-heavy-biped.json"
TARBOSAURUS_PATH = REPO_ROOT / "profiles/v9/tarbosaurus-provisional.json"
CATALOG_RIG_PATH = REPO_ROOT / "catalog/rigs/hero-theropod-v8_3.semantic-rig.json"
PROFILE_RIG_PATH = REPO_ROOT / "profiles/v9/rig.airborne-jaw-breathing.json"

# Tarbosaurus provisional has null dimensions; inertia scaling needs a
# positive characteristic height. Use the fixture hip height (2.15 m) as an
# explicit provisional engineering assumption. COM position and linear
# momentum are unaffected (height only scales I = diag * M * H^2).
PROVISIONAL_CHARACTERISTIC_HEIGHT_M = 2.15

# Realistic running takeoff: horizontal speed carried in (preload), stance
# only generates the vertical impulse — the economical predator launch.
# Landing XZ is exactly vx*T analytic so the target-hit gate passes.
LAUNCH_COM_M = (0.0, 2.0, 0.0)
LAUNCH_VELOCITY_MPS = (4.5, 2.5, 0.0)
PRELOAD_VELOCITY_MPS = (4.5, 0.0, 0.0)
LANDING_COM_M = (2.7448, 1.7, 0.0)

# Absurd launch on an exactly-hit far target: far beyond the provisional
# force/friction/power envelope, so the fallback must name the capacity.
BRUTAL_VELOCITY_MPS = (14.0, 9.0, 0.0)
BRUTAL_LANDING_COM_M = (26.145, 1.7, 0.0)


def _load_profile(path: Path) -> tuple[dict, BodyInstanceProfile]:
    document = json.loads(path.read_text(encoding="utf-8"))
    return document, BodyInstanceProfile.from_document(document)


def _load_rig() -> tuple[dict, dict, str]:
    # Prefer the catalog rig when present; both files share the same Bone
    # vocabulary and role layout.
    path = CATALOG_RIG_PATH if CATALOG_RIG_PATH.is_file() else PROFILE_RIG_PATH
    document = json.loads(path.read_text(encoding="utf-8"))
    return document, dict(document["roles"]), str(path.relative_to(REPO_ROOT))


def _synthetic_segment_to_node(roles: dict) -> dict[str, str]:
    """Explicit segment-id -> Bone binding for the synthetic fixture.

    Forelimb segments have no forelimb chain in the rig vocabulary, so they
    bind to the chest node as carried mass (documented here, not branched).
    """
    return {
        "pelvis": roles["pelvis"],
        "abdomen": roles["spine"][2],
        "thorax": roles["chest"],
        "neck_base": roles["neck"][0],
        "neck_distal": roles["neck"][2],
        "head": roles["head"],
        "tail_base": roles["tail"][0],
        "tail_mid": roles["tail"][4],
        "tail_distal": roles["tail"][-1],
        "thigh_l": roles["legs"]["left"]["contactChain"][0],
        "thigh_r": roles["legs"]["right"]["contactChain"][0],
        "lower_leg_l": roles["legs"]["left"]["contactChain"][1],
        "lower_leg_r": roles["legs"]["right"]["contactChain"][1],
        "foot_l": roles["leftFoot"],
        "foot_r": roles["rightFoot"],
        "forelimb_l": roles["chest"],
        "forelimb_r": roles["chest"],
    }


def _tarbosaurus_segment_to_node(roles: dict) -> dict[str, str]:
    """Explicit segment-id -> Bone binding for the provisional Tarbosaurus."""
    return {
        "pelvis": roles["pelvis"],
        "trunk": roles["spine"][2],
        "chest": roles["chest"],
        "neck": roles["neck"][2],
        "head": roles["head"],
        "tail_01": roles["tail"][0],
        "tail_02": roles["tail"][2],
        "tail_03": roles["tail"][5],
        "tail_04": roles["tail"][-1],
        "thigh_l": roles["legs"]["left"]["contactChain"][0],
        "thigh_r": roles["legs"]["right"]["contactChain"][0],
        "shin_l": roles["legs"]["left"]["contactChain"][1],
        "shin_r": roles["legs"]["right"]["contactChain"][1],
        "foot_l": roles["leftFoot"],
        "foot_r": roles["rightFoot"],
        "forelimb_l": roles["chest"],
        "forelimb_r": roles["chest"],
    }


def _name_to_node(segment_to_node: dict[str, str], roles: dict) -> dict[str, int]:
    # Deterministic order: root first, remaining Bones sorted. The FK star
    # below needs parents ordered before children; bindings may share nodes.
    unique = sorted(set(segment_to_node.values()) | {roles["root"]})
    unique.remove(roles["root"])
    ordered = [roles["root"]] + unique
    return {name: index for index, name in enumerate(ordered)}


def _binding_dicts(profile: BodyInstanceProfile) -> list[dict]:
    return [
        {
            "id": segment.id,
            "mass_fraction": segment.mass_fraction,
            "inertia_diagonal_normalized": list(segment.inertia_diagonal_normalized),
        }
        for segment in profile.segments
    ]


def _characteristic_height(profile: BodyInstanceProfile) -> float:
    height = profile.dimensions.get("hip_height_m")
    if height is None:
        return PROVISIONAL_CHARACTERISTIC_HEIGHT_M
    return float(height)


def test_fixture_profiles_bind_all_17_segments():
    _, synthetic = _load_profile(SYNTHETIC_PATH)
    _, tarbosaurus = _load_profile(TARBOSAURUS_PATH)
    _, roles, rig_source = _load_rig()
    assert rig_source in (
        "catalog/rigs/hero-theropod-v8_3.semantic-rig.json",
        "profiles/v9/rig.airborne-jaw-breathing.json",
    )

    # Admission facts from the real documents.
    assert synthetic.profile_id == "synthetic_heavy_biped_fixture_v1"
    assert synthetic.total_mass_kg == pytest.approx(1500.0)
    assert synthetic.absolute_dynamics_enabled is True
    assert synthetic.mass_mode == "absolute"
    assert synthetic.absolute_policy == "fixture_absolute_allowed"
    assert len(synthetic.segments) == 17

    assert tarbosaurus.profile_id == "tarbosaurus_provisional_normalized_v1"
    assert tarbosaurus.total_mass_kg is None
    assert tarbosaurus.absolute_dynamics_enabled is False
    assert tarbosaurus.mass_mode == "normalized"
    assert len(tarbosaurus.segments) == 17

    synthetic_map = _synthetic_segment_to_node(roles)
    tarbosaurus_map = _tarbosaurus_segment_to_node(roles)
    assert len(synthetic_map) == 17 and len(tarbosaurus_map) == 17
    # Every bound Bone must exist in the rig vocabulary (binding is data).
    rig_bones: set[str] = set()
    for value in roles.values():
        if isinstance(value, str):
            rig_bones.add(value)
        elif isinstance(value, list):
            rig_bones.update(v for v in value if isinstance(v, str))
        elif isinstance(value, dict):
            for nested in value.values():
                if isinstance(nested, str):
                    rig_bones.add(nested)
                elif isinstance(nested, dict):
                    for chain in nested.values():
                        if isinstance(chain, list):
                            for item in chain:
                                if isinstance(item, str):
                                    rig_bones.add(item)
                                elif isinstance(item, list):
                                    rig_bones.update(item)
    for node in list(synthetic_map.values()) + list(tarbosaurus_map.values()):
        assert node in rig_bones

    synthetic_bindings = bind_profile_segments(
        _binding_dicts(synthetic),
        name_to_node=_name_to_node(synthetic_map, roles),
        segment_to_node=synthetic_map,
        total_mass_kg=synthetic.total_mass_kg,
        characteristic_height_m=_characteristic_height(synthetic),
        absolute_dynamics_enabled=synthetic.absolute_dynamics_enabled,
    )
    tarbosaurus_bindings = bind_profile_segments(
        _binding_dicts(tarbosaurus),
        name_to_node=_name_to_node(tarbosaurus_map, roles),
        segment_to_node=tarbosaurus_map,
        total_mass_kg=tarbosaurus.total_mass_kg,
        characteristic_height_m=_characteristic_height(tarbosaurus),
        absolute_dynamics_enabled=tarbosaurus.absolute_dynamics_enabled,
    )
    assert len(synthetic_bindings) == 17
    assert len(tarbosaurus_bindings) == 17
    assert sum(b.mass_kg for b in synthetic_bindings) == pytest.approx(1500.0)
    # Normalized profile binds mass fractions (total 1.0).
    assert sum(b.mass_kg for b in tarbosaurus_bindings) == pytest.approx(1.0)


def test_synthetic_running_takeoff_is_airborne_with_physics():
    _, synthetic = _load_profile(SYNTHETIC_PATH)
    capacity = CapacityProfile(profile_id="fixture_provisional_v1")
    receipt = plan_power_attack(
        PowerAttackRequest(
            body=synthetic,
            capacity=capacity,
            launch_com_m=LAUNCH_COM_M,
            launch_velocity_mps=LAUNCH_VELOCITY_MPS,
            preload_velocity_mps=PRELOAD_VELOCITY_MPS,
            landing_com_m=LANDING_COM_M,
        )
    )
    assert receipt["variant"] == "airborne"
    assert receipt["physics_evaluated"] is True
    assert receipt["takeoff"]["verdict"] == "PASS"
    assert receipt["landing"]["verdict"] == "PASS"
    assert receipt["takeoff_impulse_ns"] == pytest.approx([0.0, 3750.0, 0.0])
    assert receipt["flight_time_s"] == pytest.approx(0.6099568011384792)
    # Margins that prove the gate actually measured something (mean GRF
    # includes body weight; landing crouch owns vertical energy only).
    assert receipt["takeoff"]["required_peak_force_n"] == pytest.approx(42161.78571428571)
    assert receipt["takeoff"]["force_limit_n"] == pytest.approx(51502.5)
    assert receipt["landing"]["required_work_j"] == pytest.approx(17931.0)
    assert receipt["landing"]["absorption_budget_j"] == pytest.approx(35316.0)
    assert receipt["arrest"]["verdict"] == "PASS"
    assert receipt["arrest"]["required_arrest_distance_m"] == pytest.approx(1.290137614678899)


def test_tarbosaurus_normalized_yields_airborne_normalized():
    _, tarbosaurus = _load_profile(TARBOSAURUS_PATH)
    capacity = CapacityProfile(profile_id="fixture_provisional_v1")
    receipt = plan_power_attack(
        PowerAttackRequest(
            body=tarbosaurus,
            capacity=capacity,
            launch_com_m=LAUNCH_COM_M,
            launch_velocity_mps=LAUNCH_VELOCITY_MPS,
            preload_velocity_mps=PRELOAD_VELOCITY_MPS,
            landing_com_m=LANDING_COM_M,
        )
    )
    assert receipt["variant"] == "airborne_normalized"
    assert receipt["physics_evaluated"] is False
    assert receipt["takeoff"] is None and receipt["landing"] is None
    assert receipt["takeoff_impulse_ns"] is None
    assert receipt["limiting_factor"] is None


def test_absurd_launch_falls_back_to_grounded_lunge():
    _, synthetic = _load_profile(SYNTHETIC_PATH)
    capacity = CapacityProfile(profile_id="fixture_provisional_v1")
    receipt = plan_power_attack(
        PowerAttackRequest(
            body=synthetic,
            capacity=capacity,
            launch_com_m=LAUNCH_COM_M,
            launch_velocity_mps=BRUTAL_VELOCITY_MPS,
            landing_com_m=BRUTAL_LANDING_COM_M,
        )
    )
    assert receipt["variant"] == "grounded_lunge"
    assert receipt["limiting_factor"] == "takeoff.force_ok"


def test_centroidal_rigid_translation_gives_p_equals_m_v():
    _, synthetic = _load_profile(SYNTHETIC_PATH)
    _, roles, _ = _load_rig()
    segment_to_node = _synthetic_segment_to_node(roles)
    name_to_node = _name_to_node(segment_to_node, roles)
    bindings = bind_profile_segments(
        _binding_dicts(synthetic),
        name_to_node=name_to_node,
        segment_to_node=segment_to_node,
        total_mass_kg=synthetic.total_mass_kg,
        characteristic_height_m=_characteristic_height(synthetic),
        absolute_dynamics_enabled=synthetic.absolute_dynamics_enabled,
    )
    node_count = len(name_to_node)
    parents: list[int | None] = [None] + [0] * (node_count - 1)
    rest_translations = [[0.0, 0.0, 0.0]] + [
        [0.1 * i, 0.05 * i, 0.02 * i] for i in range(1, node_count)
    ]
    rest_rotations = [(0.0, 0.0, 0.0, 1.0)] * node_count
    velocity = np.array([1.5, 0.0, -2.0])
    times = [0.0, 0.1, 0.2]
    world_positions: list[np.ndarray] = []
    world_rotations: list[np.ndarray] = []
    for t in times:
        local_translations = [list(row) for row in rest_translations]
        local_translations[0] = list(np.array(rest_translations[0]) + velocity * t)
        pos, rot = fk_world_frames(
            parents,
            rest_translations,
            rest_rotations,
            local_translations=local_translations,
            local_rotations=list(rest_rotations),
        )
        world_positions.append(pos)
        world_rotations.append(rot)
    series = compute_centroidal_series(
        bindings,
        times_s=times,
        world_positions=world_positions,
        world_rotations=world_rotations,
        mass_mode="absolute",
    )
    assert len(series) == 3
    expected = tuple(float(v) for v in 1500.0 * velocity)
    for sample in series:
        assert sample.total_mass_kg == pytest.approx(1500.0)
        assert sample.linear_momentum_kg_mps == pytest.approx(expected)
        assert sample.mass_mode == "absolute"


def test_contact_authority_wiring_is_additive_and_fail_closed():
    # The engine path exposes the persistent ground-plane verdict opt-in;
    # default-off keeps existing receipts byte-identical.
    signature = inspect.signature(evaluate_airborne_skin)
    assert "include_contact_authority" in signature.parameters
    assert signature.parameters["include_contact_authority"].default is False
    # Persistent semantics: loaded-but-lifted is unknown contact (FAIL),
    # never a zero-skate pass.
    from eonwild_motion.dynamics.contact_authority import PatchFrame

    def _frames(gap: float):
        return [
            PatchFrame(
                time_s=i / 120.0,
                sole_m=((0.0, gap, 0.10), (0.0, gap, -0.10)),
                toe_m=((0.12, gap, 0.05), (0.12, gap, -0.05)),
            )
            for i in range(4)
        ]

    assert evaluate_contact_authority(_frames(0.0002), [True] * 4)["verdict"] == "PASS"
    assert evaluate_contact_authority(_frames(0.05), [True] * 4)["verdict"] == "FAIL"
