"""Cross-clip continuity, turning, braking, and momentum-aware body coupling.

Replaces slerp-and-hope transitions with carried state:

* :class:`ContinuityPacket` — root pose, linear velocity, centroidal
  angular momentum, contacts, tail state, target commitment, phase and
  overlay state at a clip boundary.
* :func:`blend_packets` — minimum-jerk position + quaternion slerp +
  C1 velocity matching between boundary packets.
* :func:`capture_step_target` — recovery-step placement from the linear
  inverted-pendulum capture point.
* :func:`turn_plan` / :func:`brake_plan` — yaw-rate-limited heading
  changes and friction-limited deceleration with step accounting.
* :func:`redistribute_tail_head` — tail/head as angular-momentum
  redistribution (reduced-order point-mass tail), not a lagged sine. In
  flight total ``L`` is conserved: tail rotation is answered by opposite
  body rotation, computed here instead of assumed away.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..errors import ContractError
from .centroidal import _finite, _quat, _vec3, quat_mul


@dataclass(frozen=True)
class ContinuityPacket:
    root_position_m: tuple[float, float, float]
    root_orientation: tuple[float, float, float, float]
    linear_velocity_mps: tuple[float, float, float]
    angular_momentum_kg_m2ps: tuple[float, float, float]
    contacts: Mapping[str, str]  # effector -> "loaded" | "swing" | "ibeam"...
    tail_angle_rad: float = 0.0
    tail_angular_velocity_radps: float = 0.0
    target_commitment: str | None = None
    gait_phase: float = 0.0
    breathing_phase: float = 0.0
    gaze_mode: str = "forward"
    event_cursor: int = 0
    interruptible: bool = True
    angular_velocity_radps: tuple[float, float, float] = (0.0, 0.0, 0.0)


def _quat_conj(q: np.ndarray) -> np.ndarray:
    return np.array([-q[0], -q[1], -q[2], q[3]])


def _quat_rotate(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate vector v by unit quaternion q (x, y, z, w)."""
    qv = np.array([v[0], v[1], v[2], 0.0])
    return quat_mul(quat_mul(q, qv), _quat_conj(q))[:3]


def _exp_rotvec(v: np.ndarray) -> np.ndarray:
    """Rotation vector to unit quaternion."""
    angle = float(np.linalg.norm(v))
    if angle < 1e-12:
        return np.array([0.0, 0.0, 0.0, 1.0])
    axis = v / angle
    return np.array([*(axis * math.sin(angle / 2.0)), math.cos(angle / 2.0)])


def bridge_impulse(leaving: ContinuityPacket, entering: ContinuityPacket) -> dict[str, Any]:
    """Angular-momentum accounting for a clip boundary (the audit surface).

    Flight (no loaded contact either side) conserves total L: a mismatch
    is a hard error, never a silent blend. On the ground the boundary
    delivers ``entering.L − leaving.L`` through contact reactions, which
    is returned (not hidden) for the receipt.
    """
    l0 = np.asarray(leaving.angular_momentum_kg_m2ps, dtype=float)
    l1 = np.asarray(entering.angular_momentum_kg_m2ps, dtype=float)
    flight = "loaded" not in leaving.contacts.values() and "loaded" not in entering.contacts.values()
    if flight:
        scale = max(1.0, float(np.linalg.norm(l0)), float(np.linalg.norm(l1)))
        if float(np.linalg.norm(l1 - l0)) > 1e-6 * scale:
            raise ContractError("flight boundary would change angular momentum without contact")
        return {"flight": True, "delivered_kg_m2ps": [0.0, 0.0, 0.0]}
    return {"flight": False, "delivered_kg_m2ps": [float(v) for v in l1 - l0]}


