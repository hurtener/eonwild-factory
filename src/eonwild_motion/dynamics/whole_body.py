"""Axial-chain whole-body solve: spine/neck/head target tracking on COM plans.

The legs already have a geometric solver (``solve/airborne_gait.py``) and
the root is reconstructed from the COM plan
(``planning/power_attack.py``). This module owns what the engine has never
driven: the axial chains. Given a root track plus a target window (the
bite), it solves pitch angles along a semantic chain (spine → neck →
head) with cyclic coordinate descent, projects every joint through its
hard envelope, reports preferred-margin status, and couples the tail
through the damped ODE (``transition.tail_ode_track``) driven by the
head sweep it must answer — momentum redistribution as a computed track.

Reduced-order model, stated plainly: each chain joint contributes one
sagittal pitch degree of freedom about the caller-supplied lateral axis
on top of its rest orientation. That covers the pitch-dominated
bite/feeding/vocal tasks that carry the predator fantasy; full 3-DOF
articulation surfaces arrive with the reviewed joint catalog.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..errors import ContractError
from .capacity import JointEnvelope, contracted_preferred_envelope
from .centroidal import _finite, _quat, _vec3, fk_world_frames, quat_mul
from .transition import tail_ode_track

SCHEMA = "eonwild.motion.v9.axial-solve.v1"


def _axis_angle_quat(axis: np.ndarray, angle_rad: float) -> np.ndarray:
    return np.array(
        [*(axis * math.sin(angle_rad / 2.0)), math.cos(angle_rad / 2.0)], dtype=float
    )


def _matrix_to_quat(matrix: np.ndarray) -> np.ndarray:
    """Rotation matrix to unit quaternion (x, y, z, w); fail-closed."""
    m = np.asarray(matrix, dtype=float).reshape(3, 3)
    trace = float(np.trace(m))
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        quat = np.array(
            [(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s,
             (m[1, 0] - m[0, 1]) / s, 0.25 * s]
        )
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
        quat = np.array(
            [0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s,
             (m[2, 1] - m[1, 2]) / s]
        )
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
        quat = np.array(
            [(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s,
             (m[0, 2] - m[2, 0]) / s]
        )
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
        quat = np.array(
            [(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s,
             (m[1, 0] - m[0, 1]) / s]
        )
    norm = float(np.linalg.norm(quat))
    if norm <= 1e-12 or not math.isfinite(norm):
        raise ContractError("root rotation matrix is degenerate")
    return quat / norm


def solve_axial_chain(
    *,
    parents: Sequence[int | None],
    rest_translations: Sequence[Sequence[float]],
    rest_rotations: Sequence[Sequence[float]],
    chain: Sequence[int],
    root_position_m: Sequence[float],
    root_rotation: np.ndarray,
    lateral_axis: Sequence[float],
    target_m: Sequence[float],
    envelopes: Mapping[int, JointEnvelope] | None = None,
    iterations: int = 60,
    tolerance_m: float = 1e-4,
) -> dict[str, Any]:
    """CCD pitch solve for one axial chain reaching ``target_m``.

    Returns solved pitch angles (radians, one per chain joint from base
    to tip), end-effector residual, per-joint envelope projection facts
    and iteration count. Deterministic: fixed iteration cap, no random
    restarts; unreachable targets report maximum extension honestly.

    Frame note: pitch is applied about ``lateral_axis`` in each node's
    local frame and measured in the parent-frame world plane. This is
    exact for axis-aligned rigs (identity rest rotations on the axial
    chain, the theropod norm); for twisted rest poses treat results as
    first-order and re-validate against the skinned head marker.
    """
    if len(chain) < 1:
        raise ContractError("axial chain needs at least one joint")
    count = len(parents)
    lateral = np.asarray([_finite(float(v), label="lateral axis") for v in lateral_axis], dtype=float)
    if lateral.shape != (3,) or float(np.linalg.norm(lateral)) <= 1e-12:
        raise ContractError("lateral axis must be a non-zero 3-vector")
    target = _vec3(target_m, label="target_m")
    root_pos = _vec3(root_position_m, label="root_position_m")
    root_rot = np.asarray(root_rotation, dtype=float).reshape(3, 3)
    iters = int(iterations)
    if iters < 1:
        raise ContractError("axial iterations must be positive")
    tol = _finite(tolerance_m, label="tolerance_m")

    pitch = np.zeros(len(chain))
    chain_index = {node: position for position, node in enumerate(chain)}
    lateral_unit = lateral / float(np.linalg.norm(lateral))
    hard = {node: (envelopes[node].hard_min_deg, envelopes[node].hard_max_deg) if envelopes and node in envelopes else (-180.0, 180.0) for node in chain}

    def evaluate(angles: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        # Pitch quaternions premultiply rest orientation (parent-frame
        # pitch); the FK carries those frames to the world. Node 0's
        # parent frame is the world root placement.
        local_q: list[tuple[float, float, float, float]] = []
        root_quat = _matrix_to_quat(root_rot)
        for node in range(count):
            if node == 0 and parents[node] is None:
                # World root placement owns the root node's frame.
                base = root_quat
            else:
                base = _quat(np.asarray(rest_rotations[node]), label="rest rotation")
            if node in chain_index:
                twist = _axis_angle_quat(lateral_unit, float(angles[chain_index[node]]))
                base = quat_mul(twist, base)
            local_q.append((float(base[0]), float(base[1]), float(base[2]), float(base[3])))
        world_pos, world_rot = fk_world_frames(
            parents,
            [root_pos if i == 0 and parents[i] is None else rest_translations[i] for i in range(count)],
            rest_rotations,
            local_translations=[
                root_pos if i == 0 and parents[i] is None else rest_translations[i]
                for i in range(count)
            ],
            local_rotations=local_q,
        )
        return world_pos[chain[-1]], world_pos, world_rot
    residual = math.inf
    used = 0
    for used in range(1, iters + 1):
        tip, positions, rotations = evaluate(pitch)
        residual = float(np.linalg.norm(target - tip))
        if residual <= tol:
            break
        for position in reversed(range(len(chain))):
            node = chain[position]
            tip, positions, rotations = evaluate(pitch)
            joint_pos = positions[node]
            to_tip = tip - joint_pos
            to_target = target - joint_pos
            # Sagittal-plane angle between the two directions.
            axis_world = rotations[parents[node]] @ lateral if parents[node] is not None else root_rot @ lateral
            normal = axis_world / float(np.linalg.norm(axis_world))
            a = to_tip - normal * float(to_tip @ normal)
            b = to_target - normal * float(to_target @ normal)
            if float(np.linalg.norm(a)) < 1e-9 or float(np.linalg.norm(b)) < 1e-9:
                continue
            cos_a = max(-1.0, min(1.0, float(a @ b) / (float(np.linalg.norm(a)) * float(np.linalg.norm(b)))))
            delta = math.acos(cos_a)
            sign = float(np.sign(float(np.cross(a, b) @ normal))) or 1.0
            pitch[position] += sign * delta
            low, high = (math.radians(hard[node][0]), math.radians(hard[node][1]))
            pitch[position] = max(low, min(high, pitch[position]))
    tip, _, _ = evaluate(pitch)
    residual = float(np.linalg.norm(target - tip))
    joints = []
    for position, node in enumerate(chain):
        deg = math.degrees(float(pitch[position]))
        fact: dict[str, Any] = {"node": node, "pitch_deg": deg, "hard_deg": list(hard[node])}
        if envelopes and node in envelopes:
            conditioned = contracted_preferred_envelope(envelopes[node])
            low_p, high_p = conditioned["preferred_conditioned_deg"]
            fact["preferred_deg"] = [low_p, high_p]
            fact["inside_preferred"] = bool(low_p <= deg <= high_p)
        joints.append(fact)
    return {
        "schema": SCHEMA,
        "pitch_rad": [float(v) for v in pitch],
        "joints": joints,
        "tip_m": [float(v) for v in tip],
        "target_m": [float(v) for v in target],
        "residual_m": residual,
        "reached": bool(residual <= tol),
        "iterations": used,
    }


def solve_bite_window(
    *,
    parents: Sequence[int | None],
    rest_translations: Sequence[Sequence[float]],
    rest_rotations: Sequence[Sequence[float]],
    chain: Sequence[int],
    root_track: Sequence[Mapping[str, Any]],
    root_rotations: Sequence[np.ndarray],
    lateral_axis: Sequence[float],
    targets_m: Sequence[Sequence[float]],
    times_s: Sequence[float],
    envelopes: Mapping[int, JointEnvelope] | None = None,
    head_mass_kg: float = 80.0,
    head_lever_m: float = 1.0,
    tail_moment_gain: float = 1.0,
    tail_params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Axial solve over a target window plus tail momentum coupling.

    Each sample solves the head chain at its target; the head sweep rate
    (point-mass head at ``head_lever_m``) drives the tail ODE as the
    answering moment, so the tail track is coupled to what the head did —
    not to a pelvis-velocity sine.
    """
    frames = len(root_track)
    for name, seq in (("root_track", root_track), ("root_rotations", root_rotations),
                      ("targets_m", targets_m), ("times_s", times_s)):
        if len(seq) != frames or frames == 0:
            raise ContractError(f"bite window {name} must match the track length")
    head_m = _finite(head_mass_kg, label="head_mass_kg")
    lever = _finite(head_lever_m, label="head_lever_m")
    if head_m <= 0.0 or lever <= 0.0:
        raise ContractError("head coupling needs positive mass and lever")
    gain = _finite(tail_moment_gain, label="tail_moment_gain")

    samples: list[dict[str, Any]] = []
    head_sweep_radps: list[float] = [0.0]
    prev_pitch: list[float] | None = None
    worst_residual = 0.0
    for k in range(frames):
        solved = solve_axial_chain(
            parents=parents,
            rest_translations=rest_translations,
            rest_rotations=rest_rotations,
            chain=chain,
            root_position_m=root_track[k]["root_position_m"],
            root_rotation=np.asarray(root_rotations[k], dtype=float),
            lateral_axis=lateral_axis,
            target_m=targets_m[k],
            envelopes=envelopes,
        )
        worst_residual = max(worst_residual, solved["residual_m"])
        if prev_pitch is not None:
            dt = float(times_s[k] - times_s[k - 1])
            rate = float(np.linalg.norm(np.asarray(solved["pitch_rad"]) - np.asarray(prev_pitch))) / dt if dt > 0 else 0.0
            head_sweep_radps.append(rate)
        prev_pitch = solved["pitch_rad"]
        samples.append({**solved, "time_s": float(times_s[k])})
    # Answering moment: oppose the head sweep (change of head angular
    # momentum for a point-mass head at the lever).
    head_inertia = head_m * lever * lever
    moments = [0.0]
    for k in range(1, frames):
        dt = float(times_s[k] - times_s[k - 1])
        accel = (head_sweep_radps[k] - head_sweep_radps[k - 1]) / dt if dt > 0 else 0.0
        moments.append(-gain * head_inertia * accel)
    tail = tail_ode_track(
        list(times_s), moments,
        inertia_kg_m2=float((tail_params or {}).get("inertia_kg_m2", 750.0)),
        damping_ratio=float((tail_params or {}).get("damping_ratio", 0.7)),
        natural_freq_hz=float((tail_params or {}).get("natural_freq_hz", 1.5)),
        max_angle_rad=float((tail_params or {}).get("max_angle_rad", math.radians(35.0))),
        body_inertia_kg_m2=(tail_params or {}).get("body_inertia_kg_m2"),
    )
    all_preferred = all(j.get("inside_preferred", True) for s in samples for j in s["joints"])
    return {
        "schema": SCHEMA,
        "samples": samples,
        "worst_residual_m": worst_residual,
        "all_reached": all(s["reached"] for s in samples),
        "all_inside_preferred": bool(all_preferred),
        "tail_track": tail,
        "coupling": "tail driven by head-sweep angular impulse; body counter-rotation propagated when body inertia given",
    }


__all__ = ["solve_axial_chain", "solve_bite_window"]
