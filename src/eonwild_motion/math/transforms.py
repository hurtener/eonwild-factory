from __future__ import annotations

import numpy as np

from .quaternion import multiply


def quaternion_matrix(q: np.ndarray) -> np.ndarray:
    x, y, z, w = np.asarray(q, dtype=np.float64)
    n = max(float(np.dot(q, q)), 1e-30)
    s = 2.0 / n
    return np.array([
        [1 - s * (y*y + z*z), s * (x*y - z*w), s * (x*z + y*w)],
        [s * (x*y + z*w), 1 - s * (x*x + z*z), s * (y*z - x*w)],
        [s * (x*z - y*w), s * (y*z + x*w), 1 - s * (x*x + y*y)],
    ], dtype=np.float64)


def local_matrix(translation: np.ndarray, rotation: np.ndarray, scale: np.ndarray) -> np.ndarray:
    result = np.eye(4, dtype=np.float64)
    result[:3, :3] = quaternion_matrix(rotation) @ np.diag(scale)
    result[:3, 3] = translation
    return result


def all_world_matrices(glb, translations, rotations, scales=None):
    if scales is None:
        scales = [np.asarray(value, dtype=np.float64) for value in glb.rest_scale]
    worlds = [None] * len(glb.nodes)
    def resolve(index):
        if worlds[index] is None:
            local = local_matrix(translations[index], rotations[index], scales[index])
            parent = glb.parents[index]
            worlds[index] = local if parent is None else resolve(int(parent)) @ local
        return worlds[index]
    return [resolve(index) for index in range(len(glb.nodes))]


def world_matrix(glb, translations, rotations, index, scales=None):
    if scales is None:
        scales = [np.asarray(value, dtype=np.float64) for value in glb.rest_scale]
    chain = []
    cursor = int(index)
    while cursor is not None:
        chain.append(cursor)
        cursor = glb.parents[cursor]
    result = np.eye(4, dtype=np.float64)
    for node in reversed(chain):
        result = result @ local_matrix(translations[node], rotations[node], scales[node])
    return result


def all_world_rotations(glb, local_rotations: list[np.ndarray]) -> list[np.ndarray]:
    worlds: list[np.ndarray | None] = [None] * len(local_rotations)

    def resolve(index: int) -> np.ndarray:
        if worlds[index] is None:
            parent = glb.parents[index]
            worlds[index] = (
                local_rotations[index]
                if parent is None
                else multiply(resolve(int(parent)), local_rotations[index])
            )
        return worlds[index]  # type: ignore[return-value]

    return [resolve(index) for index in range(len(local_rotations))]


def all_world_positions(glb, local_translations, local_rotations):
    rotations = all_world_rotations(glb, local_rotations)
    positions = [None] * len(glb.nodes)
    def resolve(index):
        if positions[index] is None:
            parent = glb.parents[index]
            if parent is None:
                positions[index] = np.asarray(local_translations[index], dtype=np.float64)
            else:
                parent = int(parent)
                resolve(parent)
                basis = quaternion_matrix(rotations[parent])
                positions[index] = positions[parent] + basis @ (
                    np.asarray(local_translations[index], dtype=np.float64)
                    * np.asarray(glb.rest_scale[parent], dtype=np.float64)
                )
        return positions[index]
    return [resolve(index) for index in range(len(glb.nodes))]
