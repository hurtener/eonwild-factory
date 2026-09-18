"""Transport timing tests are not evidence of a biologically exact sprint."""
from dataclasses import replace
import math

import numpy as np
import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.planning.airborne_gait import AirborneGait, build_airborne_plan, sample_airborne_gait
from eonwild_motion.planning.gait_transition import GaitTransition, _Choreography
from eonwild_motion.planning.swing_transport import transport_progress, validate_transport_ramp


@pytest.mark.parametrize('ramp', [0., .06, .18, .24, .45])
def test_transport_preserves_distance_monotonicity_and_contact_rest(ramp):
    xs = np.array([transport_progress(float(u), ramp) for u in np.linspace(0., 1., 1001)])
    assert xs[0] == 0. and xs[-1] == 1.
    assert np.all(np.diff(xs) >= 0.)
    assert np.max(np.abs(xs + xs[::-1] - 1)) < 2e-14
    h = 1e-5
    for end in (0., 1.):
        inward = h if end == 0 else -h
        a, b, c = [transport_progress(end + i * inward, ramp) for i in range(3)]
        assert abs((-3*a + 4*b - c) / (2*inward)) < 1e-6
        assert abs((a - 2*b + c) / (inward*inward)) < .1


@pytest.mark.parametrize('ramp', [.06, .18, .24, .45])
def test_velocity_ramp_joins_have_matching_position_velocity_and_acceleration(ramp):
    h = 1e-5
    for centre in (ramp, 1-ramp):
        f = lambda u: transport_progress(u, ramp)
        before = (3*f(centre)-4*f(centre-h)+f(centre-2*h))/(2*h)
        after = (-3*f(centre)+4*f(centre+h)-f(centre+2*h))/(2*h)
        assert abs(before-after) < 1e-7
        assert abs(before-1/(1-ramp)) < 1e-7
        assert abs((f(centre-h)-2*f(centre)+f(centre+h))/(h*h)) < .01


@pytest.mark.parametrize('value', [True, None, '0.2', float('nan'), float('inf'), -.1, .01, .5])
def test_invalid_ramps_fail_closed(value):
    with pytest.raises(ContractError):
        validate_transport_ramp(value)
    with pytest.raises(ContractError):
        AirborneGait(swing_transport_ramp_fraction=value)


@pytest.mark.parametrize('value', [True, None, '0.2', float('nan'), float('inf'), -.001, 1.001])
def test_invalid_phases_fail_closed(value):
    with pytest.raises(ContractError):
        transport_progress(value, .18)


def test_roundoff_is_not_a_new_contact_interval():
    assert transport_progress(-1e-15, .18) == 0
    assert transport_progress(1+1e-15, .18) == 1


def test_zero_sentinel_is_exact_legacy_position_curve():
    for u in np.linspace(0., 1., 101):
        u = float(u)
        assert transport_progress(u, 0.) == u*u*u*(10+u*(-15+6*u))


def test_coordination_does_not_shorten_stride_slow_root_or_change_contacts():
    original = AirborneGait(step_length_body_heights=1.55, step_period_s=23/48,
                           flight_fraction=.22, cycles=1)
    changed = replace(original, swing_transport_ramp_fraction=.18)
    a, b = build_airborne_plan(original, 2.6), build_airborne_plan(changed, 2.6)
    assert a['duration_s'] == b['duration_s']
    assert a['flight_seconds_per_step'] == b['flight_seconds_per_step']
    altered = False
    for x, y in zip(a['samples'], b['samples']):
        for field in ('time_s','root_forward_m','pelvis_height_offset_m','support_count','flight'):
            assert x[field] == y[field]
        for side in ('left','right'):
            f, g = x['feet'][side], y['feet'][side]
            for field in ('contact','touchdown_time_s','height_m','toe_flex_degrees','foot_pitch_degrees','swing_phase'):
                assert f[field] == g[field]
            if f['contact']:
                assert f['forward_m'] == g['forward_m']
            else:
                altered |= abs(f['forward_m']-g['forward_m']) > .01
    assert altered
    assert b['samples'][-1]['root_forward_m'] == 2*1.55*2.6


@pytest.mark.parametrize('kind', ['start', 'stop'])
def test_transition_uses_same_transport_as_its_bound_airborne_gait(kind):
    gait = AirborneGait(swing_transport_ramp_fraction=.18)
    c = _Choreography(GaitTransition(kind), gait, 2.6)
    if kind == 'stop':
        actual, wanted = c.sample(0), sample_airborne_gait(gait, 0, 2.6)
        for side in ('left','right'):
            assert abs(actual['feet'][side]['forward_m']-wanted['feet'][side]['forward_m']) < 1e-10
    else:
        for phase in (.55,.69,.8,.97,1.):
            t = c.ramp + phase*c.period
            actual, wanted = c.sample(c.delay+t), sample_airborne_gait(gait,t,2.6)
            for side in ('left','right'):
                got = actual['feet'][side]['forward_m']-actual['root_forward_m']
                expected = wanted['feet'][side]['forward_m']-wanted['root_forward_m']
                assert abs(got-expected) < 1e-10
