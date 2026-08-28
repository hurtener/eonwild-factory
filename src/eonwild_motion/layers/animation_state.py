from __future__ import annotations

from typing import Any

import numpy as np

from ..errors import ValidationFailure


def clip_state(glb, clip: str):
    tracks: dict[tuple[str, str], np.ndarray] = {}
    accessors: dict[tuple[str, str], int] = {}
    timelines: dict[tuple[str, str], np.ndarray] = {}
    for name, property_name, sampler in glb.animation_channels(clip):
        key = (name, property_name)
        accessor = int(sampler["output"])
        tracks[key] = np.asarray(glb.accessor_values(accessor), dtype=np.float64)
        accessors[key] = accessor
        timelines[key] = np.asarray(
            glb.accessor_values(int(sampler["input"])), dtype=np.float64
        ).reshape(-1)
    return tracks, accessors, timelines


def sample_locals(glb, tracks, sample: int):
    translations = []
    rotations = []
    scales = []
    for index, node in enumerate(glb.nodes):
        name = node.get("name", f"node_{index}")
        translations.append(
            tracks.get((name, "translation"), np.asarray([glb.rest_translation[index]]))[sample if (name, "translation") in tracks else 0].copy()
        )
        rotations.append(
            tracks.get((name, "rotation"), np.asarray([glb.rest_rotation[index]]))[sample if (name, "rotation") in tracks else 0].copy()
        )
        scales.append(
            tracks.get((name, "scale"), np.asarray([glb.rest_scale[index]]))[sample if (name, "scale") in tracks else 0].copy()
        )
    return translations, rotations, scales


def patch(accessors, node: str, property_name: str, values: np.ndarray) -> dict[str, Any]:
    key = (node, property_name)
    if key not in accessors:
        raise ValidationFailure(f"semantic channel has no animation accessor: {node}.{property_name}")
    return {"accessor": accessors[key], "property": property_name, "values": values}


def close_quaternion_loop(rows: np.ndarray) -> None:
    for sample in range(1, len(rows)):
        if float(np.dot(rows[sample - 1], rows[sample])) < 0.0:
            rows[sample] *= -1.0
    rows[-1] = rows[0]