def packet_from_mapping(value: Mapping[str, Any]) -> ContinuityPacket:
    try:
        return ContinuityPacket(
            root_position_m=tuple(float(v) for v in value["root_position_m"]),
            root_orientation=tuple(float(v) for v in value["root_orientation"]),
            linear_velocity_mps=tuple(float(v) for v in value["linear_velocity_mps"]),
            angular_momentum_kg_m2ps=tuple(float(v) for v in value["angular_momentum_kg_m2ps"]),
            contacts=dict(value["contacts"]),
            tail_angle_rad=float(value.get("tail_angle_rad", 0.0)),
            tail_angular_velocity_radps=float(value.get("tail_angular_velocity_radps", 0.0)),
            target_commitment=value.get("target_commitment"),
            gait_phase=float(value.get("gait_phase", 0.0)),
            breathing_phase=float(value.get("breathing_phase", 0.0)),
            gaze_mode=str(value.get("gaze_mode", "forward")),
            event_cursor=int(value.get("event_cursor", 0)),
            interruptible=bool(value.get("interruptible", True)),
            angular_velocity_radps=tuple(float(v) for v in value.get("angular_velocity_radps", (0.0, 0.0, 0.0))),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError(f"continuity packet is malformed: {exc}") from exc


def continuity_error(leaving: ContinuityPacket, entering: ContinuityPacket) -> dict[str, Any]:
    """Boundary mismatch between two clips; all terms must be ~0 for a seam."""
    dp = np.asarray(leaving.root_position_m) - np.asarray(entering.root_position_m)
    dv = np.asarray(leaving.linear_velocity_mps) - np.asarray(entering.linear_velocity_mps)
    dl = np.asarray(leaving.angular_momentum_kg_m2ps) - np.asarray(entering.angular_momentum_kg_m2ps)
    a = _quat(np.asarray(leaving.root_orientation), label="leaving orientation")
    b = _quat(np.asarray(entering.root_orientation), label="entering orientation")
    angle = 2.0 * math.acos(max(-1.0, min(1.0, abs(float(a @ b)))))
    contact_breaks = sorted(
        key
        for key in set(leaving.contacts) | set(entering.contacts)
        if leaving.contacts.get(key) != entering.contacts.get(key)
    )
    return {
        "position_error_m": float(np.linalg.norm(dp)),
        "orientation_error_deg": math.degrees(angle),
        "velocity_error_mps": float(np.linalg.norm(dv)),
        "angular_momentum_error": float(np.linalg.norm(dl)),
        "tail_angle_error_rad": abs(leaving.tail_angle_rad - entering.tail_angle_rad),
        "tail_velocity_error_radps": abs(leaving.tail_angular_velocity_radps - entering.tail_angular_velocity_radps),
        "contact_breaks": contact_breaks,
        "target_handoff": leaving.target_commitment == entering.target_commitment,
        "interruptibility": (leaving.interruptible, entering.interruptible),
    }


def _min_jerk(alpha: float) -> float:
    x = max(0.0, min(1.0, alpha))
    return 10 * x**3 - 15 * x**4 + 6 * x**5


def _slerp(a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
    dot = float(a @ b)
    if dot < 0.0:
        b = -b
        dot = -dot
    if dot > 0.9995:
        out = a + t * (b - a)
        return out / np.linalg.norm(out)
    theta = math.acos(max(-1.0, min(1.0, dot)))
    return (math.sin((1 - t) * theta) * a + math.sin(t * theta) * b) / math.sin(theta)


def blend_packets(
    leaving: ContinuityPacket,
    entering: ContinuityPacket,
    *,
    duration_s: float,
    sample_hz: int = 120,
) -> list[dict[str, Any]]:
    """C1-continuous bridge: min-jerk position, spin-matching orientation.

    Position uses cubic Hermite (endpoint velocities exact). Orientation
    is ``slerp(q0, q1, min_jerk(t))`` corrected by a Hermite rotation
    vector that is exactly zero at both ends with the packets' endpoint
    angular velocities — incoming/outgoing spin is carried, never zeroed
    (with zero spin this reduces to the plain slerp bridge).

    Angular momentum follows :func:`bridge_impulse`: constant in flight
    (mismatch raises), linearly interpolated on the ground with the
    delivered impulse returned by ``bridge_impulse`` for the receipt.
    """
    duration = _finite(duration_s, label="blend duration")
    if duration <= 0.0:
        raise ContractError("blend duration must be positive")
    count = max(2, int(math.ceil(duration * sample_hz)) + 1)
    impulse = bridge_impulse(leaving, entering)
    p0 = np.asarray(leaving.root_position_m, dtype=float)
    p1 = np.asarray(entering.root_position_m, dtype=float)
    v0 = np.asarray(leaving.linear_velocity_mps, dtype=float)
    v1 = np.asarray(entering.linear_velocity_mps, dtype=float)
    q0 = _quat(np.asarray(leaving.root_orientation), label="leaving orientation")
    q1 = _quat(np.asarray(entering.root_orientation), label="entering orientation")
    w0 = _quat_rotate(_quat_conj(q0), np.asarray(leaving.angular_velocity_radps, dtype=float))
    w1 = _quat_rotate(_quat_conj(q1), np.asarray(entering.angular_velocity_radps, dtype=float))
    l0 = np.asarray(leaving.angular_momentum_kg_m2ps, dtype=float)
    l1 = np.asarray(entering.angular_momentum_kg_m2ps, dtype=float)
    samples = []
    for i in range(count):
        t = i / (count - 1)
        # Cubic Hermite for position/velocity continuity.
        h00 = 2 * t**3 - 3 * t**2 + 1
        h10 = t**3 - 2 * t**2 + t
        h01 = -2 * t**3 + 3 * t**2
        h11 = t**3 - t**2
        pos = h00 * p0 + h10 * duration * v0 + h01 * p1 + h11 * duration * v1
        base = _slerp(q0, q1, _min_jerk(t))
        # Corrective rotation: zero at both ends, endpoint spin exact
        # (the exp Jacobian at the identity is the identity).
        u = h10 * duration * w0 + h11 * duration * w1
        quat = quat_mul(base, _exp_rotvec(u))
        quat = quat / float(np.linalg.norm(quat))
        samples.append(
            {
                "time_s": t * duration,
                "root_position_m": [float(v) for v in pos],
                "root_orientation": [float(v) for v in quat],
                "angular_momentum": [float(v) for v in (l0 if impulse["flight"] else (1 - t) * l0 + t * l1)],
                "tail_angle_rad": (1 - t) * leaving.tail_angle_rad + t * entering.tail_angle_rad,
                "tail_angular_velocity_radps": (1 - t) * leaving.tail_angular_velocity_radps
                + t * entering.tail_angular_velocity_radps,
            }
        )
    return samples


def capture_step_target(
    com_m: Sequence[float],
    com_velocity_mps: Sequence[float],
    *,
    com_height_m: float,
    gravity_mps2: float = 9.81,
    ground_m: float = 0.0,
) -> dict[str, Any]:
    """Linear inverted-pendulum capture point: where to step to stop.

    ``x_capture = x_com + v_horizontal · √(h/g)``. Only the horizontal
    velocity counts — vertical motion does not move the foot target, and
    the target lives on the ground plane. When upper-body compensation
    is insufficient, the planner must schedule this step instead of
    hiding imbalance in spine offsets.
    """
    com = _vec3(com_m, label="com_m")
    vel = _vec3(com_velocity_mps, label="com_velocity_mps")
    height = _finite(com_height_m, label="com_height_m")
    if height <= 0.0:
        raise ContractError("capture height must be positive")
    if not math.isfinite(gravity_mps2) or gravity_mps2 <= 0.0:
        raise ContractError("capture gravity must be positive")
    ground = _finite(ground_m, label="ground_m")
    tau = math.sqrt(height / gravity_mps2)
    horizontal = np.array([vel[0], 0.0, vel[2]])
    capture = np.array([com[0], ground, com[2]]) + horizontal * tau
    return {
        "capture_point_m": [float(v) for v in capture],
        "displacement_m": float(np.linalg.norm(horizontal * tau)),
        "time_constant_s": tau,
    }


def turn_plan(
    *,
    entry_speed_mps: float,
    heading_change_deg: float,
    max_yaw_rate_degps: float = 90.0,
    step_length_m: float = 1.2,
) -> dict[str, Any]:
    """Yaw-rate-limited turn with alternating step accounting."""
    speed = _finite(entry_speed_mps, label="entry_speed_mps")
    heading = _finite(heading_change_deg, label="heading_change_deg")
    yaw_rate = _finite(max_yaw_rate_degps, label="max_yaw_rate_degps")
    step = _finite(step_length_m, label="step_length_m")
    if speed < 0.0 or yaw_rate <= 0.0 or step <= 0.0:
        raise ContractError("turn inputs are out of range")
    duration = abs(heading) / yaw_rate if heading else 0.0
    distance = speed * duration
    steps = max(1, int(math.ceil(distance / step))) if distance > 0 else 1
    # Tight turns bleed speed: retain cos(heading/steps) per step, floored.
    retention = max(0.4, math.cos(math.radians(abs(heading) / steps))) if steps else 1.0
    return {
        "duration_s": duration,
        "travel_m": distance,
        "steps_required": steps,
        "exit_speed_mps": speed * retention,
        "speed_retention": retention,
        "yaw_rate_degps": math.copysign(yaw_rate, heading) if heading else 0.0,
    }


def brake_plan(
    *,
    entry_speed_mps: float,
    friction_coefficient: float = 0.8,
    step_length_m: float = 1.2,
    gravity_mps2: float = 9.81,
) -> dict[str, Any]:
    """Friction-limited stop: distance, time and support steps required."""
    speed = _finite(entry_speed_mps, label="entry_speed_mps")
    mu = _finite(friction_coefficient, label="friction_coefficient")
    step = _finite(step_length_m, label="step_length_m")
    if speed < 0.0 or mu <= 0.0 or step <= 0.0:
        raise ContractError("brake inputs are out of range")
    decel = mu * gravity_mps2
    distance = speed * speed / (2.0 * decel) if speed > 0 else 0.0
    duration = speed / decel if speed > 0 else 0.0
    return {
        "deceleration_mps2": decel,
        "braking_distance_m": distance,
        "braking_time_s": duration,
        "steps_required": max(1, int(math.ceil(distance / step))) if distance > 0 else 0,
    }


def redistribute_tail_head(
    residual_angular_momentum: Sequence[float],
    *,
    tail_mass_kg: float,
    tail_length_m: float,
    head_mass_kg: float,
    neck_length_m: float,
    max_tail_deg: float = 35.0,
    airborne: bool = True,
) -> dict[str, Any]:
    """Counter-rotate tail (and stabilize head) against residual momentum.

    Reduced-order model: the tail is a point mass at ``tail_length_m``;
    the impulse it can offset in ``response_time`` bounds the correction.
    In flight the correction is internal redistribution (total L
    conserved — reported, not created); on the ground the remainder must
    be answered by contact reactions, i.e. a step (reported as
    ``untransferred``).
    """
    residual = _vec3(residual_angular_momentum, label="residual_angular_momentum")
    tail_m = _finite(tail_mass_kg, label="tail_mass_kg")
    tail_l = _finite(tail_length_m, label="tail_length_m")
    head_m = _finite(head_mass_kg, label="head_mass_kg")
    neck_l = _finite(neck_length_m, label="neck_length_m")
    if min(tail_m, tail_l, head_m, neck_l) <= 0.0:
        raise ContractError("tail/head redistribution needs positive mass and length")
    residual_mag = float(np.linalg.norm(residual))
    tail_inertia = tail_m * tail_l * tail_l
    # Angle that would absorb the residual if the tail swept it in 0.25 s.
    response_time_s = 0.25
    required_rad = residual_mag * response_time_s / tail_inertia if tail_inertia > 0 else math.inf
    allowed_rad = math.radians(_finite(max_tail_deg, label="max_tail_deg"))
    applied_rad = min(required_rad, allowed_rad)
    transferred = applied_rad * tail_inertia / response_time_s
    direction = (-residual / residual_mag) if residual_mag > 0 else np.zeros(3)
    head_gain = 0.85  # stabilize gaze against ~85% of the tail sweep
    return {
        "tail_axis": [float(v) for v in direction],
        "tail_angle_deg": math.degrees(applied_rad),
        "tail_angle_capped": bool(required_rad > allowed_rad),
        "head_counter_deg": math.degrees(applied_rad) * head_gain,
        "transferred_kg_m2ps": transferred,
        "untransferred_kg_m2ps": max(0.0, residual_mag - transferred),
        "conservation": "internal redistribution; total L conserved" if airborne else "remainder requires contact reaction (step)",
    }


__all__ = [
    "ContinuityPacket",
    "blend_packets",
    "brake_plan",
    "bridge_impulse",
    "capture_step_target",
    "continuity_error",
    "packet_from_mapping",
    "redistribute_tail_head",
    "turn_plan",
]
