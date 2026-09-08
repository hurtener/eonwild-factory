"""Strict frozen-source identity with one admitted uniform geometry scale."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import json
import math
import struct

import numpy as np

from ..errors import ContractError, ValidationFailure
from ..glb.container import Glb


def _encode(document: Mapping, binary: bytes) -> bytes:
    data = json.dumps(
        document, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    data += b" " * ((-len(data)) % 4)
    payload = bytes(binary) + b"\0" * ((-len(binary)) % 4)
    body = (struct.pack("<II", len(data), 0x4E4F534A) + data
            + struct.pack("<II", len(payload), 0x004E4942) + payload)
    return struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body


def _active_roots(source: Glb) -> tuple[int, ...]:
    scenes = source.document.get("scenes")
    scene = source.document.get("scene", 0)
    if (not isinstance(scenes, Sequence) or isinstance(scenes, (str, bytes))
            or type(scene) is not int or not 0 <= scene < len(scenes)
            or not isinstance(scenes[scene], Mapping)):
        raise ContractError("admitted source requires one valid active scene")
    roots = scenes[scene].get("nodes")
    if (not isinstance(roots, Sequence) or isinstance(roots, (str, bytes))
            or not roots or any(type(value) is not int or not 0 <= value < len(source.nodes)
                               for value in roots)
            or len(roots) != len(set(roots))):
        raise ContractError("admitted source scene roots are malformed")
    if set(roots) != {index for index, parent in enumerate(source.parents) if parent is None}:
        raise ContractError("admitted source scene must contain every topology root")
    return tuple(roots)


def validate_frozen_source_with_uniform_scale(
    source: Glb, expected_sha256: str,
) -> tuple[Glb, float]:
    """Return frozen bytes and admitted scale after proving current-state identity.

    The only admitted difference from ``source.raw`` is one positive uniform
    multiplier on every active scene-root scale. Document, binary, topology,
    names, local TRS, and cached container state otherwise remain exact.
    """
    if (not isinstance(source, Glb) or not isinstance(expected_sha256, str)
            or hashlib.sha256(source.raw).hexdigest() != expected_sha256):
        raise ContractError("admitted source frozen geometry hash is stale")
    raw_source = Glb.from_bytes(source.raw)
    if bytes(source.binary) != bytes(raw_source.binary):
        raise ContractError("admitted source binary differs from frozen geometry")
    current_roots, raw_roots = _active_roots(source), _active_roots(raw_source)
    if current_roots != raw_roots:
        raise ContractError("admitted source roots differ from frozen geometry")
    normalized = deepcopy(source.document)
    factors = []
    for root in raw_roots:
        raw_node, current_node = raw_source.document["nodes"][root], source.document["nodes"][root]
        if not isinstance(raw_node, Mapping) or not isinstance(current_node, Mapping):
            raise ContractError("admitted source root is malformed")
        try:
            raw_scale = np.asarray(raw_node.get("scale", [1, 1, 1]), dtype=float)
            current_scale = np.asarray(current_node.get("scale", [1, 1, 1]), dtype=float)
        except (TypeError, ValueError) as exc:
            raise ContractError("admitted source scale is invalid") from exc
        if (raw_scale.shape != (3,) or current_scale.shape != (3,)
                or not np.isfinite(raw_scale).all() or not np.isfinite(current_scale).all()
                or (raw_scale <= 0).any() or (current_scale <= 0).any()):
            raise ContractError("admitted source scale is invalid")
        factors.extend((current_scale / raw_scale).tolist())
        if "scale" in raw_node:
            normalized["nodes"][root]["scale"] = deepcopy(raw_node["scale"])
        else:
            normalized["nodes"][root].pop("scale", None)
    factor = float(factors[0])
    if (not math.isfinite(factor) or not .25 <= factor <= 4
            or not np.allclose(factors, factor, rtol=0, atol=1e-12)
            or normalized != raw_source.document):
        raise ContractError("admitted source must equal frozen geometry plus one uniform scale")
    try:
        parsed = Glb.from_bytes(_encode(source.document, bytes(source.binary)))
    except (TypeError, ValueError, ValidationFailure) as exc:
        raise ContractError("admitted source state is malformed") from exc
    if (source.document != parsed.document or source.nodes != parsed.nodes
            or source.parents != parsed.parents
            or source.name_to_node != parsed.name_to_node
            or source.rest_translation != parsed.rest_translation
            or source.rest_rotation != parsed.rest_rotation
            or source.rest_scale != parsed.rest_scale):
        raise ContractError("cached source state differs from its admitted document")
    return raw_source, factor
