"""Sampled ground-resultant sensitivity from an admitted centroidal series.

This is an offline diagnostic for emitted motion.  It differentiates sampled
COM velocity and angular momentum, so it is not an exact statement about a
LINEAR glTF channel at its velocity-discontinuous keys.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from ..errors import ContractError
from .centroidal import CentroidalSample, _finite, _finite_diff, _vec3


@dataclass(frozen=True)
class SupportResultantSample:
    time_s: float
    force_n: tuple[float, float, float]
    point_m: tuple[float, float, float]
    angular_momentum_rate_nm: tuple[float, float, float]
    free_normal_moment_nm: float


def sampled_support_resultants(
    samples: Sequence[CentroidalSample],
    *,
    ground_height_m: float,
    up_axis: Sequence[float],
    forward_axis: Sequence[float],
    gravity_mps2: float = 9.80665,
) -> tuple[SupportResultantSample, ...]:
    """Infer one ground-force application point at each centroidal sample.

    Tangential moment balance determines the two coordinates on the declared
    ground plane.  The remaining normal-axis moment is reported as a free
    moment; a single force application point cannot generally explain it.
    """
    if len(samples) < 3:
        raise ContractError("support resultant needs at least three centroidal samples")
    if any(sample.mass_mode != "absolute" for sample in samples):
        raise ContractError("support resultant requires absolute mass samples")
    masses = np.asarray([_finite(sample.total_mass_kg, label="sample mass") for sample in samples])
    if np.any(masses <= 0.0) or not np.allclose(masses, masses[0], rtol=0.0, atol=1e-9):
        raise ContractError("support resultant requires one positive constant mass")
    times = np.asarray([_finite(sample.time_s, label="sample time") for sample in samples])
    if np.any(np.diff(times) <= 0.0):
        raise ContractError("support resultant timeline must be strictly increasing")
    up = _vec3(up_axis, label="up axis")
    forward = _vec3(forward_axis, label="forward axis")
    up_norm = float(np.linalg.norm(up))
    if up_norm <= 1e-12:
        raise ContractError("support resultant up axis must be nonzero")
    up /= up_norm
    forward -= up * float(np.dot(up, forward))
    forward_norm = float(np.linalg.norm(forward))
    if forward_norm <= 1e-12:
        raise ContractError("support resultant forward axis must differ from up")
    forward /= forward_norm
    lateral = np.cross(up, forward)
    ground = _finite(ground_height_m, label="ground height")
    gravity = _finite(gravity_mps2, label="gravity")
    if gravity <= 0.0:
        raise ContractError("gravity must be positive")

    com = np.asarray([sample.com_m for sample in samples], dtype=float)
    velocity = np.asarray([sample.com_velocity_mps for sample in samples], dtype=float)
    momentum = np.asarray([sample.angular_momentum_kg_m2ps for sample in samples], dtype=float)
    if not np.isfinite(com).all() or not np.isfinite(velocity).all() or not np.isfinite(momentum).all():
        raise ContractError("support resultant samples must be finite")
    acceleration = _finite_diff(velocity, times)
    momentum_rate = _finite_diff(momentum, times)
    gravity_vector = -gravity * up

    result: list[SupportResultantSample] = []
    for index, sample in enumerate(samples):
        force = masses[index] * (acceleration[index] - gravity_vector)
        normal_force = float(force @ up)
        if normal_force <= 1e-9:
            raise ContractError("support resultant requires positive normal force")
        center = com[index]
        height_delta = ground - float(center @ up)
        force_lateral = float(force @ lateral)
        force_forward = float(force @ forward)
        torque_lateral = float(momentum_rate[index] @ lateral)
        torque_forward = float(momentum_rate[index] @ forward)
        offset_forward = (height_delta * force_forward - torque_lateral) / normal_force
        offset_lateral = (torque_forward + height_delta * force_lateral) / normal_force
        point = (
            center
            + offset_lateral * lateral
            + height_delta * up
            + offset_forward * forward
        )
        produced = np.cross(point - center, force)
        free_normal = float((momentum_rate[index] - produced) @ up)
        result.append(
            SupportResultantSample(
                time_s=float(sample.time_s),
                force_n=tuple(float(value) for value in force),
                point_m=tuple(float(value) for value in point),
                angular_momentum_rate_nm=tuple(float(value) for value in momentum_rate[index]),
                free_normal_moment_nm=free_normal,
            )
        )
    return tuple(result)


__all__ = ["SupportResultantSample", "sampled_support_resultants"]
