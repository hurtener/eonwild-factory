#!/usr/bin/env python3
"""Bounded actual-source probe for the shared semantic foot-frame law."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import numpy as np

from eonwild_motion.factory import compiler
from eonwild_motion.solve.airborne_gait import grounded_touchdown_target
from eonwild_motion.solve.constant_skin_targets import ConstantSkinTargetUnavailable
from eonwild_motion.solve.source_motion_query import SourceMotionUnavailable, _thaw


class Captured(RuntimeError):
    pass


def probe(law, plan):
    query = law._query
    gait = query._locomotion_gait
    period = 2.0 * gait.step_period_s
    zero = {side: [0.0, 0.0, 0.0] for side in ("left", "right")}

    def unrefined(time_s, limit):
        value = query._evaluate_owned(time_s, side=limit, target_offsets=zero)
        if isinstance(value, SourceMotionUnavailable):
            raise RuntimeError(value.reason)
        row = _thaw(value.row)
        for foot in row["feet"].values():
            foot.pop("target_offset_m", None)
        return value, row

    def transported(time_s, side, limit):
        value, row = unrefined(time_s, limit)
        _, rotation = law._foot_frame(query, np.asarray(value.worlds), side)
        declared = grounded_touchdown_target(
            query.context,
            row,
            side=side,
            body_response_sample=query._body_sample(None, row),
        )
        effector = np.asarray(declared["target_foot_world_m"], dtype=float)
        return effector + rotation @ law._local_material_references[side], row

    boundaries = {}
    samples = set([0.0, float(plan["duration_s"])])
    for side, offset in (("left", 0.0), ("right", gait.step_period_s)):
        lift = (offset + period * gait.duty_factor) % period
        touchdown = offset % period
        if touchdown <= lift:
            touchdown += period
        anchor = law._provider.anchor_for(side)
        target_lift, lift_row = transported(lift, side, "left_limit")
        support_lift = (
            anchor.material_origin_m[anchor.lowest_patch_index]
            + query.context.forward * lift_row["feet"][side]["forward_m"]
        )
        target_touchdown, touchdown_row = transported(
            touchdown, side, "left_limit"
        )
        support_touchdown = (
            anchor.material_origin_m[anchor.lowest_patch_index]
            + query.context.forward
            * touchdown_row["feet"][side]["forward_m"]
        )
        up_index = int(np.argmax(np.abs(query.context.up)))
        base_gap = float(
            anchor.material_origin_m[anchor.lowest_patch_index][up_index]
            - law._skin.ground
        )
        gap_shift = query.context.up * (0.0001 - base_gap)
        support_lift += gap_shift
        support_touchdown += gap_shift
        boundaries[side] = {
            "lift_off_s": lift,
            "lift_off_target_residual_m": float(
                np.linalg.norm(target_lift - support_lift)
            ),
            "touchdown_s": touchdown,
            "touchdown_target_residual_m": float(
                np.linalg.norm(target_touchdown - support_touchdown)
            ),
        }
        middle = 0.5 * (lift + touchdown)
        for event in (lift, touchdown):
            for epsilon in (1e-5, 1e-7):
                samples.update((event - epsilon, event, event + epsilon))
        samples.add(middle)

    values = law.values(sorted(t for t in samples if 0 <= t <= plan["duration_s"]))
    sample_rows = []
    for value in values:
        if isinstance(value, ConstantSkinTargetUnavailable):
            sample_rows.append({"time_s": value.time_s, "status": value.status, "reason": value.reason})
        else:
            sample_rows.append({
                "time_s": value.time_s,
                "status": value.status,
                "contacts": {side: bool(value.row["feet"][side]["contact"]) for side in ("left", "right")},
                "corrections_m": {side: list(map(float, value.corrections_m[side])) for side in ("left", "right")},
                "minimum_gaps_m": {side: float(value.observations[side]["minimum_gap_m"]) for side in ("left", "right")},
                "loaded_material_max_residuals_m": {
                    side: float(
                        value.observations[side][
                            "loaded_material_max_residual_m"
                        ]
                    )
                    for side in ("left", "right")
                },
            })
    return {
        "boundaries": boundaries,
        "loaded_support_membership": law.receipt()["loaded_support_membership"],
        "samples": sample_rows,
    }


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: probe_semantic_foot_frame.py ROOT MOTION_SET")
    root, motion_set = map(Path, argv[1:])
    captured = {}
    original = compiler.emit_source_cubics

    def capture(source, law, plan, **kwargs):
        captured.update(probe(law, plan))
        raise Captured

    compiler.emit_source_cubics = capture
    try:
        compiler.compile_motion_set(
            motion_set,
            "walk",
            root=root,
            output=root / "out" / "unused-probe-output",
        )
    except Captured:
        pass
    finally:
        compiler.emit_source_cubics = original
    print(json.dumps(captured, indent=2, allow_nan=False))


if __name__ == "__main__":
    main(sys.argv)
