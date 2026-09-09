from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.source import geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.airborne_gait import AirborneGait
from eonwild_motion.planning.gait_transition import (
    build_transition_plan,
    load_gait_transition,
)
from eonwild_motion.planning.grounded_gait import (
    build_grounded_plan,
    load_grounded_gait,
    sample_grounded_gait,
)
from eonwild_motion.solve.performance import Performance, decorate_plan, load_performance
from eonwild_motion.solve.support_anchors import CanonicalSupportAnchorProvider
from eonwild_motion.solve.whole_body_gait_transition import _encode


ROOT = Path(__file__).resolve().parents[1]
WALK_RECIPE = ROOT / "recipes/heavy-biped/walk.v3.json"
START_PROFILE = ROOT / "catalog/programs/heavy-biped.start.v2.json"
STOP_PROFILE = ROOT / "catalog/programs/heavy-biped.stop.v2.json"


def _replace_strings(value, names):
    if isinstance(value, dict):
        return {key: _replace_strings(item, names) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_strings(item, names) for item in value]
    return names.get(value, value) if isinstance(value, str) else value


def _bound_walk(*, renamed_frame=False):
    recipe = json.loads(WALK_RECIPE.read_text())
    source = Glb.from_bytes((ROOT / recipe["source"]["path"]).read_bytes())
    roles = json.loads((ROOT / recipe["rig"]["path"]).read_text())["roles"]
    contact = json.loads((ROOT / recipe["contact_profile"]["path"]).read_text())
    forward = (0.0, 0.0, 1.0)
    if renamed_frame:
        document = deepcopy(source.document)
        names = {node["name"]: f"shifted_{node['name']}" for node in document["nodes"]}
        for node in document["nodes"]:
            node["name"] = names[node["name"]]
        root = source.name_to_node[roles["root"]]
        document["nodes"][root]["rotation"] = [
            0.0,
            math.sqrt(0.5),
            0.0,
            math.sqrt(0.5),
        ]
        source = Glb.from_bytes(_encode(document, source.binary))
        roles = _replace_strings(roles, names)
        contact = _replace_strings(contact, names)
        contact["source"]["sha256"] = hashlib.sha256(source.raw).hexdigest()
        forward = (1.0, 0.0, 0.0)
    grounded = load_grounded_gait(
        json.loads((ROOT / recipe["program_profile"]["path"]).read_text())
    )
    solver = AirborneGait(
        step_period_s=grounded.step_period_s,
        cycles=grounded.cycles,
        sample_hz=grounded.sample_hz,
        swing_hip_lift_degrees=grounded.swing_hip_lift_degrees,
    )
    performance = load_performance(
        json.loads((ROOT / recipe["performance_profile"]["path"]).read_text())
    )
    height = geometry_height(source, roles, (0, 1, 0))
    steady = decorate_plan(build_grounded_plan(grounded, height), performance)
    return source, roles, contact, grounded, solver, steady, forward


def _provider(source, roles, contact, grounded, solver, plan, forward, transition=None):
    return CanonicalSupportAnchorProvider.build(
        source,
        semantic_roles=roles,
        solver_gait=solver,
        locomotion_gait=grounded,
        transition=transition,
        plan=plan,
        contact_profile=contact,
        up_axis=(0, 1, 0),
        forward_axis=forward,
    )


def _origin(provider, side):
    return provider.anchor_for(side).material_origin_m


def test_start_steady_stop_share_exact_sustained_touchdown_material_anchors():
    source, roles, contact, grounded, solver, steady, forward = _bound_walk()
    start = load_gait_transition(json.loads(START_PROFILE.read_text()))
    stop = load_gait_transition(json.loads(STOP_PROFILE.read_text()))
    height = float(steady["body_height_m"])
    start_plan = decorate_plan(build_transition_plan(start, grounded, height), load_performance(json.loads((ROOT / json.loads(WALK_RECIPE.read_text())["performance_profile"]["path"]).read_text())))
    stop_plan = decorate_plan(build_transition_plan(stop, grounded, height), load_performance(json.loads((ROOT / json.loads(WALK_RECIPE.read_text())["performance_profile"]["path"]).read_text())))
    providers = (
        _provider(source, roles, contact, grounded, solver, steady, forward),
        _provider(source, roles, contact, grounded, solver, start_plan, forward, start),
        _provider(source, roles, contact, grounded, solver, stop_plan, forward, stop),
    )
    for side, expected_phase in (("left", 0.0), ("right", grounded.step_period_s)):
        assert [provider.anchor_for(side).touchdown_phase_s for provider in providers] == pytest.approx([expected_phase] * 3)
        assert [provider.anchor_for(side).contact_side_convention for provider in providers] == ["right_continuous_touchdown"] * 3
        assert np.array_equal(_origin(providers[0], side), _origin(providers[1], side))
        assert np.array_equal(_origin(providers[0], side), _origin(providers[2], side))
        assert len({provider.anchor_for(side).gait_family_sha256 for provider in providers}) == 1


