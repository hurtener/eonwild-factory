"""Definitions used by the emitted native recovery audit remain explicit."""
from pathlib import Path
import importlib.util

import pytest

from eonwild_motion.errors import ContractError


path = Path(__file__).resolve().parents[1] / "tools/audit_recovery_chain.py"
spec = importlib.util.spec_from_file_location("audit_recovery_chain_test", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_joint_and_direction_definitions_are_unambiguous():
    assert module.interior_degrees((0, 1, 0), (1, 0, 0)) == pytest.approx(90)
    assert module.direction_from_down_degrees(
        (0, -1, 0), forward=(0, 0, 1), up=(0, 1, 0)
    ) == pytest.approx(0)
    assert module.direction_from_down_degrees(
        (0, -1, 1), forward=(0, 0, 1), up=(0, 1, 0)
    ) == pytest.approx(45)
    assert module.direction_from_down_degrees(
        (0, -1, -1), forward=(0, 0, 1), up=(0, 1, 0)
    ) == pytest.approx(-45)


def test_zero_axes_and_vectors_fail_closed():
    with pytest.raises(ContractError, match="nonzero axis"):
        module.direction_from_down_degrees(
            (0, 0, 0), forward=(0, 0, 1), up=(0, 1, 0)
        )


def test_temporal_summary_uses_only_consecutive_samples_inside_scope():
    summary = module.temporal_summary([0, 10, 80, 90], [0, 1, 2, 3], [0, 1, 3])
    assert summary["minimum"] == {"value": 0.0, "index": 0, "time_s": 0.0}
    assert summary["maximum"] == {"value": 90.0, "index": 3, "time_s": 3.0}
    assert summary["maximum_absolute_native_rate_per_s"] == pytest.approx(10)
    assert summary["maximum_absolute_native_rate_witness"]["to_index"] == 1


def test_direction_rates_unwrap_across_signed_180_boundary():
    summary = module.temporal_summary(
        [179, -179, -177], [0, 1, 2], range(3), circular=True
    )
    assert summary["maximum_absolute_native_rate_per_s"] == pytest.approx(2)
