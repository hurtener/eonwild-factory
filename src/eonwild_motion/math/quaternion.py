from __future__ import annotations

import numpy as np


def normalize(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, dtype=np.float64)
    return q / np.maximum(np.linalg.norm(q, axis=-1, keepdims=True), 1e-15)


def inverse(q: np.ndarray) -> np.ndarray:
    q = normalize(q)
    return np.concatenate([-q[..., :3], q[..., 3:4]], axis=-1)


def multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    av, aw = a[..., :3], a[..., 3:4]
    bv, bw = b[..., :3], b[..., 3:4]
    vector = aw * bv + bw * av + np.cross(av, bv)
    scalar = aw * bw - np.sum(av * bv, axis=-1, keepdims=True)
    return normalize(np.concatenate([vector, scalar], axis=-1))


def from_rotation_vector(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float64)
    angle = np.linalg.norm(vector, axis=-1, keepdims=True)
    half = angle * 0.5
    scale = np.empty_like(angle)
    np.divide(np.sin(half), angle, out=scale, where=angle > 1e-12)
    scale[angle <= 1e-12] = 0.5 - angle[angle <= 1e-12] ** 2 / 48.0
    return normalize(np.concatenate([vector * scale, np.cos(half)], axis=-1))


def to_rotation_vector(q: np.ndarray) -> np.ndarray:
    q = normalize(q)
    q = q if q[..., 3] >= 0.0 else -q
    vector = q[:3]
    scalar = float(np.clip(q[3], -1.0, 1.0))
    length = np.linalg.norm(vector)
    angle = 2.0 * np.arctan2(length, scalar)
    return vector * (angle / max(length, 1e-15))


def power(q: np.ndarray, fraction: float) -> np.ndarray:
    return from_rotation_vector(to_rotation_vector(q) * float(fraction))