def test_provider_is_independent_of_shifted_or_nested_active_grid_rows():
    source, roles, contact, grounded, solver, steady, forward = _bound_walk()
    shifted = deepcopy(steady)
    height = float(shifted["body_height_m"])
    shifted["samples"] = [
        sample_grounded_gait(grounded, 0.003 + index / 480, height)
        for index in range(1, 20)
    ]
    # The provider validates the bound law and top-level program identity, not
    # a finite output grid. A candidate refinement still validates its own grid
    # separately before applying any correction.
    baseline = _provider(source, roles, contact, grounded, solver, steady, forward)
    nested = _provider(source, roles, contact, grounded, solver, shifted, forward)
    for side in ("left", "right"):
        assert np.array_equal(_origin(baseline, side), _origin(nested, side))
        assert baseline.anchor_for(side).material_vertex_indices == nested.anchor_for(side).material_vertex_indices


def test_family_identity_and_anchor_exclude_sampling_and_clip_domain_controls():
    source, roles, contact, grounded, solver, steady, forward = _bound_walk()
    changed = replace(grounded, cycles=1, sample_hz=24)
    changed_solver = replace(solver, cycles=1, sample_hz=24)
    changed_plan = decorate_plan(
        build_grounded_plan(changed, float(steady["body_height_m"])),
        load_performance(
            json.loads(
                (ROOT / json.loads(WALK_RECIPE.read_text())["performance_profile"]["path"]).read_text()
            )
        ),
    )
    baseline = _provider(source, roles, contact, grounded, solver, steady, forward)
    sampled = _provider(
        source, roles, contact, changed, changed_solver, changed_plan, forward
    )
    for side in ("left", "right"):
        assert baseline.anchor_for(side).gait_family_sha256 == sampled.anchor_for(side).gait_family_sha256
        assert np.array_equal(_origin(baseline, side), _origin(sampled, side))


def test_provider_uses_semantics_and_declared_frame_after_renaming_and_root_rotation():
    source, roles, contact, grounded, solver, plan, forward = _bound_walk(renamed_frame=True)
    provider = _provider(source, roles, contact, grounded, solver, plan, forward)
    for side in ("left", "right"):
        anchor = provider.anchor_for(side)
        assert anchor.material_origin_m.shape == (len(anchor.material_vertex_indices), 3)
        assert np.isfinite(anchor.material_origin_m).all()
        assert anchor.material_vertex_indices


def test_provider_rejects_transition_contract_mismatch_without_recovering_gait_from_rows():
    source, roles, contact, grounded, solver, steady, forward = _bound_walk()
    transition = load_gait_transition(json.loads(START_PROFILE.read_text()))
    plan = decorate_plan(build_transition_plan(transition, grounded, float(steady["body_height_m"])), load_performance(json.loads((ROOT / json.loads(WALK_RECIPE.read_text())["performance_profile"]["path"]).read_text())))
    plan["transition_contract"]["root_distance_m"] += 0.01
    with pytest.raises(ContractError, match="transition_contract.*differs"):
        _provider(source, roles, contact, grounded, solver, plan, forward, transition)


def test_opt_in_is_typed_and_omitted_performance_payload_stays_absent():
    source, roles, contact, grounded, solver, steady, forward = _bound_walk()
    assert "canonical_support_anchors" not in steady["performance"]
    provider = _provider(source, roles, contact, grounded, solver, steady, forward)
    receipt = provider.receipt()
    assert set(receipt["sides"]) == {"left", "right"}
    for side in ("left", "right"):
        assert receipt["sides"][side]["material_vertex_count"] == len(
            provider.anchor_for(side).material_vertex_indices
        )
    with pytest.raises(ContractError, match="canonical_support_anchors must be boolean"):
        Performance(canonical_support_anchors=1)
    with pytest.raises(ContractError, match="require skin refinement"):
        Performance(canonical_support_anchors=True, skin_refinement=False)
    enabled = decorate_plan(
        build_grounded_plan(grounded, float(steady["body_height_m"])),
        Performance(canonical_support_anchors=True),
    )
    assert enabled["performance"]["canonical_support_anchors"] is True


