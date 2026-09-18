from pathlib import Path
import importlib.util
import sys

import pytest


path = Path(__file__).resolve().parents[1] / 'tools/connected_timeline.py'
spec = importlib.util.spec_from_file_location('connected_timeline_test', path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_exact_join_belongs_to_incoming_interval():
    segments = [
        {'label': 'start', 'timeline_start_s': 0., 'timeline_end_s': 1.},
        {'label': 'steady-tail', 'timeline_start_s': 1., 'timeline_end_s': 1.75},
        {'label': 'stop', 'timeline_start_s': 1.75, 'timeline_end_s': 2.75},
    ]
    assert module.segment_at(segments, 0.999)['label'] == 'start'
    assert module.segment_at(segments, 1.)['label'] == 'steady-tail'
    assert module.segment_at(segments, 1.75)['label'] == 'stop'
    with pytest.raises(ValueError):
        module.segment_at(segments, 2.75)


def test_declared_motor_travel_uses_exact_samples_and_bounded_interpolation():
    rows = [
        {'time_s': 0., 'root_forward_m': 0.},
        {'time_s': .5, 'root_forward_m': 2.},
        {'time_s': 1., 'root_forward_m': 5.},
    ]
    assert module.plan_distance(rows, .5) == 2.
    assert module.plan_distance(rows, .75) == pytest.approx(3.5)
    with pytest.raises(ValueError):
        module.plan_distance(rows, 1.01)
