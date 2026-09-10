"""Factory orchestration for the source-sampled body-support coordinator."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping, Sequence

import numpy as np

from ..dynamics.body_support_bridge import (
    SAMPLE_SEMANTICS,
    build_surface_mass_trial_evaluator,
)
from ..dynamics.body_support_coordinator import (
    SCHEMA as BODY_SUPPORT_POLICY,
    BodySupportSolution,
    coordinator_policy,
    solve_body_support_trajectory,
)
from ..dynamics.source_body_support_adapter import SourceFinalGeometryAdapter
from ..dynamics.surface_mass import COORDINATES, prepare_surface_mass_proxy
from ..errors import ContractError
from ..solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from ..solve.source_motion_query import SourceMotionQuery
from .io import digest, json_bytes


@dataclass(frozen=True)
class BodySupportCompilation:
    law: CanonicalConstantSkinTargetLaw | None
    surface_mass_profile: Mapping[str, Any]
    surface_mass_audit: Mapping[str, Any]
    solution: BodySupportSolution
    receipt: Mapping[str, Any]


def body_support_payloads(compilation: BodySupportCompilation) -> dict[str, bytes]:
    """Serialize the same bound evidence for checkpoints and final packages."""
    return {
        "surface-mass-profile.json": json_bytes(compilation.surface_mass_profile),
        "surface-mass-audit.json": json_bytes(compilation.surface_mass_audit),
        "body-support-coordination.json": json_bytes(compilation.receipt),
    }


def coordinate_body_support(
    *,
    source_bytes: bytes,
    rig_bytes: bytes,
    animal_bytes: bytes,
    query: SourceMotionQuery,
    law: CanonicalConstantSkinTargetLaw,
    plan: Mapping[str, Any],
    forward_axis: Sequence[float],
    up_axis: Sequence[float],
) -> BodySupportCompilation:
    """Run one bounded source-law coordination without emitted-GLB claims."""
    try:
        times = tuple(float(row["time_s"]) for row in plan["samples"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("body-support compilation requires a sampled plan") from exc
    if len(times) < 6 or any(not np.isfinite(value) for value in times):
        raise ContractError("body-support compilation requires at least five finite intervals")
    if any(after <= before for before, after in zip(times, times[1:])):
        raise ContractError("body-support compilation plan times must increase")
    duration = times[-1] - times[0]
    if times[0] != 0.0:
        raise ContractError("body-support compilation plan must start at zero")
    forward = np.asarray(forward_axis, dtype=float)
    up = np.asarray(up_axis, dtype=float)
    if (
        forward.shape != (3,)
        or not np.isfinite(forward).all()
        or not np.array_equal(forward, np.asarray((0.0, 0.0, 1.0)))
        or up.shape != (3,)
        or not np.isfinite(up).all()
        or not np.array_equal(up, np.asarray((0.0, 1.0, 0.0)))
    ):
        raise ContractError(
            "body-support compilation requires declared canonical +Y up and +Z forward axes"
        )
    profile, audit = prepare_surface_mass_proxy(
        source_bytes,
        rig_bytes,
        animal_bytes,
        source_sha256=digest(source_bytes),
        rig_sha256=digest(rig_bytes),
        animal_sha256=digest(animal_bytes),
        coordinate_system=COORDINATES,
    )
    adapter = SourceFinalGeometryAdapter(query, law)
    travel = forward * float(
        plan["samples"][-1]["root_forward_m"]
        - plan["samples"][0]["root_forward_m"]
    )
    policy = dict(coordinator_policy())
    trial_evaluator = build_surface_mass_trial_evaluator(
        source_bytes=source_bytes,
        surface_mass_profile=profile,
        duration_s=duration,
        body_control_cycle_s=adapter.body_control_cycle_s,
        body_height_m=adapter.body_height_m,
        sample_count=len(times) - 1,
        cycle_travel_m=travel,
        terminal_particle_tolerance_m=float(
            policy["terminal_particle_tolerance_m"]
        ),
        frozen_anchor_sha256=adapter.frozen_anchor_sha256,
        evaluate_final_geometry=adapter,
    )
    solution = solve_body_support_trajectory(
        trial_evaluator,
        frozen_anchor_sha256=adapter.frozen_anchor_sha256,
    )
    accepted_law = (
        adapter.law_for_coefficients(solution.coefficients)
        if solution.status == "AVAILABLE"
        else None
    )
    binding = adapter.binding_receipt(solution.coefficients)
    receipt: dict[str, Any] = {
        "policy": policy,
        "policy_id": BODY_SUPPORT_POLICY,
        "status": solution.status,
        "solution": _json_safe(asdict(solution)),
        "surface_mass_profile_sha256": digest(json_bytes(profile)),
        "surface_mass_audit_sha256": digest(json_bytes(audit)),
        "frozen_anchor_sha256": adapter.frozen_anchor_sha256,
        "trial_binding": dict(binding),
        "trial_sampling": {
            "duration_s": duration,
            "body_control_cycle_s": adapter.body_control_cycle_s,
            "interval_count": len(times) - 1,
            "cycle_travel_m": [float(value) for value in travel],
            "sample_semantics": SAMPLE_SEMANTICS,
        },
        "source_sampled_dynamics": solution.status,
        "source_sampled_final_geometry": (
            "AVAILABLE" if solution.status == "AVAILABLE" else "UNAVAILABLE"
        ),
        "emitted_full_mesh_floor": "NOT_RUN",
        "serialized_dynamics_parity": "NOT_RUN",
        "joint_contact_trial_policy": "frozen_neutral_controls_fail_closed.v1",
        "classification": (
            "bounded source-shaped engineering coordination proxy; not anatomy, "
            "physiology, emitted physical validation, or visual approval"
        ),
    }
    if solution.status == "AVAILABLE":
        receipt["accepted_binding"] = dict(binding)
    return BodySupportCompilation(accepted_law, profile, audit, solution, receipt)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
__all__ = [
    "BODY_SUPPORT_POLICY",
    "BodySupportCompilation",
    "body_support_payloads",
    "coordinate_body_support",
]
