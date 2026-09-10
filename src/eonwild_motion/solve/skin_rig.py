"""Per-compilation skinned rig and compressed material-surface witnesses.

Extracted from the V9 supported-interaction experiments. No experiment import,
prior animation, rig-specific bone name or shared mutable cache is involved.
Every skin influence set contributes; mouth witnesses are surface centroids,
not a convenient skeleton joint presented as contact.
"""
from __future__ import annotations

import numpy as np

from ..contact_gauge import _read_glb_accessor, _validate_contact_skin_binding
from ..errors import ContractError
from .airborne_gait import _unit


def rotation_matrix(quaternion):
    q = np.asarray(quaternion, dtype=float)
    norm = np.linalg.norm(q)
    if norm < 1e-12 or not np.isfinite(norm):
        raise ContractError("invalid pose quaternion")
    x, y, z, w = q / norm
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


class SkinRig:
    def __init__(self, glb, roles, forward, up, contact_profile, *, oral=False):
        self.glb, self.roles = glb, roles
        self.forward, self.up = _unit(forward), _unit(up)
        self.lateral = _unit(np.cross(self.up, self.forward))
        self.parents = tuple(glb.parents)
        self.order = []
        visiting = set()
        visited = set()
        def visit(index):
            if index in visiting:
                raise ContractError("cyclic rig hierarchy")
            if index in visited:
                return
            visiting.add(index)
            parent = self.parents[index]
            if parent is not None:
                visit(parent)
            visiting.remove(index); visited.add(index); self.order.append(index)
        for index in range(len(glb.nodes)):
            visit(index)
        self.roles_i = {key: [glb.name_to_node[n] for n in ([value] if isinstance(value, str) else value)]
                        for key, value in roles.items() if key in ("root", "pelvis", "spine", "chest", "neck", "head", "tail", "jaw_lower")}
        self.legs = {side: [glb.name_to_node[n] for n in roles["legs"][side]["contactChain"]] for side in ("left", "right")}
        geometry = contact_profile["geometry"]
        _validate_contact_skin_binding(glb, geometry)
        skin = glb.document["skins"][geometry["skin_index"]]
        self.joints = np.asarray(skin["joints"], dtype=int)
        def read(index):
            return np.asarray(_read_glb_accessor(glb, index, label="skin-rig accessor"), dtype=float)
        inverse = read(skin["inverseBindMatrices"])
        self.inverse_bind = inverse.reshape(-1, 4, 4).transpose(0, 2, 1)
        xyz = read(geometry["position_accessor"])
        self.positions = np.c_[xyz, np.ones(len(xyz))]
        ids = np.concatenate([read(i) for i in geometry["joint_accessors"]], axis=1)
        self.weights = np.concatenate([read(i) for i in geometry["weight_accessors"]], axis=1)
        if ids.shape != self.weights.shape or len(ids) != len(xyz) or not np.isfinite(self.weights).all() or (self.weights < 0).any():
            raise ContractError("invalid skin influence arrays")
        if not np.isfinite(ids).all() or (ids != np.floor(ids)).any() or (ids < 0).any() or (ids >= len(self.joints)).any():
            raise ContractError("skin influence references an invalid joint")
        self.ids = ids.astype(int)
        total = self.weights.sum(axis=1)
        if (total <= 0).any():
            raise ContractError("skin vertex has no weight")
        self.weights = self.weights / total[:, None]
        self.node_ids = self.joints[self.ids]
        self.foot_masks = {}
        self.foot_regions = {}
        for side, mask in geometry["feet"].items():
            selected = []
            regions = {}
            for region, label in (("sole", "sole_joints"), ("toe", "toe_joints")):
                nodes = [glb.name_to_node[n] for n in mask[label]]
                declared = np.where(np.isin(self.node_ids, nodes), self.weights, 0)
                policy = mask.get("membership_policy", "max_individual_weight.v1")
                if policy == "max_individual_weight.v1":
                    strength = declared.max(axis=1)
                elif policy == "sum_declared_region_weights.v1":
                    strength = declared.sum(axis=1)
                else:
                    raise ContractError("unsupported skin contact membership policy")
                indices = np.flatnonzero(strength >= mask["weight_threshold"])
                if not len(indices):
                    raise ContractError("skin contact mask is empty")
                regions[region] = indices
                selected.append(indices)
            # Keep the historic unique union for existing callers. The named
            # region arrays retain contact-gauge sole-then-toe ordering for
            # the explicit canonical support-anchor provider.
            self.foot_regions[side] = regions
            self.foot_masks[side] = np.unique(np.concatenate(selected))
        self.ground = float(geometry["ground"]["level_m"])
        self.neutral = tuple(np.asarray(v, dtype=float) for v in (glb.rest_translation, glb.rest_rotation, glb.rest_scale))
        self.neutral_world = self.world(*self.neutral)
        self.mouth_masks, self.centroid_terms = {}, {}
        if oral:
            self._admit_mouth()

    def world(self, translations, rotations, scales):
        worlds = np.zeros((len(translations), 4, 4))
        for index in self.order:
            local = np.eye(4)
            local[:3, :3] = rotation_matrix(rotations[index]) * scales[index]
            local[:3, 3] = translations[index]
            parent = self.parents[index]
            worlds[index] = local if parent is None else worlds[parent] @ local
        return worlds

    def skin(self, worlds, indices=None):
        select = slice(None) if indices is None else indices
        transforms = worlds[self.joints] @ self.inverse_bind
        return np.einsum('nv,nvij,nj->ni', self.weights[select], transforms[self.ids[select]], self.positions[select])[:, :3]

    def descendants(self, root):
        nodes = {root}
        for index in self.order:
            if self.parents[index] in nodes:
                nodes.add(index)
        return nodes

    def compress(self, indices):
        terms = np.zeros((len(self.joints), 4))
        for slot in range(self.ids.shape[1]):
            ids = self.ids[indices, slot]
            local = np.einsum('nij,nj->ni', self.inverse_bind[ids], self.positions[indices])
            np.add.at(terms, ids, local * self.weights[indices, slot, None] / len(indices))
        return terms

    def centroid(self, worlds, name):
        return np.einsum('nij,nj->i', worlds[self.joints], self.centroid_terms[name])[:3]

    def _admit_mouth(self):
        if 'jaw_lower' not in self.roles_i:
            raise ContractError("oral program requires a semantic lower-jaw role")
        jaw, head = self.roles_i['jaw_lower'][0], self.roles_i['head'][0]
        lower_weight = (self.weights * np.isin(self.node_ids, list(self.descendants(jaw)))).sum(axis=1)
        head_weight = (self.weights * np.isin(self.node_ids, list(self.descendants(head)))).sum(axis=1)
        points = self.skin(self.neutral_world)
        front, height = points @ self.forward, points @ self.up
        lower = np.flatnonzero(lower_weight > .7)
        if len(lower) < 10:
            raise ContractError("oral program cannot identify the lower-jaw surface")
        lower = lower[front[lower] > np.quantile(front[lower], .90)]
        upper = np.flatnonzero((head_weight > .7) & (lower_weight < .1) & (front > np.quantile(front[lower], .1)))
        if len(upper) < 3:
            raise ContractError("oral program cannot identify the upper rostral surface")
        lower = lower[height[lower] > np.quantile(height[lower], .7)]
        upper = upper[height[upper] < np.quantile(height[upper], .3)]
        if min(len(lower), len(upper)) < 3:
            raise ContractError("oral surface mask is empty")
        self.lower_jaw_indices = np.flatnonzero(lower_weight > .5)
        self.mouth_masks = {'upper': upper, 'lower': lower}
        self.centroid_terms = {key: self.compress(ids) for key, ids in self.mouth_masks.items()}

    def mouth_calibration(self):
        return {'classification': 'V9 rostral facing-surface mask, all normalized skin influences; not exact tooth contact',
                'upper_vertex_indices': self.mouth_masks['upper'].tolist(), 'lower_vertex_indices': self.mouth_masks['lower'].tolist(),
                'initial_upper_m': self.centroid(self.neutral_world, 'upper').tolist(),
                'initial_lower_m': self.centroid(self.neutral_world, 'lower').tolist()}
