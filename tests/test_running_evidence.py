"""Independent published example and conservation at the transfer boundary."""
import json
from pathlib import Path
import numpy as np
import pytest
from eonwild_motion.planning.running_evidence import birds_prior, EmpiricalSupport, resolve_evidence
from eonwild_motion.planning.running import resolve_running
from eonwild_motion.planning.running_support import RunningSupportCycle

ROOT = Path(__file__).resolve().parents[1]


def test_published_birds_example():
    p = birds_prior(8000,3.1,5)
    assert p['duty_factor'] == pytest.approx(.543,abs=.0005)
    assert p['contact_s'] == pytest.approx(.427,abs=.0005)
    assert p['same_foot_stride_m'] == pytest.approx(4.083,abs=.0005)


@pytest.mark.parametrize('animal,leg',[('allo',1.985),('tarbo',2.415)])
def test_transferred_aerial_support_preserves_impulse_and_periodicity(animal,leg):
    profile = json.loads((ROOT/f'catalog/embodiment/{animal}.v1.json').read_text())
    recipe = json.loads((ROOT/'catalog/behaviors/running-review.v10.json').read_text())
    gait = resolve_running(profile,recipe)
    e = resolve_evidence(profile,gait,leg)
    c = RunningSupportCycle(gait,profile['authoring']['bodyHeightM'],recipe['coordination'],e)
    x = np.linspace(0,1,10001)
    rows = np.array([c.vertical(float(v),offset=False) for v in x])
    assert np.trapezoid(rows[:,3],x) == pytest.approx(1,abs=1e-7)
    assert np.trapezoid(rows[:,1],x) == pytest.approx(0,abs=1e-7)
    assert e['predicted']['duty_factor'] > .5  # Conflict stays visible.
    assert e['applied']['duty_factor'] == pytest.approx(.43)
    assert c.vertical(c.contact)[1] > 0
    assert c.vertical(0)[1] < 0
    assert .25 < x[np.argmax(rows[:,3])]/c.contact < .35
    assert np.max(np.abs(rows[0]-rows[-1])) < 1e-10
    eps = 1e-6
    for phase in [0.,.2,c.contact,1.]:
        a,b = c.vertical(phase-eps),c.vertical(phase+eps)
        center = c.vertical(phase)
        assert (b[0]-a[0])/(2*eps*c.step) == pytest.approx(center[1],abs=1e-6)
        assert (b[1]-a[1])/(2*eps*c.step) == pytest.approx(center[2],abs=.001)
    # No roll reset at the contact/recovery event.
    t=c.contact*c.step
    foot=lambda t: c.sample(t)['feet']['left']
    for key in ('foot_pitch_degrees','stance_roll_swing_pitch_degrees','pad_pitch_degrees'):
        assert abs(foot(t-eps)[key]-foot(t+eps)[key])<.001
    # Peak heel rise belongs to grounded propulsion, not free-leg extension.
    assert foot(.9*t)['foot_pitch_degrees'] > foot(t+.04*c.step)['foot_pitch_degrees']


def test_invalid_or_tensile_prior_is_rejected():
    with pytest.raises(ValueError): birds_prior(-1,2,4)
    with pytest.raises(ValueError): EmpiricalSupport([1,4],.9)
