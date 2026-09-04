"""Deterministic accepted V5.5 lower-foot calibration for V8.1."""
from __future__ import annotations
from typing import Any
import numpy as np
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import AnatomicalBasis, SemanticMap

def lower_foot_pivots(asset:GlbAsset,semantics:SemanticMap,basis:AnatomicalBasis,gap_fraction:float)->dict[str,Any]:
    if not 0.0<gap_fraction<1.0: raise ValueError("gap_fraction must be strictly between 0 and 1")
    primitive=asset.primitive()
    if primitive.joints is None or primitive.weights is None: raise ValueError("Expected skinned mesh")
    skin_index=asset.skin_index_for_mesh_node(primitive.mesh_index)
    inverse_bind_before=asset.skin_data(skin_index)[1].copy()
    before=asset.skin_points(primitive.positions,primitive.joints,primitive.weights,asset.rest_world,skin_index)
    adjustments=[]; toes_before={}
    for side in ("l","r"):
        foot=semantics.bone(f"foot_{side}"); toe_names=[semantics.bone(f"toe_{side}"),semantics.bone(f"toe_2_{side}"),semantics.bone(f"toe_3_{side}")]
        fi=asset.name_to_node[foot]; fp=asset.rest_world[fi][:3,3].copy(); toe_positions=[]
        for toe in toe_names:
            pos=asset.rest_world[asset.name_to_node[toe]][:3,3].copy(); toes_before[toe]=pos; toe_positions.append(pos)
        centroid=np.mean(toe_positions,axis=0); gap=float(np.dot(centroid-fp,basis.up))
        if gap>=0: raise ValueError(f"Expected {foot} above toe-root plane")
        change=asset.move_joint_world_position_preserve_rest_skin(foot,fp+basis.up*gap*gap_fraction,skin_index=skin_index)
        change.update({"side":side,"toeRootCentroid":centroid.tolist(),"originalVerticalGapM":-gap,"movementDownM":-gap*gap_fraction,"remainingVerticalGapM":float(np.dot(asset.rest_world[fi][:3,3]-centroid,basis.up))})
        adjustments.append(change)
    after=asset.skin_points(primitive.positions,primitive.joints,primitive.weights,asset.rest_world,skin_index)
    toe_error=max(float(np.linalg.norm(asset.rest_world[asset.name_to_node[n]][:3,3]-p)) for n,p in toes_before.items())
    rest_error=float(np.max(np.linalg.norm(after-before,axis=1)))
    movement_delta=abs(adjustments[0]["movementDownM"]-adjustments[1]["movementDownM"])
    inverse_bind_after=asset.skin_data(skin_index)[1]
    changed_slots=np.flatnonzero(np.max(np.abs(inverse_bind_after-inverse_bind_before),axis=(1,2))>1e-12).astype(int).tolist()
    result={"gapFraction":gap_fraction,"adjustments":adjustments,"maximumToeRootOriginErrorM":toe_error,"maximumRestSkinnedVertexErrorM":rest_error,"bilateralMovementDifferenceM":movement_delta,"inverseBindSlotsChanged":len(changed_slots),"changedInverseBindSlots":changed_slots}
    if toe_error>=1e-6 or rest_error>=1e-6 or movement_delta>=1e-6 or len(changed_slots)!=2: raise ValueError(f"Foot pivot invariants failed: {result}")
    return result
