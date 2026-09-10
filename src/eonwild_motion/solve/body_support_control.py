"""Immutable query binding for optional periodic body-support coordinates."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Sequence

import numpy as np

from ..contracts.v9_models import canonical_hash
from ..dynamics.body_support_coordinator import (
    COEFFICIENT_COUNT,
    BodyDelta,
    coordinator_policy,
    periodic_body_delta,
)
from ..errors import ContractError


SCHEMA = "eonwild.motion.source-body-support-control.v1"
POLICY_ID = "periodic_body_support_control.v1"


def _axis(value: Sequence[float], label: str) -> tuple[float, float, float]:
    try:
        result = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"body-support {label} must be a finite unit vector") from exc
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ContractError(f"body-support {label} must be a finite unit vector")
    norm = float(np.linalg.norm(result))
    if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ContractError(f"body-support {label} must be a finite unit vector")
    return tuple(float(item) for item in result)


@dataclass(frozen=True)
class BodySupportControl:
    schema: str
    policy_id: str
    policy_sha256: str
    coefficients: tuple[float, ...]
    same_foot_cycle_s: float
    body_height_m: float
    up_axis: tuple[float, float, float]
    forward_axis: tuple[float, float, float]
    binding_sha256: str

    @classmethod
    def build(
        cls,
        coefficients: Sequence[float],
        *,
        same_foot_cycle_s: float,
        body_height_m: float,
        up_axis: Sequence[float],
        forward_axis: Sequence[float],
    ) -> "BodySupportControl":
        try:
            values = np.asarray(coefficients, dtype=float)
        except (TypeError, ValueError) as exc:
            raise ContractError("body-support control requires 12 finite coefficients") from exc
        if values.shape != (COEFFICIENT_COUNT,) or not np.isfinite(values).all():
            raise ContractError("body-support control requires 12 finite coefficients")
        cycle, height = float(same_foot_cycle_s), float(body_height_m)
        if not math.isfinite(cycle) or cycle <= 0.0:
            raise ContractError("body-support control requires a positive finite source cycle")
        if not math.isfinite(height) or height <= 0.0:
            raise ContractError("body-support control requires a positive finite body height")
        policy = dict(coordinator_policy())
        translation_bound = (
            float(policy["translation_coefficient_bound_body_heights"]) * height
        )
        rotation_bound = math.radians(
            float(policy["rotation_coefficient_bound_degrees"])
        )
        if (np.abs(values[:6]) > translation_bound).any() or (
            np.abs(values[6:]) > rotation_bound
        ).any():
            raise ContractError("body-support control coefficient exceeds its policy bound")
        up, forward = _axis(up_axis, "up axis"), _axis(forward_axis, "forward axis")
        if not math.isclose(float(np.dot(up, forward)), 0.0, rel_tol=0.0, abs_tol=1e-12):
            raise ContractError("body-support forward axis must be orthogonal to up")
        policy_sha256 = canonical_hash(policy)
        payload = {
            "schema": SCHEMA,
            "policy_id": POLICY_ID,
            "policy_sha256": policy_sha256,
            "coefficients": [float(item) for item in values],
            "same_foot_cycle_s": cycle,
            "body_height_m": height,
            "up_axis": list(up),
            "forward_axis": list(forward),
        }
        return cls(
            schema=SCHEMA,
            policy_id=POLICY_ID,
            policy_sha256=policy_sha256,
            coefficients=tuple(payload["coefficients"]),
            same_foot_cycle_s=cycle,
            body_height_m=height,
            up_axis=up,
            forward_axis=forward,
            binding_sha256=canonical_hash(payload),
        )

    def _payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "policy_id": self.policy_id,
            "policy_sha256": self.policy_sha256,
            "coefficients": list(self.coefficients),
            "same_foot_cycle_s": self.same_foot_cycle_s,
            "body_height_m": self.body_height_m,
            "up_axis": list(self.up_axis),
            "forward_axis": list(self.forward_axis),
        }

    def validate_for_query(
        self,
        *,
        same_foot_cycle_s: float,
        body_height_m: float,
        up_axis: Sequence[float],
        forward_axis: Sequence[float],
    ) -> None:
        expected = BodySupportControl.build(
            self.coefficients,
            same_foot_cycle_s=same_foot_cycle_s,
            body_height_m=body_height_m,
            up_axis=up_axis,
            forward_axis=forward_axis,
        )
        if self != expected or canonical_hash(self._payload()) != self.binding_sha256:
            raise ContractError("body-support control binding differs from its policy")

    def delta(self, time_s: float) -> BodyDelta:
        if canonical_hash(self._payload()) != self.binding_sha256:
            raise ContractError("body-support control binding differs from its policy")
        return periodic_body_delta(self.coefficients, time_s, self.same_foot_cycle_s)

    def receipt(self) -> dict[str, Any]:
        if canonical_hash(self._payload()) != self.binding_sha256:
            raise ContractError("body-support control binding differs from its policy")
        return {
            "schema": self.schema,
            "policy_id": self.policy_id,
            "policy_sha256": self.policy_sha256,
            "binding_sha256": self.binding_sha256,
            "coefficients": list(self.coefficients),
            "same_foot_cycle_s": self.same_foot_cycle_s,
            "body_height_m": self.body_height_m,
            "up_axis": list(self.up_axis),
            "forward_axis": list(self.forward_axis),
            "classification": "optional pre-leg periodic body-support coordinates",
        }


__all__ = ["BodySupportControl", "POLICY_ID", "SCHEMA"]
