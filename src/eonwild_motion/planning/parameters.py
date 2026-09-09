"""Stable serialization for optional planner parameters."""
from dataclasses import asdict
from typing import Any


def gait_parameters(gait: Any) -> dict[str, Any]:
    """Serialize declared values without adding unset fields to legacy plans."""
    return {key: value for key, value in asdict(gait).items() if value is not None}
