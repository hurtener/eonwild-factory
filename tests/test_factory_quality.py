from copy import deepcopy
import math

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.quality import emitted_rotation_rates, require_supported_geometry, solver_checks
from eonwild_motion.factory.source import admit_geometry
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.whole_body_gait_transition import _build_glb, _encode
from test_v9_airborne_gait import fixture


def test_solver_missing_or_nonfinite_evidence_cannot_pass():
    keys = ("max_foot_target_residual_m", "max_unreachable_extension_m", "maximum_articulation_envelope_violation_degrees")
    valid = dict.fromkeys(keys, 0.)
    assert solver_checks(valid)["status"] == "PASS"
    assert solver_checks({})["status"] == "FAIL"
    for key in keys:
        for value in (math.nan, math.inf, True, -.01, 1):
            assert solver_checks({**valid, key: value})["status"] == "FAIL"


def test_final_rotation_rate_reads_serialized_motion():
    source, roles = fixture()
    root = source.name_to_node[roles["root"]]
    angle = math.radians(45)
    rows = np.array([[0, 0, 0, 1], [0, math.sin(angle / 2), 0, math.cos(angle / 2)]])
    raw = _build_glb(source, "rate", np.array([0., .1]), {(root, "rotation"): rows}, "test", {})
    result = emitted_rotation_rates(Glb.from_bytes(raw), 400)
    assert result["status"] == "FAIL"
    assert result["maximum_degrees_per_s"] == pytest.approx(450, abs=.01)
    assert emitted_rotation_rates(Glb.from_bytes(raw), 500)["status"] == "PASS"


@pytest.mark.parametrize("change", [{"matrix": [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]}, {"scale": [1,2,1]}, {"scale": [-1,1,1]}])
def test_unhandled_transform_is_rejected_not_silently_reinterpreted(change):
    source, roles = fixture()
    doc = deepcopy(source.document)
    doc["nodes"][0].update(change)
    bad = Glb.from_bytes(_encode(doc, source.binary))
    with pytest.raises(ContractError):
        admit_geometry(bad, roles, forward_axis=(0,0,1))
