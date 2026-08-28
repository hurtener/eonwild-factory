from __future__ import annotations

import numpy as np

from .quaternion import multiply


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
