"""Pose-matched and phase-matched transition clip synthesis."""
from __future__ import annotations

import math
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from eonproc_v3.curves import minimum_jerk
from .clip import AnimationClip


def _sample_index(clip: AnimationClip, phase: float) -> int:
    return int(np.clip(round(phase * (len(clip.times) - 1)), 0, len(clip.times) - 1))


def pose_transition(
    name: str,
    source: AnimationClip,
    target: AnimationClip,
    duration: float,
    sample_hz: int,
    source_phase: float = 0.0,
    target_phase: float = 0.0,
    root_name: str | None = None,
    tags: tuple[str, ...] = (),
) -> AnimationClip:
    count = int(round(duration * sample_hz)) + 1
    times = np.linspace(0.0, duration, count)
    mix = np.asarray([minimum_jerk(float(t / max(duration, 1e-9))) for t in times])
    si = _sample_index(source, source_phase)
    ti = _sample_index(target, target_phase)
    bones = sorted(set(source.rotations) | set(target.rotations))
    rotations: dict[str, np.ndarray] = {}
    for bone in bones:
        q0 = source.rotations.get(bone)
        q1 = target.rotations.get(bone)
        if q0 is None:
            start = q1[ti]
        else:
            start = q0[si]
        if q1 is None:
            end = start
        else:
            end = q1[ti]
        key_rots = Rotation.from_quat(np.stack([start, end]))
        interpolation = Slerp([0.0, 1.0], key_rots)
        rotations[bone] = interpolation(mix).as_quat()
    translations: dict[str, np.ndarray] = {}
    nodes = sorted(set(source.translations) | set(target.translations))
    for node in nodes:
        a = source.translations.get(node)
        b = target.translations.get(node)
        start = (a[si] if a is not None else b[ti]).copy()
        end = (b[ti] if b is not None else start).copy()
        translations[node] = start[None, :] * (1.0 - mix[:, None]) + end[None, :] * mix[:, None]
    extras = {
        "generator": "Eonwild procedural animation toolkit v4",
        "version": "4.0.0",
        "loop": False,
        "rootMotion": False,
        "transition": True,
        "transitionType": "C2 minimum-jerk pose match",
        "sourceClip": source.name,
        "targetClip": target.name,
        "sourcePhase": source_phase,
        "targetPhase": target_phase,
        "tags": list(tags),
    }
    diagnostics = {
        "clip": name,
        "source": source.name,
        "target": target.name,
        "duration_seconds": duration,
        "rotation_start_exact": True,
        "rotation_end_exact": True,
        "translation_start_exact": True,
        "translation_end_exact": True,
        "endpoint_velocity": "zeroed by quintic blend; runtime phase crossfade is preferred between moving loops",
    }
    return AnimationClip(name=name, times=times, rotations=rotations, translations=translations, extras=extras, diagnostics=diagnostics).normalize()


def phase_matched_loop_transition(
    name: str,
    source: AnimationClip,
    target: AnimationClip,
    duration: float,
    sample_hz: int,
    root_name: str,
    tags: tuple[str, ...] = (),
) -> AnimationClip:
    """Blend two loops while advancing both at the same normalized phase."""
    count = int(round(duration * sample_hz)) + 1
    times = np.linspace(0.0, duration, count)
    phase = times / max(duration, 1e-9)
    mix = np.asarray([minimum_jerk(float(value)) for value in phase])

    def interp_quat(values: np.ndarray, p: float) -> np.ndarray:
        f = p * (len(values) - 1)
        i0 = int(math.floor(f))
        i1 = min(i0 + 1, len(values) - 1)
        local = f - i0
        return Slerp([0.0, 1.0], Rotation.from_quat(np.stack([values[i0], values[i1]])))([local]).as_quat()[0]

    bones = sorted(set(source.rotations) | set(target.rotations))
    rotations: dict[str, list[np.ndarray]] = {bone: [] for bone in bones}
    for p, blend in zip(phase, mix):
        for bone in bones:
            a_values = source.rotations.get(bone, target.rotations[bone])
            b_values = target.rotations.get(bone, source.rotations[bone])
            a = interp_quat(a_values, float(p))
            b = interp_quat(b_values, float(p))
            q = Slerp([0.0, 1.0], Rotation.from_quat(np.stack([a, b])))([float(blend)]).as_quat()[0]
            rotations[bone].append(q)
    rest_root = source.translations[root_name][0]
    translations = {root_name: np.repeat(rest_root[None, :], count, axis=0)}
    return AnimationClip(
        name=name, times=times,
        rotations={bone: np.asarray(values) for bone, values in rotations.items()},
        translations=translations,
        extras={
            "generator": "Eonwild procedural animation toolkit v4", "version": "4.0.0",
            "loop": False, "rootMotion": False, "transition": True,
            "transitionType": "phase-matched moving-loop blend",
            "sourceClip": source.name, "targetClip": target.name, "tags": list(tags),
        },
        diagnostics={"clip": name, "phase_matched": True, "duration_seconds": duration},
    ).normalize()
