"""Additional fail-closed engineering witnesses; never biological approval."""
from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from ..glb.animation import read_animation_tracks
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices, _world_position
from ..planning.articulation_profile import ArticulationProfile
from ..planning.grounded_gait import grounded_phase_sample_counts


def emitted_articulation_envelopes(
    glb: Glb,
    *,
    semantic_roles: Mapping[str, Any],
    plan: Mapping[str, Any],
    profile: ArticulationProfile,
    forward_axis: Any,
    up_axis: Any,
    tolerance_degrees: float = 0.01,
) -> dict[str, Any]:
    """Measure bound scalar guardrails on the reopened serialized animation."""
    if not isinstance(profile, ArticulationProfile):
        raise ContractError("final articulation check requires a validated profile")
    if not math.isfinite(tolerance_degrees) or tolerance_degrees < 0:
        raise ContractError("articulation tolerance must be finite and non-negative")
    try:
        legs = {side: [glb.name_to_node[name] for name in semantic_roles["legs"][side]["contactChain"]]
                for side in ("left", "right")}
    except (KeyError, TypeError) as exc:
        raise ContractError("final articulation check requires complete semantic legs") from exc
    if any(len(chain) != 4 for chain in legs.values()):
        raise ContractError("final articulation check requires hip/knee/ankle/foot chains")
    animations = glb.document.get("animations", [])
    if not isinstance(animations, list) or len(animations) != 1 or not isinstance(animations[0].get("name"), str):
        raise ContractError("final articulation check requires one named animation")
    tracks, times = _clip_state(glb, animations[0]["name"])
    rows = plan.get("samples")
    if not isinstance(rows, list) or len(rows) != len(times) or not np.allclose(
        times, [row["time_s"] for row in rows], rtol=0, atol=2e-6
    ):
        raise ContractError("final articulation timeline differs from the plan")
    forward = np.asarray(forward_axis, dtype=float)
    up = np.asarray(up_axis, dtype=float)
    if (forward.shape != (3,) or up.shape != (3,) or not np.isfinite(forward).all()
            or not np.isfinite(up).all() or np.linalg.norm(forward) < 1e-10
            or np.linalg.norm(up) < 1e-10):
        raise ContractError("final articulation axes are invalid")
    forward /= np.linalg.norm(forward)
    up /= np.linalg.norm(up)
    if abs(float(forward @ up)) > 1e-6:
        raise ContractError("final articulation axes are invalid")

    def unit(vector: np.ndarray) -> np.ndarray:
        length = float(np.linalg.norm(vector))
        if not np.isfinite(vector).all() or not math.isfinite(length) or length < 1e-10:
            raise ContractError("final articulation contains a degenerate segment")
        return vector / length

    def interior(a: np.ndarray, b: np.ndarray) -> float:
        return math.degrees(math.acos(float(np.clip(unit(a) @ unit(b), -1, 1))))

    maximum = 0.0
    witness = None
    counts = {"support": 0, "swing": 0}
    observed = {phase: {joint: [math.inf, -math.inf]
                        for joint in profile.support}
                for phase in counts}
    preferred_departure = 0.0
    for index, (time_s, row) in enumerate(zip(times, rows)):
        worlds = _world_matrices(glb, *_pose(glb, tracks, index))
        for side, (hip, knee, ankle, foot) in legs.items():
            hp, kp, ap, fp = (np.asarray(_world_position(worlds[node]))
                              for node in (hip, knee, ankle, foot))
            angles = {
                "hip_sagittal_degrees": math.degrees(math.atan2(
                    float((kp - hp) @ forward), -float((kp - hp) @ up))),
                "knee_interior_degrees": interior(hp - kp, ap - kp),
                "ankle_interior_degrees": interior(kp - ap, fp - ap),
            }
            if not all(math.isfinite(value) for value in angles.values()):
                raise ContractError("final articulation contains a non-finite angle")
            contact = row["feet"][side]["contact"]
            if type(contact) is not bool:
                raise ContractError("final articulation contact state must be boolean")
            phase_name = "support" if contact else "swing"
            counts[phase_name] += 1
            for joint, angle in angles.items():
                observed[phase_name][joint][0] = min(observed[phase_name][joint][0], angle)
                observed[phase_name][joint][1] = max(observed[phase_name][joint][1], angle)
                envelope = profile.effective(
                    contact=contact, swing_phase=row["feet"][side]["swing_phase"])[joint]
                violation = max(envelope.hard_min_deg - angle,
                                angle - envelope.hard_max_deg, 0.0)
                preferred_departure = max(
                    preferred_departure,
                    max(envelope.preferred_min_deg - angle,
                        angle - envelope.preferred_max_deg, 0.0),
                )
                if violation > maximum:
                    maximum = violation
                    witness = {"time_s": float(time_s), "sample_index": index,
                               "side": side, "phase": phase_name, "joint": joint,
                               "angle_degrees": angle,
                               "hard_degrees": [envelope.hard_min_deg, envelope.hard_max_deg]}
    missing_phases = []
    if (plan.get("program") == "grounded_gait"
            or plan.get("locomotion_program") == "grounded_gait"):
        per_leg = grounded_phase_sample_counts(rows)
        missing_phases = [
            f"{side}:{phase}"
            for side in ("left", "right")
            for phase in ("support", "swing")
            if per_leg[side][phase] == 0
        ]
    result = {
        "status": "PASS" if not missing_phases and maximum <= tolerance_degrees else "FAIL",
        "maximum_violation_degrees": maximum,
        "tolerance_degrees": tolerance_degrees,
        "maximum_preferred_departure_degrees": preferred_departure,
        "witness": witness,
        "phase_sample_counts": counts,
        "observed_degrees": {
            phase: {joint: values if math.isfinite(values[0]) else None
                    for joint, values in joints.items()}
            for phase, joints in observed.items()
        },
        "profile": profile.receipt(),
        "classification": "reopened scalar engineering guardrails; not biological ROM or 6DoF joint validation",
    }
    if missing_phases:
        result["missing_phase_samples"] = missing_phases
    return result


