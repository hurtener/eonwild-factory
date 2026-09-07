"""Preview transport is exact timing evidence, not Unity parity evidence."""
from pathlib import Path
import importlib.util
import sys

import pytest


path = Path(__file__).resolve().parents[1] / 'tools/preview_clock.py'
spec = importlib.util.spec_from_file_location('preview_clock_test', path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
transport_clock = module.transport_clock


def test_transport_rebases_a_fractional_import_range_without_retiming_it():
    clock = transport_clock(17.25, 137.25, 1.0)
    assert clock.source_start_frame == 17.25
    assert clock.source_end_frame == 137.25
    assert clock.transport_start_frame == 0.0
    assert clock.transport_end_frame == 120.0
    assert clock.bake_step_frames == .5
    assert clock.receipt()['transport_duration_s'] == clock.receipt()['source_duration_s'] == 1.0


def test_transport_preserves_a_real_fractional_terminal_time_without_a_held_sample():
    clock = transport_clock(3.5, 153.75, 1.2520833333333334)
    assert clock.transport_end_frame == 150.25
    assert clock.bake_step_frames == 150.25 / 301
    assert clock.bake_step_frames < 1.0
    receipt = clock.receipt()
    assert receipt['transport_frame_end'] / receipt['source_fps'] == receipt['source_duration_s']
    assert 'held' in receipt['endpoint_policy']


@pytest.mark.parametrize('start,end,duration', [
    (0, 120, 1.1), (0, 0, 0), (10, 9, .1), (True, 120, 1), (0, float('inf'), 1),
])
def test_transport_clock_rejects_uncovered_or_invalid_source_intervals(start, end, duration):
    with pytest.raises(ValueError):
        transport_clock(start, end, duration)
