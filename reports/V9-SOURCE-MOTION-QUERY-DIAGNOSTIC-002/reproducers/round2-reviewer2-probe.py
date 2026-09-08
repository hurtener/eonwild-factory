from __future__ import annotations

import copy
import json
import sys

sys.path.insert(0, "tests")

from eonwild_motion.planning.gait_transition import GaitTransition, build_transition_plan
from eonwild_motion.solve.source_motion_query import SourceMotionQuery
import test_source_motion_query as fixture_module


def outcome(call):
    try:
        value = call()
    except Exception as exc:
        return {"exception": type(exc).__name__, "message": str(exc)}
    return {
        "result": type(value).__name__,
        "status": getattr(value, "status", None),
        "step_sizes_s": getattr(value, "step_sizes_s", None),
    }


query, source, roles, gait, plan, solver = fixture_module._grounded_query()
result = {
    "reviewed_head": "270d4b2c9bdc13998cec2a3e816cfca5b4c2e362",
    "directional_event_room": {
        str(time): {
            side: outcome(lambda time=time, side=side: query.raw_probe(time, side=side))
            for side in ("left_limit", "right_limit")
        }
        for time in (0.352, 0.8)
    },
    "overflow_inputs": {},
    "transition_contract_mutations": {},
}
for method in ("derivative", "raw_probe"):
    result["overflow_inputs"][f"{method}.initial_h_s"] = outcome(
        lambda method=method: getattr(query, method)(0.123, initial_h_s=10**10000)
    )
for field in ("body_height_m", "duration_s", "same_foot_cycle_s"):
    bad = copy.deepcopy(plan)
    bad[field] = 10**10000
    result["overflow_inputs"][f"plan.{field}"] = outcome(
        lambda bad=bad: SourceMotionQuery(
            source,
            semantic_roles=roles,
            solver_gait=solver,
            locomotion_gait=gait,
            plan=bad,
            forward_axis=(0.0, 0.0, 1.0),
        )
    )
bad = copy.deepcopy(plan)
bad["samples"][3]["feet"]["left"]["target_offset_m"] = 10**10000
result["overflow_inputs"]["target_offset_m.evaluate"] = outcome(
    lambda: SourceMotionQuery(
        source,
        semantic_roles=roles,
        solver_gait=solver,
        locomotion_gait=gait,
        plan=bad,
        forward_axis=(0.0, 0.0, 1.0),
    ).evaluate(bad["samples"][3]["time_s"])
)
transition = GaitTransition("start", sample_hz=24, boundary_sample_hz=48)
transition_plan = build_transition_plan(
    transition, gait, fixture_module.FIXTURE_HEIGHT_M
)
for field, value in (
    ("steady_phase_s", 123.0),
    ("entry_speed_mps", 999.0),
    ("root_distance_m", -999.0),
    ("interface_schema", "bogus"),
):
    bad = copy.deepcopy(transition_plan)
    bad["transition_contract"][field] = value
    result["transition_contract_mutations"][field] = outcome(
        lambda bad=bad: SourceMotionQuery(
            source,
            semantic_roles=roles,
            solver_gait=solver,
            locomotion_gait=gait,
            plan=bad,
            transition=transition,
            forward_axis=(0.0, 0.0, 1.0),
        )
    )
print(json.dumps(result, indent=2, sort_keys=True))