def require_supported_geometry(source: Glb) -> None:
    """The current FK/skin adapter consumes TRS, not opaque node matrices."""
    for index, node in enumerate(source.nodes):
        if "matrix" in node:
            raise ContractError(f"node {index} uses a matrix; normalize it to explicit TRS before admission")
        scale = np.asarray(node.get("scale", [1, 1, 1]), dtype=float)
        if scale.shape != (3,) or not np.isfinite(scale).all() or np.any(scale <= 0):
            raise ContractError(f"node {index} has unsupported scale")
        if np.max(scale) - np.min(scale) > 1e-6:
            raise ContractError(f"node {index} has nonuniform scale; bake scale before admission")


def solver_checks(receipt: Mapping[str, Any]) -> dict:
    limits = {"max_foot_target_residual_m": 0.001, "max_unreachable_extension_m": 0.001,
              "maximum_articulation_envelope_violation_degrees": 0.01}
    pitch_rate_key = "maximum_solved_foot_pitch_velocity_degrees_per_s"
    pitch_limit_key = "solved_foot_pitch_velocity_limit_degrees_per_s"
    if pitch_rate_key in receipt or pitch_limit_key in receipt:
        pitch_limit = receipt.get(pitch_limit_key)
        valid_limit = (not isinstance(pitch_limit, bool) and isinstance(pitch_limit, (int, float))
                       and math.isfinite(pitch_limit) and pitch_limit > 0)
        limits[pitch_rate_key] = float(pitch_limit) if valid_limit else None
    checks, values = {}, {}
    for key, limit in limits.items():
        value = receipt.get(key)
        valid = not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0
        values[key] = float(value) if valid else None
        checks[key] = bool(valid and limit is not None and value <= limit)
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "values": values, "limits": limits,
            "classification": "engineering feasibility only; missing evidence is a failure"}


