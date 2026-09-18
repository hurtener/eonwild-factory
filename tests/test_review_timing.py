"""The fast-walk review must not gain a duplicated frame from 48 + one ULP."""
from pathlib import Path
import importlib.util
import pytest

path = Path(__file__).resolve().parents[1] / 'tools/review_timing.py'
spec = importlib.util.spec_from_file_location('review_timing_test', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
native_sample_times = module.native_sample_times
native_still_times = module.native_still_times


def test_fast_walk_does_not_duplicate_the_loop_endpoint():
    duration = 1.6000000000000003
    times = native_sample_times(duration, 30)
    assert len(times) == 48
    assert times == [i / 30 for i in range(48)]
    assert times[-1] < 1.6


def test_fractional_sprint_timing_is_not_shortened_or_retimed():
    duration = 2 * .4791666666666667
    times = native_sample_times(duration, 30)
    assert len(times) == 29
    assert times[-1] < duration <= len(times) / 30
    assert times == [i / 30 for i in range(29)]


def test_a_real_fractional_frame_is_not_treated_as_roundoff():
    assert len(native_sample_times(1.6 + 1e-8, 30)) == 49


def test_requested_stills_retain_exact_native_seconds_including_terminal():
    assert native_still_times(23 / 24, [0, 23 / 96, 23 / 48, 23 / 24]) == [
        0, 23 / 96, 23 / 48, 23 / 24]


@pytest.mark.parametrize('times', [[], [0] * 13, [-.1], [1.01], [0, 0], [.5, .4],
    [float('nan')], [float('inf')], [True], '0.2'])
def test_invalid_native_still_times_fail_closed(times):
    with pytest.raises(ValueError):
        native_still_times(1., times)


@pytest.mark.parametrize('duration,fps', [(True,30),('1.6',30),(float('nan'),30),
    (float('inf'),30),(0,30),(-1,30),(61,30),(1,True),(1,30.),(1,11),(1,121)])
def test_invalid_timing_fails_closed(duration,fps):
    with pytest.raises(ValueError):
        native_sample_times(duration, fps)
