import pytest

from eonwild_motion.solve.grounded_transition_clearance import (
    GroundedTransitionClearanceUnavailable,
    _monotone_floor,
)


def test_material_vertex_switch_is_supported_when_minimum_gap_is_monotone():
    def measure(height):
        # The minimum witness switches at 0.0004 m, but both material branches
        # increase with target height and the lower envelope remains monotone.
        a = height - 0.0003
        b = 0.5 * height - 0.0001
        return (min(a, b), 11 if a <= b else 29)

    floor = _monotone_floor(measure, 0.5, "left")
    assert measure(floor)[0] >= 0.0001
    assert floor == pytest.approx(0.0004, abs=1e-5)


def test_nonmonotone_distal_branch_fails_closed():
    def measure(height):
        if 0.2 < height < 0.4:
            return (-0.3, 7)
        return (height - 0.2499, 3)

    with pytest.raises(GroundedTransitionClearanceUnavailable, match="nonmonotone"):
        _monotone_floor(measure, 0.5, "right")


def test_missing_safe_steady_bracket_fails_closed():
    with pytest.raises(
        GroundedTransitionClearanceUnavailable, match="steady target"
    ):
        _monotone_floor(lambda height: (-0.01 + height * 0.001, 4), 0.5, "left")
