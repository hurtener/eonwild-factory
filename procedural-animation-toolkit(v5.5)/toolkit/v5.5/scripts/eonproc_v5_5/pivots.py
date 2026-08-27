"""Deterministic V5.5 lower-foot pivot placement."""
from __future__ import annotations

from typing import Any

import numpy as np

from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import AnatomicalBasis, SemanticMap


def lower_foot_pivots(
    asset: GlbAsset,
    semantics: SemanticMap,
    basis: AnatomicalBasis,
    gap_fraction: float,
) -> dict[str, Any]:
    """Lower both foot pivots while preserving toe origins and rest skin."""
    if not 0.0 < gap_fraction < 1.0:
        raise ValueError("gap_fraction must be strictly between 0 and 1")
    primitive = asset.primitive()
    if primitive.joints is None or primitive.weights is None:
        raise ValueError("Expected a skinned mesh with joints and weights")
    skin_index = asset.skin_index_for_mesh_node(primitive.mesh_index)
    before_points = asset.skin_points(
        primitive.positions,
        primitive.joints,
        primitive.weights,
        asset.rest_world,
        skin_index,
    )
    adjustments: list[dict[str, Any]] = []
    toe_origins_before: dict[str, np.ndarray] = {}
    for side in ("l", "r"):
        foot_name = semantics.bone(f"foot_{side}")
        toe_names = [
            semantics.bone(f"toe_{side}"),
            semantics.bone(f"toe_2_{side}"),
            semantics.bone(f"toe_3_{side}"),
        ]
        foot_index = asset.name_to_node[foot_name]
        foot_position = asset.rest_world[foot_index][:3, 3].copy()
        toe_positions = []
        for toe_name in toe_names:
            toe_position = asset.rest_world[asset.name_to_node[toe_name]][:3, 3].copy()
            toe_origins_before[toe_name] = toe_position
            toe_positions.append(toe_position)
        split_centroid = np.mean(toe_positions, axis=0)
        signed_gap = float(np.dot(split_centroid - foot_position, basis.up))
        if signed_gap >= 0.0:
            raise ValueError(f"Expected {foot_name} above its toe-root plane, signed gap={signed_gap}")
        target = foot_position + basis.up * signed_gap * gap_fraction
        adjustment = asset.move_joint_world_position_preserve_rest_skin(
            foot_name,
            target,
            skin_index=skin_index,
        )
        remaining_gap = float(np.dot(asset.rest_world[foot_index][:3, 3] - split_centroid, basis.up))
        adjustment.update({
            "side": side,
            "toeRootCentroid": split_centroid.astype(float).tolist(),
            "originalVerticalGapM": -signed_gap,
            "movementDownM": -signed_gap * gap_fraction,
            "remainingVerticalGapM": remaining_gap,
        })
        adjustments.append(adjustment)

    after_points = asset.skin_points(
        primitive.positions,
        primitive.joints,
        primitive.weights,
        asset.rest_world,
        skin_index,
    )
    rest_vertex_error = np.linalg.norm(after_points - before_points, axis=1)
    toe_origin_error = {
        name: float(np.linalg.norm(asset.rest_world[asset.name_to_node[name]][:3, 3] - position))
        for name, position in toe_origins_before.items()
    }
    movement_delta = abs(adjustments[0]["movementDownM"] - adjustments[1]["movementDownM"])
    result = {
        "gapFraction": gap_fraction,
        "anatomicalUp": basis.up.astype(float).tolist(),
        "adjustments": adjustments,
        "maximumToeRootOriginErrorM": max(toe_origin_error.values(), default=0.0),
        "maximumRestSkinnedVertexErrorM": float(rest_vertex_error.max(initial=0.0)),
        "bilateralMovementDifferenceM": movement_delta,
    }
    if result["maximumToeRootOriginErrorM"] >= 1e-6:
        raise ValueError(f"Toe-root preservation failed: {result['maximumToeRootOriginErrorM']}")
    if result["maximumRestSkinnedVertexErrorM"] >= 1e-6:
        raise ValueError(f"Rest-skin preservation failed: {result['maximumRestSkinnedVertexErrorM']}")
    if movement_delta >= 1e-6:
        raise ValueError(f"Bilateral pivot movement mismatch: {movement_delta}")
    return result
