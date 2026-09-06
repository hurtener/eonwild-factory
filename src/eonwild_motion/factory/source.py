"""Admit calibrated geometry once; motion programs need no input animation.

A historical take can supply a declared reference pose during admission. Its
choreography, timing and root trajectory are not inputs to later compilation.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices, _world_position
from ..solve.whole_body_gait_transition import _encode
from .io import frame_axes


def admit_geometry(source: Glb, roles: Mapping[str, Any], *, reference_clip: str | None = None,
                   forward_axis: Any = None, up_axis: Any = (0, 1, 0)) -> tuple[bytes, dict[str, Any]]:
    try:
        root = source.name_to_node[roles["root"]]
    except KeyError as exc:
        raise ContractError("admission requires a bound root") from exc
    if reference_clip is None:
        t, r, s = source.rest_translation, source.rest_rotation, source.rest_scale
        if forward_axis is None:
            raise ContractError("neutral source admission requires an explicit forward axis")
    else:
        tracks, times = _clip_state(source, reference_clip)
        t, r, s = _pose(source, tracks, 0)
        if forward_axis is None:
            first = _world_matrices(source, t, r, s)
            last = _world_matrices(source, *_pose(source, tracks, len(times) - 1))
            forward_axis = np.asarray(_world_position(last[root])) - _world_position(first[root])
    forward, up = frame_axes(forward_axis, up_axis)
    doc = deepcopy(source.document)
    for i, node in enumerate(doc["nodes"]):
        node.pop("matrix", None)
        node["translation"] = [float(v) for v in t[i]]
        node["rotation"] = [float(v) for v in r[i]]
        node["scale"] = [float(v) for v in s[i]]
    doc.pop("animations", None)
    # Old event/state tracks describe the removed performance, not this source.
    doc.pop("extras", None)
    doc["extras"] = {"eonwildGeometry": {"schema": "eonwild.motion.geometry.v1",
        "reference_clip": reference_clip, "forward_axis": forward.tolist(), "up_axis": up.tolist(),
        "claim": "calibrated geometry; no behavioral or biological validation"}}
    encoded = _encode(doc, source.binary)
    reopened = Glb.from_bytes(encoded)
    if reopened.document.get("animations"):
        raise ContractError("admitted geometry must not contain animations")
    return encoded, doc["extras"]["eonwildGeometry"]


def geometry_height(source: Glb, roles: Mapping[str, Any], up_axis: Any) -> float:
    """Match the emitter's pelvis-to-distal-digit carrier measurement."""
    worlds = _world_matrices(source, source.rest_translation, source.rest_rotation, source.rest_scale)
    _, up = frame_axes(source.document["extras"]["eonwildGeometry"]["forward_axis"], up_axis)
    try:
        pelvis = np.asarray(_world_position(worlds[source.name_to_node[roles["pelvis"]]]))
        toes = [source.name_to_node[name] for leg in roles["legs"].values()
                for chain in leg["toeChains"] for name in chain]
    except (KeyError, TypeError) as exc:
        raise ContractError("incomplete biped geometry binding") from exc
    if not toes:
        raise ContractError("digit geometry is required")
    ground = min(float(np.asarray(_world_position(worlds[n])) @ up) for n in toes)
    height = float(pelvis @ up - ground)
    if height <= 0:
        raise ContractError("pelvis must be above the toe plane")
    return height
