"""Animation clip containers and validation helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import numpy as np

from eonproc_v3.gltf_io import quaternion_continuity


@dataclass
class AnimationClip:
    name: str
    times: np.ndarray
    rotations: dict[str, np.ndarray]
    translations: dict[str, np.ndarray] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    world_matrices: list[list[np.ndarray]] | None = None

    def normalize(self, exact_loop: bool | None = None) -> "AnimationClip":
        self.times = np.asarray(self.times, dtype=np.float64).reshape(-1)
        if len(self.times) < 2 or np.any(np.diff(self.times) <= 0.0):
            raise ValueError(f"{self.name}: times must be strictly increasing")
        loop = bool(self.extras.get("loop", False)) if exact_loop is None else bool(exact_loop)
        for name, values in list(self.rotations.items()):
            array = quaternion_continuity(np.asarray(values, dtype=np.float64))
            if array.shape != (len(self.times), 4):
                raise ValueError(f"{self.name}:{name}: invalid rotation shape {array.shape}")
            if loop:
                array[-1] = array[0]
            self.rotations[name] = array
        for name, values in list(self.translations.items()):
            array = np.asarray(values, dtype=np.float64)
            if array.shape != (len(self.times), 3):
                raise ValueError(f"{self.name}:{name}: invalid translation shape {array.shape}")
            if loop and self.extras.get("rootMotion", False) is False:
                array[-1] = array[0]
            self.translations[name] = array
        return self

    def gltf_spec(self) -> dict[str, Any]:
        self.normalize()
        return {
            "name": self.name,
            "times": self.times.astype(np.float32),
            "rotations": {name: values.astype(np.float32) for name, values in self.rotations.items()},
            "translations": {name: values.astype(np.float32) for name, values in self.translations.items()},
            "interpolation": "LINEAR",
            "extras": self.extras,
        }

    @property
    def duration(self) -> float:
        return float(self.times[-1] - self.times[0])
