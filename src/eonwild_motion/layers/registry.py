from __future__ import annotations

from typing import Any

from ..errors import ContractError


def apply_registered_layer(
    implementation: str,
    glb,
    base_glb,
    rig: dict[str, Any],
    motion: dict[str, Any],
    layer: dict[str, Any],
):
    if implementation == "chest_balance_world_relative@1":
        from .chest_balance_world_relative_v1 import apply

        return apply(glb, rig, motion, layer)
    if implementation == "pelvis_balance_pre_ik@1":
        from .pelvis_balance_pre_ik_v1 import apply

        return apply(glb, base_glb, rig, motion, layer)
    if implementation == "leg_contact_resolve@1":
        from .leg_contact_resolve_v1 import apply

        return apply(glb, base_glb, rig, motion, layer)
    if implementation == "chest_tail_head_stabilization@1":
        from .chest_tail_head_stabilization_v1 import apply

        return apply(glb, base_glb, rig, motion, layer)
    raise ContractError(f"unknown layer implementation: {implementation}")
