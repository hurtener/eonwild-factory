from __future__ import annotations

import numpy as np
import pytest

from eonwild_motion.dynamics.body_support_coordinator import (
    BodyDelta,
    periodic_body_delta,
)
from eonwild_motion.dynamics.source_body_support_adapter import (
    SourceFinalGeometryAdapter,
)
from eonwild_motion.errors import ContractError
from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from test_constant_skin_targets import _inputs


def _adapter(monkeypatch):
    monkeypatch.setattr(
        CanonicalConstantSkinTargetLaw,
        "_solve_joint_contact_endpoint",
        lambda self, query, side, time_s: np.zeros(4),
    )
    inputs = _inputs()
    values = dict(inputs)
    query = values.pop("query")
    provider = values.pop("provider")
    law = CanonicalConstantSkinTargetLaw.build(
        query,
        provider,
        law_id="canonical_semantic_joint_contact_targets.v3",
        **values,
    )
    return SourceFinalGeometryAdapter(query, law)


def test_adapter_runs_bound_control_through_final_law_and_skin(monkeypatch) -> None:
    adapter = _adapter(monkeypatch)
    skin = adapter._frozen_law._skin
    original_skin = skin.skin

    def admitted_full_skin(worlds, indices=None):
        result = original_skin(worlds, indices)
        if indices is None:
            result = np.array(result, copy=True)
            result[:, 1] += 0.002
        return result

    monkeypatch.setattr(skin, "skin", admitted_full_skin)
    coefficients = (0.0, 0.0001) + (0.0,) * 10
    cycle = adapter.body_control_cycle_s
    time_s = 0.2
    sample = adapter(
        coefficients,
        periodic_body_delta(coefficients, time_s, cycle),
        time_s,
    )
    assert sample.final_geometry_passed is True
    assert sample.frozen_anchor_sha256 == adapter.frozen_anchor_sha256
    assert adapter.body_height_m > 0.0
    assert len(sample.support_points_m) >= 3
    assert sample.joint_world_matrices
    assert all(
        np.asarray(matrix).shape == (4, 4)
        for matrix in sample.joint_world_matrices.values()
    )


def test_adapter_query_binding_changes_without_moving_frozen_anchors(monkeypatch) -> None:
    adapter = _adapter(monkeypatch)
    zero = adapter.binding_receipt((0.0,) * 12)
    shifted = adapter.binding_receipt((0.0, 0.0001) + (0.0,) * 10)
    assert zero["query_binding_sha256"] != shifted["query_binding_sha256"]
    assert zero["final_law_binding_sha256"] != shifted["final_law_binding_sha256"]
    assert zero["frozen_anchor_sha256"] == shifted["frozen_anchor_sha256"]
    assert (
        zero["skin_target_law"]["law_binding_sha256"]
        == shifted["skin_target_law"]["law_binding_sha256"]
    )


def test_adapter_rejects_delta_not_derived_from_complete_coefficients(monkeypatch) -> None:
    adapter = _adapter(monkeypatch)
    coefficients = (0.0, 0.0001) + (0.0,) * 10
    with pytest.raises(ContractError, match="delta differs"):
        adapter(coefficients, BodyDelta((0.0,) * 3, (0.0,) * 3), 0.2)


def test_adapter_rechecks_frozen_anchor_integrity(monkeypatch) -> None:
    adapter = _adapter(monkeypatch)
    anchor = adapter._frozen_law._provider._anchors["left"]
    anchor.material_origin_m.setflags(write=True)
    anchor.material_origin_m[0, 0] += 0.001
    with pytest.raises(ContractError, match="anchor"):
        adapter.binding_receipt((0.0,) * 12)


def test_adapter_rejects_unmasked_full_skin_floor_failure(monkeypatch) -> None:
    adapter = _adapter(monkeypatch)
    skin = adapter._frozen_law._skin
    original_skin = skin.skin
    masked = set(
        int(index)
        for side in ("left", "right")
        for index in skin.foot_masks[side]
    )
    unmasked = next(index for index in range(len(skin.positions)) if index not in masked)

    def lower_only_full_skin(worlds, indices=None):
        result = original_skin(worlds, indices)
        if indices is None:
            result = np.array(result, copy=True)
            result[unmasked, 1] = skin.ground - 0.001
        return result

    monkeypatch.setattr(skin, "skin", lower_only_full_skin)
    coefficients = (0.0,) * 12
    time_s = 0.2
    with pytest.raises(ContractError, match="full posed skin violates"):
        adapter(
            coefficients,
            periodic_body_delta(
                coefficients, time_s, adapter.body_control_cycle_s
            ),
            time_s,
        )


@pytest.mark.parametrize(
    "coefficients",
    [(0.0,) * 11, (False,) + (0.0,) * 11, (float("nan"),) + (0.0,) * 11],
)
def test_adapter_rejects_invalid_coefficient_vectors(monkeypatch, coefficients) -> None:
    with pytest.raises(ContractError, match="12 finite coefficients"):
        _adapter(monkeypatch).binding_receipt(coefficients)
