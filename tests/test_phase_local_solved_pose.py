from __future__ import annotations

from copy import deepcopy
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
from eonwild_motion.planning.grounded_gait import GroundedGait, build_grounded_plan
from eonwild_motion.solve import airborne_gait as solver
from eonwild_motion.solve.whole_body_gait_transition import _encode
from test_v9_airborne_gait import fixture


ROOT = Path(__file__).resolve().parents[1]
HEAVY_BIPED = ROOT / "assets/sha256/044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6.glb"


def _captured_context(monkeypatch, source, roles, gait):
    captured = []
    original = solver.solve_airborne_plan_sample

    def observe(context, row, *, body_response_sample=None):
        captured.append(context)
        return original(context, row, body_response_sample=body_response_sample)

    monkeypatch.setattr(solver, "solve_airborne_plan_sample", observe)
    _, _, plan, _ = solver.solve_airborne_gait(
        source, source_clip="source", semantic_roles=roles, gait=gait)
    assert captured
    return captured[0], plan, original


def _frame_transformed_renamed_fixture():
    source, roles = fixture("renamed_frame_", 1.37, upper_body=True)
    document = deepcopy(source.document)
    root = source.name_to_node[roles["root"]]
    document["nodes"][root]["rotation"] = [0., math.sqrt(.5), 0., math.sqrt(.5)]
    return Glb.from_bytes(_encode(document, source.binary)), roles


def _context_array_bytes(context):
    return (
        *(matrix.tobytes() for matrix in context.base_w),
        context.up.tobytes(), context.forward.tobytes(), context.lateral.tobytes(),
        context.origin.tobytes(),
        *(value.tobytes() for value in context.anatomical_normals.values()),
        *(value.tobytes() for value in context.toe_normals.values()),
    )


def test_phase_local_row_evaluator_is_order_independent_and_does_not_mutate_context(monkeypatch):
    source, roles = _frame_transformed_renamed_fixture()
    source_document = deepcopy(source.document)
    source_binary = bytes(source.binary)
    roles_before = deepcopy(roles)
    context, plan, direct = _captured_context(
        monkeypatch,
        source,
        roles,
        AirborneGait(cycles=1, sample_hz=24, step_length_body_heights=.31,
                     touchdown_reach_body_heights=.14, swing_clearance_body_heights=.16),
    )
    target = len(plan["samples"]) // 2
    plan_before = deepcopy(plan)
    context_arrays_before = _context_array_bytes(context)
    first = direct(context, plan["samples"][target])
    for index in (0, len(plan["samples"]) - 1, target - 1, target + 1, 1):
        direct(context, plan["samples"][index])
    repeated = direct(context, plan["samples"][target])
    assert repeated == first
    assert all(not matrix.flags.writeable for matrix in context.base_w)
    assert _context_array_bytes(context) == context_arrays_before
    assert plan == plan_before
    assert roles == roles_before
    assert source.document == source_document
    assert source.binary == source_binary
    bad = deepcopy(plan["samples"][target])
    bad["feet"]["left"]["target_offset_m"] = [1., 0., 0.]
    with pytest.raises(ContractError, match="invalid bounded skin target correction"):
        direct(context, bad)
    assert plan == plan_before
    assert roles == roles_before
    assert _context_array_bytes(context) == context_arrays_before
    assert source.document == source_document
    assert source.binary == source_binary


def test_renamed_frame_transformed_full_clip_payload_is_byte_identical():
    source, roles = _frame_transformed_renamed_fixture()
    root_motion, in_place, _, _ = solver.solve_airborne_gait(
        source, source_clip="source", semantic_roles=roles,
        gait=AirborneGait(cycles=1, sample_hz=24,
                          step_length_body_heights=.31,
                          touchdown_reach_body_heights=.14,
                          swing_clearance_body_heights=.16),
    )
    assert hashlib.sha256(root_motion).hexdigest() == (
        "b3aa6cff836839ec87b1ad12da37783f5dec17d47c775fc2580f85f8646395b2")
    assert hashlib.sha256(in_place).hexdigest() == (
        "3143995ba6519207a2c603eaf0c06004d97b222da1d1744b72b5f452f5ae058b")


def test_actual_heavy_biped_full_clip_payload_is_published_byte_identity():
    source = Glb.from_bytes(HEAVY_BIPED.read_bytes())
    roles = json.loads((ROOT / "catalog/rigs/heavy-biped.v9.json").read_text())["roles"]
    up = (0., 1., 0.)
    forward = (.03893162055641767, 0., .9992418770852486)
    height = geometry_height(source, roles, up)
    plan = build_grounded_plan(
        GroundedGait(cycles=1, sample_hz=24, step_length_body_heights=.1,
                     touchdown_reach_body_heights=.05,
                     swing_clearance_body_heights=.08),
        height,
    )
    root_motion, in_place, _, _ = solver.solve_airborne_gait(
        source, source_clip=None, semantic_roles=roles,
        gait=AirborneGait(step_period_s=1.23, cycles=1, sample_hz=24),
        up_axis=up, forward_axis=forward, plan_override=plan,
        legacy_overlay=False,
    )
    assert hashlib.sha256(root_motion).hexdigest() == (
        "b806d588964d0ad8d4ef9bcea3c567a30f1cd9b65888b6cb1ccb859080e9a417")
    assert hashlib.sha256(in_place).hexdigest() == (
        "fa7cb0e645b9a0d3c09bb9d07260713448b99d6bb0d2889d8870c76c2080a880")
