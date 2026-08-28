from __future__ import annotations

from typing import Any

import numpy as np

from ..errors import ContractError, ValidationFailure
from ..math.quaternion import (
    from_rotation_vector,
    inverse,
    multiply,
    power,
    to_rotation_vector,
)
from ..math.transforms import all_world_rotations


def _roles(rig: dict[str, Any]) -> tuple[str, str, list[str]]:
    roles = rig["roles"]
    neck_and_head = [*roles["neck"], roles["head"]]
    return roles["pelvis"], roles["chest"], neck_and_head


def _resolve_parent(rig: dict[str, Any], selector: str) -> str:
    roles = rig["roles"]
    if selector == "spine_parent":
        return rig["spineParent"]
    if selector.startswith("neck:"):
        try:
            return roles["neck"][int(selector.split(":", 1)[1])]
        except (ValueError, IndexError) as exc:
            raise ContractError(f"invalid parent selector: {selector}") from exc
    value = roles.get(selector)
    if not isinstance(value, str):
        raise ContractError(f"invalid parent selector: {selector}")
    return value


def _parent_pairs(rig: dict[str, Any]) -> list[tuple[str, str]]:
    roles = rig["roles"]
    expected = rig["expectedParents"]
    if len(roles["neck"]) != len(expected["neck"]):
        raise ContractError("neck parent contract length mismatch")
    pairs = [
        (roles["pelvis"], _resolve_parent(rig, expected["pelvis"])),
        (roles["chest"], _resolve_parent(rig, expected["chest"])),
    ]
    pairs.extend(
        (name, _resolve_parent(rig, selector))
        for name, selector in zip(roles["neck"], expected["neck"])
    )
    pairs.append((roles["head"], _resolve_parent(rig, expected["head"])))
    return pairs


def _clip_tracks(glb, rig: dict[str, Any], clip: str):
    pelvis, chest, neck = _roles(rig)
    required = [pelvis, chest, *neck]
    channels = glb.rotation_channels(clip)
    by_name = {name: sampler for name, sampler in channels}
    if any(name not in glb.name_to_node or name not in by_name for name in required):
        raise ValidationFailure("semantic role missing animation rotation")
    for name, parent in _parent_pairs(rig):
        actual = glb.node_parent_name(name)
        if actual != parent:
            raise ValidationFailure(
                f"hierarchy contract mismatch for {name}: expected {parent}, got {actual}"
            )
    contract = rig["accessorContract"]
    if contract["commonTimeline"] is not True:
        raise ValidationFailure("accessor contract requires commonTimeline=true")
    timeline = None
    tracks = {}
    accessors = {}
    for name, sampler in channels:
        interpolation = sampler.get("interpolation", "LINEAR")
        if interpolation != contract["interpolation"]:
            raise ValidationFailure(
                f"interpolation contract mismatch for {name}: {interpolation}"
            )
        output_index = int(sampler["output"])
        item, view, _, _, _ = glb.accessor_layout(output_index)
        stride = int(view.get("byteStride", 16))
        if (
            item["componentType"] != contract["componentType"]
            or item["type"] != contract["type"]
            or stride != contract["byteStride"]
        ):
            raise ValidationFailure(f"accessor contract mismatch for {name}")
        current = np.asarray(
            glb.accessor_values(int(sampler["input"])), dtype=np.float64
        ).reshape(-1)
        if timeline is None:
            timeline = current
        elif not np.array_equal(timeline, current):
            raise ValidationFailure(f"common timeline contract mismatch for {clip}")
        tracks[name] = np.asarray(
            glb.accessor_values(output_index), dtype=np.float64
        )
        accessors[name] = output_index
    if timeline is None:
        raise ValidationFailure(f"no rotation tracks: {clip}")
    if any(len(rows) != len(timeline) for rows in tracks.values()):
        raise ValidationFailure(f"rotation count/timeline mismatch for {clip}")
    return tracks, accessors


def _load_locals(glb, tracks, sample: int) -> list[np.ndarray]:
    output = []
    for index, node in enumerate(glb.nodes):
        name = node.get("name", f"node_{index}")
        output.append(
            tracks[name][sample]
            if name in tracks
            else np.asarray(glb.rest_rotation[index], dtype=np.float64)
        )
    return output


def _solve(glb, rig, clip, parameters, bounds):
    tracks, accessors = _clip_tracks(glb, rig, clip)
    pelvis_name, chest, neck = _roles(rig)
    names = [chest, *neck]
    values = {name: np.empty_like(tracks[name], dtype=np.float64) for name in names}
    pelvis_index = glb.name_to_node[pelvis_name]
    chest_index = glb.name_to_node[chest]
    reference = None
    axis = int(parameters["rotationVectorAxis"])
    residuals = parameters["neckResidualFractions"]
    if len(residuals) != len(neck):
        raise ContractError("neck residual count does not match semantic chain")
    for sample in range(len(next(iter(tracks.values())))):
        local = _load_locals(glb, tracks, sample)
        world = all_world_rotations(glb, local)
        if reference is None:
            reference = world[pelvis_index]
        pelvis_roll = to_rotation_vector(
            multiply(world[pelvis_index], inverse(reference))
        )[axis]
        relative = multiply(world[chest_index], inverse(world[pelvis_index]))
        vector = np.zeros(3, dtype=np.float64)
        vector[axis] = -float(parameters["gain"]) * pelvis_roll
        chest_world = multiply(
            from_rotation_vector(to_rotation_vector(relative) + vector),
            world[pelvis_index],
        )
        delta = multiply(chest_world, inverse(world[chest_index]))
        target = list(world)
        parent = glb.parents[chest_index]
        values[chest][sample] = (
            chest_world
            if parent is None
            else multiply(inverse(target[int(parent)]), chest_world)
        )
        target[chest_index] = chest_world
        for name, residual in zip(neck, residuals):
            index = glb.name_to_node[name]
            desired = multiply(power(delta, float(residual)), world[index])
            parent = glb.parents[index]
            values[name][sample] = (
                desired
                if parent is None
                else multiply(inverse(target[int(parent)]), desired)
            )
            target[index] = desired
    for rows in values.values():
        for sample in range(1, len(rows)):
            if np.dot(rows[sample - 1], rows[sample]) < 0:
                rows[sample] *= -1
        rows[-1] = rows[0]
    limits = {
        chest: float(bounds["chestLocalDeltaDegrees"]),
        **{name: float(bounds["neckLocalDeltaDegrees"]) for name in neck},
    }
    maxima = {}
    for name, rows in values.items():
        base = tracks[name]
        maximum = max(
            float(
                np.degrees(
                    np.linalg.norm(
                        to_rotation_vector(
                            multiply(inverse(base[sample]), rows[sample])
                        )
                    )
                )
            )
            for sample in range(len(rows))
        )
        maxima[name] = maximum
        if maximum > limits[name] + 1e-6:
            raise ValidationFailure(f"local delta bound exceeded {name}: {maximum}")
    return values, accessors, maxima


def apply(glb, rig, motion, layer):
    if layer["stage"] != "stabilization":
        raise ContractError("chest balance layer requires stabilization stage")
    results = {}
    metrics = {}
    for clip in motion["clips"]:
        values, accessors, maxima = _solve(
            glb,
            rig,
            clip["name"],
            layer["parameters"],
            layer["bounds"],
        )
        results[clip["name"]] = {
            name: {"accessor": accessors[name], "values": rows}
            for name, rows in values.items()
        }
        metrics[clip["semanticId"]] = {"maxLocalDeltaDegrees": maxima}
    return results, metrics