def emitted_rotation_rates(glb: Glb, maximum_degrees_per_s: float) -> dict:
    if not math.isfinite(maximum_degrees_per_s) or maximum_degrees_per_s <= 0:
        raise ContractError("rotation rate limit must be finite and positive")
    peak = 0.0
    witness = None
    channel_count = 0
    for animation in glb.document.get("animations", []):
        for channel in animation["channels"]:
            sampler = animation["samplers"][channel["sampler"]]
            if sampler.get("interpolation", "LINEAR") == "CUBICSPLINE":
                raise ContractError(
                    "factory technical rate authority rejects CUBICSPLINE TRS channels until interval extrema are validated"
                )
            if channel["target"]["path"] != "rotation":
                continue
            if sampler.get("interpolation", "LINEAR") != "LINEAR":
                raise ContractError("factory rate witness requires emitted LINEAR quaternion channels")
            times = np.asarray(glb.accessor_values(sampler["input"]), dtype=float).reshape(-1)
            quaternions = np.asarray(glb.accessor_values(sampler["output"]), dtype=float)
            if len(times) < 2 or quaternions.shape != (len(times), 4) or not np.isfinite(quaternions).all() or not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
                raise ContractError("invalid final rotation timeline")
            norms = np.linalg.norm(quaternions, axis=1)
            if np.any(norms < 1e-10):
                raise ContractError("zero final quaternion")
            quaternions /= norms[:, None]
            angles = np.degrees(2 * np.arccos(np.clip(np.abs(np.sum(quaternions[:-1] * quaternions[1:], axis=1)), 0, 1)))
            speed = angles / np.diff(times)
            index = int(np.argmax(speed))
            channel_count += 1
            if float(speed[index]) > peak:
                peak = float(speed[index])
                node = int(channel["target"]["node"])
                witness = {"node": node, "bone": glb.nodes[node].get("name"), "times_s": times[index:index+2].tolist(),
                           "quaternions_xyzw": quaternions[index:index+2].tolist()}
    if not channel_count:
        raise ContractError("rotation witness requires at least one actual rotation channel")
    return {"status": "PASS" if peak <= maximum_degrees_per_s else "FAIL",
            "maximum_degrees_per_s": peak, "limit_degrees_per_s": maximum_degrees_per_s, "peak_witness": witness,
            "classification": "serialized per-channel rotation rate; not joint torque or muscle capacity"}


# Added acceptance gates, not substitutes for the unchanged contact/position
# gates. Estimates use a quadratic through the first/last three native samples;
# a duplicated endpoint alone cannot establish cyclic velocity continuity.
CYCLIC_ANGULAR_VELOCITY_TOLERANCE_DEG_S = 10.0
CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S = 0.001


def _endpoint_derivative(times: np.ndarray, deltas: np.ndarray) -> np.ndarray:
    if times.shape != (2,) or deltas.shape[0] != 2 or np.any(times == 0):
        raise ContractError("invalid one-sided derivative samples")
    return np.linalg.solve(np.column_stack((times, times * times)), deltas)[0]


