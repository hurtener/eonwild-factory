"""Read baked GLB animation groups and reconstruct sampled skeletal poses."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from eonproc_v3.gltf_io import GlbAsset, matrix_from_trs


@dataclass(frozen=True)
class BakedAnimation:
    name: str
    times: np.ndarray
    rotations: dict[str, np.ndarray]
    translations: dict[str, np.ndarray]
    extras: dict[str, Any]

    @property
    def duration(self) -> float:
        return float(self.times[-1] - self.times[0])


class AnimationPackReader:
    def __init__(self, asset: GlbAsset):
        self.asset = asset
        self.animations = {animation.name: animation for animation in self._read_all()}

    def _read_all(self) -> list[BakedAnimation]:
        result: list[BakedAnimation] = []
        for animation in self.asset.json.get("animations", []):
            samplers = animation.get("samplers", [])
            rotations: dict[str, np.ndarray] = {}
            translations: dict[str, np.ndarray] = {}
            common_times: np.ndarray | None = None
            for channel in animation.get("channels", []):
                sampler = samplers[int(channel["sampler"])]
                times = self.asset.accessor(int(sampler["input"])).reshape(-1).astype(np.float64)
                values = self.asset.accessor(int(sampler["output"])).astype(np.float64)
                if common_times is None:
                    common_times = times
                elif not np.array_equal(common_times, times):
                    raise ValueError(f"{animation.get('name')}: mixed sampler timelines are not supported by preview reader")
                target = channel["target"]
                node_name = self.asset.nodes[int(target["node"])].get("name", f"node_{target['node']}")
                if target["path"] == "rotation":
                    rotations[node_name] = values
                elif target["path"] == "translation":
                    translations[node_name] = values
            if common_times is None:
                continue
            result.append(BakedAnimation(
                name=animation.get("name", f"animation_{len(result)}"),
                times=common_times,
                rotations=rotations,
                translations=translations,
                extras=animation.get("extras", {}),
            ))
        return result

    def animation(self, name: str) -> BakedAnimation:
        if name not in self.animations:
            raise KeyError(f"Unknown baked animation {name}; available: {sorted(self.animations)}")
        return self.animations[name]

    def sample_tracks(self, animation: BakedAnimation, time_seconds: float) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
        t = float(np.clip(time_seconds, animation.times[0], animation.times[-1]))
        index = int(np.searchsorted(animation.times, t, side="right") - 1)
        index = max(0, min(index, len(animation.times) - 1))
        if index == len(animation.times) - 1 or animation.times[index] == t:
            return (
                {name: values[index].copy() for name, values in animation.rotations.items()},
                {name: values[index].copy() for name, values in animation.translations.items()},
            )
        nxt = index + 1
        denominator = max(float(animation.times[nxt] - animation.times[index]), 1e-12)
        u = float((t - animation.times[index]) / denominator)
        rotations: dict[str, np.ndarray] = {}
        for name, values in animation.rotations.items():
            rotations[name] = Slerp(
                [0.0, 1.0], Rotation.from_quat(np.stack([values[index], values[nxt]]))
            )([u]).as_quat()[0]
        translations = {
            name: values[index] * (1.0 - u) + values[nxt] * u
            for name, values in animation.translations.items()
        }
        return rotations, translations

    def world_matrices_at(self, animation: BakedAnimation, time_seconds: float) -> list[np.ndarray]:
        rotation_tracks, translation_tracks = self.sample_tracks(animation, time_seconds)
        locals_: list[np.ndarray] = []
        for index, node in enumerate(self.asset.nodes):
            name = node.get("name", f"node_{index}")
            translation = translation_tracks.get(name, self.asset.rest_translation[index])
            rotation = Rotation.from_quat(rotation_tracks[name]) if name in rotation_tracks else self.asset.rest_rotation[index]
            locals_.append(matrix_from_trs(translation, rotation, self.asset.rest_scale[index]))
        return self.asset.world_matrices(locals_)

    def worlds_for_samples(self, animation: BakedAnimation, indices: np.ndarray | list[int]) -> list[list[np.ndarray]]:
        return [self.world_matrices_at(animation, float(animation.times[int(index)])) for index in indices]
