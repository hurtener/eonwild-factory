"""Skinned vertex-level sole extraction and terrain-contact measurements."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import numpy as np

from eonproc_v3.gltf_io import GlbAsset, PrimitiveData
from eonproc_v3.rig import SemanticMap, AnatomicalBasis, Pose
from .terrain import TerrainSurface


@dataclass(frozen=True)
class SoleSelection:
    side: str
    vertex_indices: np.ndarray
    total_candidate_vertices: int
    rest_min_height: float
    rest_contact_quantile: float
    influencing_bones: tuple[str, ...]


@dataclass(frozen=True)
class SoleMeasurement:
    side: str
    vertex_count: int
    minimum_signed_distance: float
    contact_quantile_signed_distance: float
    median_signed_distance: float
    maximum_penetration: float
    correction_up: float
    target_contact_quantile: float
    mean_normal: np.ndarray


class SoleContactModel:
    def __init__(
        self,
        asset: GlbAsset,
        semantics: SemanticMap,
        basis: AnatomicalBasis,
        hip_height: float,
        weight_threshold: float,
        height_band: float,
        min_vertices: int,
        max_vertices: int,
        contact_quantile: float,
        clearance: float,
        max_correction: float,
    ):
        self.asset = asset
        self.semantics = semantics
        self.basis = basis
        self.hip_height = float(hip_height)
        self.primitive: PrimitiveData = asset.primitive()
        if self.primitive.joints is None or self.primitive.weights is None:
            raise ValueError("Vertex-level sole contacts require a skinned primitive")
        self.skin_nodes, _ = asset.skin_data(asset.skin_index_for_mesh_node(self.primitive.mesh_index))
        self.node_to_skin_joint = {node: index for index, node in enumerate(self.skin_nodes)}
        self.contact_quantile = float(contact_quantile)
        self.clearance = float(clearance)
        self.mesh_ground = float(np.min(self.primitive.positions[:, 1]))
        self.max_correction = float(max_correction)
        self.selections = {
            side: self._select(side, weight_threshold, height_band, min_vertices, max_vertices)
            for side in ("l", "r")
        }

    def _side_bones(self, side: str) -> list[str]:
        tags = [f"foot_{side}", f"ankle_{side}", f"toe_{side}", f"toe_2_{side}", f"toe_3_{side}"]
        bones: list[str] = []
        for tag in tags:
            if tag not in self.semantics.tags:
                continue
            root = self.semantics.bone(tag)
            bones.append(root)
            if tag.startswith("toe"):
                bones.extend(self.asset.single_child_chain(root, max_nodes=5)[1:])
        return sorted(set(bones), key=lambda name: self.asset.name_to_node[name])

    def _select(self, side: str, weight_threshold: float, height_band: float, min_vertices: int, max_vertices: int) -> SoleSelection:
        bones = self._side_bones(side)
        joint_ids = {
            self.node_to_skin_joint[self.asset.name_to_node[name]]
            for name in bones
            if self.asset.name_to_node[name] in self.node_to_skin_joint
        }
        if not joint_ids:
            raise ValueError(f"No skin joints found for {side} sole")
        joint_mask = np.isin(self.primitive.joints, np.fromiter(joint_ids, dtype=np.int64))
        side_weight = np.sum(self.primitive.weights * joint_mask, axis=1)
        candidates = np.flatnonzero(side_weight >= weight_threshold)
        if len(candidates) == 0:
            raise ValueError(f"No vertices pass sole weight threshold for {side}")
        positions = self.primitive.positions[candidates]
        min_height = float(np.min(positions[:, 1]))
        band_mask = positions[:, 1] <= min_height + height_band
        selected = candidates[band_mask]
        # Prefer the lowest, strongest vertices if the broad band is sparse.
        if len(selected) < min_vertices:
            score = (
                (self.primitive.positions[candidates, 1] - min_height) / max(height_band, 1e-9)
                + (1.0 - side_weight[candidates]) * 0.65
            )
            order = np.argsort(score)
            selected = candidates[order[: min(min_vertices, len(candidates))]]
        if len(selected) > max_vertices:
            # Preserve the lowest contact witnesses and stratify the remainder
            # across the sole footprint. This keeps collision truly vertex-level
            # without skinning thousands of redundant neighboring vertices.
            positions_selected = self.primitive.positions[selected]
            lowest_count = min(max(24, max_vertices // 4), max_vertices)
            low_order = np.argsort(positions_selected[:, 1])[:lowest_count]
            chosen = list(selected[low_order])
            remaining = np.setdiff1d(selected, np.asarray(chosen, dtype=np.int64), assume_unique=False)
            if len(remaining):
                pos = self.primitive.positions[remaining]
                x = pos[:, 0]; z = pos[:, 2]
                gx = np.floor((x - x.min()) / max(float(np.ptp(x)), 1e-9) * 11.999).astype(int)
                gz = np.floor((z - z.min()) / max(float(np.ptp(z)), 1e-9) * 7.999).astype(int)
                for cell in sorted(set(zip(gx.tolist(), gz.tolist()))):
                    mask = np.flatnonzero((gx == cell[0]) & (gz == cell[1]))
                    if len(mask):
                        local = mask[np.argmin(pos[mask, 1])]
                        chosen.append(int(remaining[local]))
                    if len(chosen) >= max_vertices:
                        break
            if len(chosen) < max_vertices:
                residual = np.setdiff1d(selected, np.asarray(chosen, dtype=np.int64), assume_unique=False)
                if len(residual):
                    stride = max(1, len(residual) // max(1, max_vertices - len(chosen)))
                    chosen.extend(residual[::stride][: max_vertices - len(chosen)].tolist())
            selected = np.asarray(chosen[:max_vertices], dtype=np.int64)
        values = self.primitive.positions[selected, 1]
        return SoleSelection(
            side=side,
            vertex_indices=np.asarray(selected, dtype=np.int64),
            total_candidate_vertices=int(len(candidates)),
            rest_min_height=float(np.min(values)),
            rest_contact_quantile=float(np.quantile(values, self.contact_quantile)),
            influencing_bones=tuple(bones),
        )

    def skinned_vertices(self, pose: Pose, side: str) -> np.ndarray:
        selection = self.selections[side]
        idx = selection.vertex_indices
        return self.asset.skin_points(
            self.primitive.positions[idx],
            self.primitive.joints[idx],
            self.primitive.weights[idx],
            pose.world_matrices,
            self.asset.skin_index_for_mesh_node(self.primitive.mesh_index),
        )

    def measure(self, pose: Pose, side: str, terrain: TerrainSurface, load: float = 1.0) -> SoleMeasurement:
        points = self.skinned_vertices(pose, side)
        heights, normals = terrain.heights_normals(points)
        signed = points[:, 1] - heights
        q = float(np.quantile(signed, self.contact_quantile))
        selection = self.selections[side]
        target_q = float(selection.rest_contact_quantile - self.mesh_ground)
        minimum = float(np.min(signed))
        # Preserve the model's curved/rest sole profile while guaranteeing that
        # no selected sole vertex is driven through the terrain.
        quantile_correction = (target_q - q) * float(load)
        penetration_correction = self.clearance - minimum
        # Collision prevention is a hard constraint once the foot carries any
        # meaningful load. Quantile matching remains softly load weighted.
        desired = max(quantile_correction, penetration_correction) if minimum < self.clearance and load > 0.08 else quantile_correction
        correction = float(np.clip(desired, -self.max_correction, self.max_correction))
        normal = np.mean(normals, axis=0)
        normal /= max(np.linalg.norm(normal), 1e-12)
        return SoleMeasurement(
            side=side,
            vertex_count=int(len(points)),
            minimum_signed_distance=float(np.min(signed)),
            contact_quantile_signed_distance=q,
            median_signed_distance=float(np.median(signed)),
            maximum_penetration=float(max(0.0, -np.min(signed))),
            correction_up=correction,
            target_contact_quantile=target_q,
            mean_normal=normal,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            side: {
                "selected_vertex_count": int(len(selection.vertex_indices)),
                "candidate_vertex_count": selection.total_candidate_vertices,
                "rest_min_height": selection.rest_min_height,
                "rest_contact_quantile": selection.rest_contact_quantile,
                "influencing_bones": list(selection.influencing_bones),
            }
            for side, selection in self.selections.items()
        }