def emitted_cyclic_continuity(glb: Glb, *, loop: bool) -> dict:
    """Measure native-time incoming/outgoing velocity on final serialized TRS.

    LINEAR rotations use shortest-path endpoint logarithms; CUBICSPLINE uses
    its authored, normalized one-sided quaternion derivatives. Root
    displacement is not erased: only its derivatives must match across a
    moving loop. This local seam witness does not bound interval extrema.
    """
    from ..layers.leg_contact_resolve_v3 import _qmul, _qinv, _q_to_rotvec
    if type(loop) is not bool:
        raise ContractError("loop declaration must be boolean")
    if not loop:
        return {"status": "NOT_APPLICABLE", "reason": "one-shot program; entry/exit contracts are separate"}
    # Retain the historic quadratic estimate for forensic comparison only.
    # glTF LINEAR playback has no quadratic endpoint tangent; the exact result
    # below is the acceptance value.
    animations = glb.document.get("animations", [])
    if len(animations) != 1 or not isinstance(animations[0].get("name"), str):
        raise ContractError("cyclic witness requires exactly one named emitted clip")
    animation = animations[0]
    parsed, _ = read_animation_tracks(glb, animation["name"], require_common_timeline=True)
    counts = {
        path: sum(1 for (_, candidate_path) in parsed if candidate_path == path)
        for path in ("rotation", "translation")
    }
    if not all(counts.values()):
        raise ContractError("cyclic witness requires actual rotation and translation channels")
    has_cubic = any(track.interpolation == "CUBICSPLINE" for track in parsed.values())
    angular = linear = 0.0
    witnesses = {"angular": None, "linear": None}
    if not has_cubic:
        for channel in animation["channels"]:
            path = channel["target"]["path"]
            if path not in counts:
                continue
            sampler = animation["samplers"][channel["sampler"]]
            times = np.asarray(glb.accessor_values(sampler["input"]), dtype=float).reshape(-1)
            values = np.asarray(glb.accessor_values(sampler["output"]), dtype=float)
            width = 4 if path == "rotation" else 3
            if (len(times) < 5 or values.shape != (len(times), width)
                or not np.isfinite(times).all() or not np.isfinite(values).all()
                or np.any(np.diff(times) <= 0)):
                raise ContractError("invalid final cyclic timeline")
            if path == "rotation":
                norms = np.linalg.norm(values, axis=1)
                if np.max(np.abs(norms - 1)) > 1e-4:
                    raise ContractError("invalid quaternion in cyclic witness")
                values /= norms[:, None]
                def deltas(endpoint, indices):
                    inverse = _qinv(tuple(values[endpoint]))
                    return np.array([_q_to_rotvec(_qmul(inverse, tuple(values[i]))) for i in indices])
                start_delta, end_delta = deltas(0, [1, 2]), deltas(-1, [-3, -2])
            else:
                start_delta, end_delta = values[1:3] - values[0], values[-3:-1] - values[-1]
            incoming = _endpoint_derivative(times[-3:-1] - times[-1], end_delta)
            outgoing = _endpoint_derivative(times[1:3] - times[0], start_delta)
            error = float(np.linalg.norm(incoming - outgoing))
            node = int(channel["target"]["node"])
            witness = {"node": node, "bone": glb.nodes[node].get("name"),
                "incoming": incoming.tolist(), "outgoing": outgoing.tolist()}
            if path == "rotation":
                error = math.degrees(error)
                if error > angular:
                    angular, witnesses["angular"] = error, witness
            elif error > linear:
                linear, witnesses["linear"] = error, witness
    from .emitted_tangent import local_cyclic_tangents
    exact = local_cyclic_tangents(glb, animation["name"])
    checks = {"angular_velocity": exact["angular_degrees_per_s"] <= CYCLIC_ANGULAR_VELOCITY_TOLERANCE_DEG_S,
              "linear_velocity": exact["linear_m_per_s"] <= CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S}
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
        "maximum_angular_velocity_seam_degrees_per_s": exact["angular_degrees_per_s"],
        "maximum_linear_velocity_seam_m_per_s": exact["linear_m_per_s"],
        "limits": {"angular_degrees_per_s": CYCLIC_ANGULAR_VELOCITY_TOLERANCE_DEG_S,
                   "linear_m_per_s": CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S},
        "peak_witnesses": exact["witnesses"],
        "classification": exact["classification"],
        "diagnostics": {"quadratic_three_sample_estimate": {
            "maximum_angular_velocity_seam_degrees_per_s": angular,
            "maximum_linear_velocity_seam_m_per_s": linear,
            "peak_witnesses": witnesses,
            "classification": ("not applicable to CUBICSPLINE; the exact serialized tangent is the acceptance value"
                               if has_cubic else "diagnostic quadratic fit through three native samples; not an emitted LINEAR pass claim"),
        }}}
