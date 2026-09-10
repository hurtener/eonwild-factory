"""Batch TRS must retain scalar hierarchy semantics used by admitted rigs."""
from types import SimpleNamespace
import numpy as np
from eonwild_motion.layers.leg_contact_resolve_v3 import (
    _world_matrices, _local_matrix, _matmul,
)


def test_batch_world_pose_matches_scalar_nested_nonuniform_hierarchy():
    rng = np.random.default_rng(981)
    count = 70
    source = SimpleNamespace(nodes=[{}] * count,
        parents=[None] + [int(rng.integers(0, i)) for i in range(1, count)])
    translations = rng.normal(size=(count, 3)).tolist()
    rotations = rng.normal(size=(count, 4)).tolist()
    scales = rng.uniform(.7, 1.3, (count, 3)).tolist()
    expected = []
    for index, parent in enumerate(source.parents):
        local = _local_matrix(translations[index], rotations[index], scales[index])
        expected.append(local if parent is None else _matmul(expected[parent], local))
    actual = _world_matrices(source, translations, rotations, scales)
    np.testing.assert_allclose(actual, expected, atol=2e-14, rtol=1e-14)