def _canonical_plan(grounded, height):
    return decorate_plan(
        build_grounded_plan(grounded, height),
        Performance(canonical_support_anchors=True),
    )


def _consume(provider, source, roles, contact, grounded, solver, plan, forward):
    from eonwild_motion.solve.skin_targets import solve_with_skin_targets
    return solve_with_skin_targets(
        source, semantic_roles=roles, gait=solver, up_axis=(0, 1, 0),
        forward_axis=forward, plan=plan, contact_profile=contact, iterations=0,
        canonical_support_anchor_provider=provider,
        canonical_locomotion_gait=grounded,
    )


def test_provider_consumption_binds_ordered_material_request_and_anchor_payload():
    source, roles, contact, grounded, solver, steady, forward = _bound_walk()
    plan = _canonical_plan(grounded, float(steady["body_height_m"]))
    provider = _provider(source, roles, contact, grounded, solver, plan, forward)
    _consume(provider, source, roles, contact, grounded, solver, plan, forward)

    reordered = deepcopy(contact)
    for side in ("left", "right"):
        feet = reordered["geometry"]["feet"][side]
        feet["sole_joints"], feet["toe_joints"] = feet["toe_joints"], feet["sole_joints"]
    wrong_order = _provider(source, roles, reordered, grounded, solver, plan, forward)
    with pytest.raises(ContractError, match="consuming request|material correspondence"):
        _consume(wrong_order, source, roles, contact, grounded, solver, plan, forward)

    provider._anchors["left"].material_origin_m.setflags(write=True)
    provider._anchors["left"].material_origin_m[0, 0] += .01
    with pytest.raises(ContractError, match="payload differs"):
        _consume(provider, source, roles, contact, grounded, solver, plan, forward)


def test_provider_requires_matching_bound_solver_and_explicit_opt_in_context():
    source, roles, contact, grounded, solver, steady, forward = _bound_walk()
    plan = _canonical_plan(grounded, float(steady["body_height_m"]))
    provider = _provider(source, roles, contact, grounded, solver, plan, forward)
    with pytest.raises(ContractError, match="require a bound provider"):
        _consume(None, source, roles, contact, grounded, solver, plan, forward)
    incompatible = replace(solver, step_period_s=solver.step_period_s * 2)
    with pytest.raises(ContractError, match="solver cadence"):
        _provider(source, roles, contact, grounded, incompatible, plan, forward)
    with pytest.raises(ContractError, match="solver cadence"):
        _consume(provider, source, roles, contact, grounded, incompatible, plan, forward)


def test_provider_rejects_corrupted_bound_rows_without_binding_output_grid():
    source, roles, contact, grounded, solver, steady, forward = _bound_walk()
    plan = _canonical_plan(grounded, float(steady["body_height_m"]))
    provider = _provider(source, roles, contact, grounded, solver, plan, forward)
    corrupted = deepcopy(plan)
    corrupted["samples"][0]["root_forward_m"] += .25
    corrupted["samples"][0]["feet"]["left"]["forward_m"] += .5
    with pytest.raises(ContractError, match=r"sample\[0\].*differs"):
        provider.validate_for_consumption(
            source, semantic_roles=roles, solver_gait=solver,
            locomotion_gait=grounded, transition=None, plan=corrupted,
            contact_profile=contact, up_axis=(0, 1, 0), forward_axis=forward,
        )
    shifted = deepcopy(plan)
    shifted["samples"][0]["feet"]["left"]["target_offset_m"] = [0., 0., 0.]
    with pytest.raises(ContractError, match="caller-owned refinement offsets"):
        provider.validate_for_consumption(
            source, semantic_roles=roles, solver_gait=solver,
            locomotion_gait=grounded, transition=None, plan=shifted,
            contact_profile=contact, up_axis=(0, 1, 0), forward_axis=forward,
        )
