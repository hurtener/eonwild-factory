"""Skin-space contact refinement and cyclic final-artifact authority.

Contact offsets are inputs to a new constrained V9 solve, never post-export
bone edits. The declared floor and material witness identities do not move.
The engineering ground/penetration/skate thresholds are unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import math
import numpy as np

from ..contact_gauge import _source_frames
from ..dynamics.contact_authority import PatchFrame, AuthorityThresholds, evaluate_contact_authority
from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _clip_state
from ..planning.grounded_gait import smooth


def skin_frames(glb, contact_profile):
    name = glb.document["animations"][0]["name"]
    _, times = _clip_state(glb, name)
    return _source_frames(glb, contact_profile, animation_name=name, sample_times=list(map(float, times)))


def points(frame, side):
    return np.asarray([p["point_m"] for region in ("sole_points", "toe_points") for p in frame["feet"][side][region]], dtype=float)


def cyclic_authority(frames, loaded, displacement, thresholds):
    """Evaluate complete loaded phases crossing the seam with unwrapped travel.

    A duplicate endpoint is checked against the *actual* initial skin before
    using the unique cyclic samples. Three copies supply context; only complete
    phases intersecting the central copy contribute. No physical seam is omitted.
    """
    if len(frames) != len(loaded) or len(frames) < 3:
        raise ContractError("cyclic contact requires at least three aligned frames")
    duration = frames[-1].time_s - frames[0].time_s
    shift = np.asarray(displacement, dtype=float)
    if duration <= 0 or shift.shape != (3,) or not np.isfinite(shift).all():
        raise ContractError("invalid cyclic contact displacement or duration")
    seam = max(float(np.max(np.linalg.norm(np.asarray(getattr(frames[-1], key)) - np.asarray(getattr(frames[0], key)) - shift, axis=1))) for key in ("sole_m", "toe_m"))
    if loaded[-1] != loaded[0] or seam > .0005:
        return {"verdict": "FAIL", "maximum_skin_seam_error_m": seam, "reasons": ["cyclic contact state or serialized skin does not close"], "phases": []}
    count = len(frames) - 1
    expanded, flags = [], []
    for cycle in (-1, 0, 1):
        for frame, load in zip(frames[:-1], loaded[:-1]):
            expanded.append(PatchFrame(frame.time_s + cycle * duration,
                tuple(map(tuple, np.asarray(frame.sole_m) + cycle * shift)),
                tuple(map(tuple, np.asarray(frame.toe_m) + cycle * shift))))
            flags.append(load)
    intervals = []
    start = None
    for i, load in enumerate(flags + [False]):
        if load and start is None:
            start = i
        elif not load and start is not None:
            if start < 2 * count and i > count:
                intervals.append((start, i))
            start = None
    results = [evaluate_contact_authority(expanded[a:b], [True] * (b - a), thresholds=thresholds) for a, b in intervals]
    if not results:
        return {"verdict": "FAIL", "maximum_skin_seam_error_m": seam, "reasons": ["no loaded contact phase"], "phases": []}
    return {"verdict": "PASS" if all(r["verdict"] == "PASS" for r in results) else "FAIL",
        "maximum_skin_seam_error_m": seam, "cyclic_context": "complete phases intersecting middle of three root-unwrapped cycles",
        "phases": [p for r in results for p in r["phases"]],
        "reasons": [reason for r in results for reason in r.get("reasons", [])]}


def evaluate_skin(glb, profile, plan):
    frames, metadata = skin_frames(glb, profile)
    if len(frames) != len(plan["samples"]):
        raise ContractError("skin and plan timelines differ")
    axis = {"X": 0, "Y": 1, "Z": 2}[profile["geometry"]["ground"]["up_axis"]]
    ground = float(profile["geometry"]["ground"]["level_m"])
    thresholds = AuthorityThresholds(up_axis=axis, ground_m=ground)
    displacement = np.asarray(frames[-1]["root_m"]) - frames[0]["root_m"]
    per_foot = {}
    global_minimum = math.inf
    maximum_stance_gap = -math.inf
    for side in ("left", "right"):
        patches = [PatchFrame(f["time_s"], tuple(tuple(p["point_m"]) for p in f["feet"][side]["sole_points"]),
                    tuple(tuple(p["point_m"]) for p in f["feet"][side]["toe_points"])) for f in frames]
        loaded = [r["feet"][side]["contact"] for r in plan["samples"]]
        per_foot[side] = (cyclic_authority(patches, loaded, displacement, thresholds) if plan.get("loop", True)
                          else evaluate_contact_authority(patches, loaded, thresholds=thresholds))
        for f, load in zip(frames, loaded):
            gap = float(points(f, side)[:, axis].min() - ground)
            global_minimum = min(global_minimum, gap)
            if load:
                maximum_stance_gap = max(maximum_stance_gap, gap)
    penetration = max(0., -global_minimum)
    valid = all(r["verdict"] == "PASS" for r in per_foot.values()) and penetration <= thresholds.penetration_tolerance_m
    return {"verdict": "PASS" if valid else "FAIL", "authority": {"per_foot": per_foot},
        "maximum_penetration_m": penetration, "maximum_stance_gap_m": maximum_stance_gap,
        "ground_level_m": ground, "sample_count": len(frames),
        "classification": "final serialized skin, fixed floor, full multi-influence weights, unchanged engineering thresholds"}


def _cyclic_fill(times, values, loaded):
    """Fill unloaded intervals with C2 interpolation of adjacent corrections."""
    result = values.copy()
    indices = np.flatnonzero(loaded)
    if not len(indices):
        raise ContractError("refinement requires loaded samples")
    duration = times[-1] - times[0]
    for i in np.flatnonzero(~np.asarray(loaded)):
        before = indices[indices < i]
        after = indices[indices > i]
        a, b = (before[-1] if len(before) else indices[-1]), (after[0] if len(after) else indices[0])
        ta = times[a] - (duration if not len(before) else 0)
        tb = times[b] + (duration if not len(after) else 0)
        gain = smooth((times[i] - ta) / max(1e-9, tb - ta))
        result[i] = (1 - gain) * values[a] + gain * values[b]
    return result


def solve_with_skin_targets(source, *, semantic_roles, gait, up_axis, forward_axis, plan, contact_profile, iterations=7):
    from .airborne_gait import solve_airborne_gait
    current = deepcopy(plan)
    up, forward = np.asarray(up_axis), np.asarray(forward_axis)
    ground = float(contact_profile["geometry"]["ground"]["level_m"])
    index_up = int(np.argmax(np.abs(up)))
    if not np.allclose(up, np.eye(3)[index_up]):
        raise ContractError("skin floor refinement requires the declared positive cardinal up axis")
    count = len(current["samples"])
    anchors = {}
    offsets = {side: np.zeros((count, 3)) for side in ("left", "right")}
    trace = []
    for iteration in range(iterations + 1):
        for i, row in enumerate(current["samples"]):
            for side in offsets:
                row["feet"][side]["target_offset_m"] = offsets[side][i].tolist()
        root_raw, inplace_raw, _, receipt = solve_airborne_gait(source, source_clip=None,
            semantic_roles=semantic_roles, gait=gait, up_axis=tuple(up), forward_axis=tuple(forward),
            plan_override=current, legacy_overlay=False)
        emitted = Glb.from_bytes(root_raw)
        frames, _ = skin_frames(emitted, contact_profile)
        times = np.asarray([r["time_s"] for r in frames])
        maximum_error = 0.0
        corrections = {}
        for side in offsets:
            loaded = np.asarray([r["feet"][side]["contact"] for r in current["samples"]])
            first = int(np.flatnonzero(loaded)[0])
            if side not in anchors:
                patch = points(frames[first], side)
                witness = int(patch[:, index_up].argmin())
                origin = patch[witness] - forward * current["samples"][first]["feet"][side]["forward_m"]
                anchors[side] = (witness, origin)
            witness, origin = anchors[side]
            correction = np.zeros_like(offsets[side])
            for i, (frame, row, load) in enumerate(zip(frames, current["samples"], loaded)):
                patch = points(frame, side)
                gap = float(patch[:, index_up].min() - ground)
                if load:
                    target = origin + forward * row["feet"][side]["forward_m"]
                    error = target - patch[witness]
                    error -= up * float(error @ up)
                    error += up * (.0001 - gap)
                    correction[i] = error
                    maximum_error = max(maximum_error, float(np.linalg.norm(error)))
            correction = _cyclic_fill(times, correction, loaded)
            # A swing can still penetrate during fold/landing; retain the
            # higher clearance rather than adjusting the ground or root.
            for i, (frame, load) in enumerate(zip(frames, loaded)):
                if not load:
                    gap = float(points(frame, side)[:, index_up].min() - ground)
                    correction[i] += up * max(0., .0001 - gap - float(correction[i] @ up))
            corrections[side] = correction
        trace.append({"iteration": iteration, "maximum_loaded_target_error_m": maximum_error})
        if maximum_error <= .0002 or iteration == iterations:
            break
        for side in offsets:
            offsets[side] += .85 * corrections[side]
            if np.max(np.linalg.norm(offsets[side], axis=1)) > .06 * current["body_height_m"]:
                raise ContractError("skin-target refinement exceeded its body-normalized correction envelope")
            if current.get("loop", True):
                offsets[side][-1] = offsets[side][0]
    receipt["skin_target_refinement"] = {"classification": "material-witness correction before repeated constrained IK, not post-export projection",
        "converged": maximum_error <= .0002, "trace": trace,
        "maximum_offset_m": max(float(np.max(np.linalg.norm(v, axis=1))) for v in offsets.values()),
        "witnesses": {side: {"patch_index": int(value[0]), "anchor_origin_m": value[1].tolist()} for side, value in anchors.items()},
        "ground_level_m": ground}
    return root_raw, inplace_raw, current, receipt
