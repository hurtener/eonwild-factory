from __future__ import annotations

import hashlib
import json
from pathlib import Path

from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from eonwild_motion.solve.source_motion_query import SourceMotionQuery, _thaw
from test_constant_skin_targets import _build, _inputs


def main() -> None:
    inputs = _inputs()
    base = inputs["query"]
    request = {
        "source": base._source,
        "semantic_roles": _thaw(base._roles),
        "solver_gait": base._solver_gait,
        "locomotion_gait": base._locomotion_gait,
        "plan": _thaw(base._plan),
        "up_axis": base._up_axis,
        "forward_axis": base._forward_axis,
        "transition": base._transition,
        "source_clip": base._source_clip,
        "legacy_overlay": base._legacy_overlay,
        "articulation_profile": base.context.articulation_profile,
        "contact_profile": _thaw(base._contact_profile),
    }

    class IgnoresOffsets(SourceMotionQuery):
        calls: list[bool] = []

        def _evaluate_owned(self, time, *, side, target_offsets):
            type(self).calls.append(target_offsets is not None)
            return super()._evaluate_owned(time, side=side, target_offsets=None)

    altered = IgnoresOffsets(**request)
    altered_inputs = dict(inputs)
    altered_inputs["query"] = altered
    law = _build(altered_inputs)
    fast = law.value(0.2)

    def force_prior_fallback(query, provider, skin, side, time_s, constants):
        return CanonicalConstantSkinTargetLaw._observe(
            query, provider, skin, side, time_s, constants
        )

    law._observe = force_prior_fallback
    fallback = law.value(0.2)
    result = {
        "schema": "eonwild.motion.source-query-offset-fastpath-reviewer2-repro.v1",
        "reviewed_head": "f125e97ec857ac006ab84126f1b052232cd66693",
        "parent": "6e3080196182688cad49a4b441753e27064824fc",
        "override": "SourceMotionQuery._evaluate_owned discards target_offsets",
        "public_methods_inherited": True,
        "fastpath_status": fast.status,
        "fastpath_reason": getattr(fast, "reason", None),
        "fallback_status": fallback.status,
        "override_received_offsets": IgnoresOffsets.calls,
        "fallback_row_offsets": {
            side: list(fallback.row["feet"][side]["target_offset_m"])
            for side in ("left", "right")
        },
    }
    out = Path(__file__).with_suffix(".json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print("result_sha256", hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
