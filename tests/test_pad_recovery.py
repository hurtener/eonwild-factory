from copy import deepcopy
import math
import numpy as np
import pytest
from eonwild_motion.errors import ContractError
from eonwild_motion.planning.foot_articulation import recovery_pitch,declare_pad_recovery
from eonwild_motion.planning.airborne_gait import AirborneGait,build_airborne_plan
from eonwild_motion.solve.performance import decorate_plan,Performance


def test_pad_has_zero_pitch_at_lift_and_land_even_with_large_metatarsal_push():
    assert recovery_pitch(0,28)==0
    assert recovery_pitch(1,28)==0
    assert recovery_pitch(.42,28)==-28
    for phase in np.linspace(0,1,81):assert -28<=recovery_pitch(float(phase),28)<=0


def test_pitch_is_c2_at_support_and_recovery_joins():
    h=1e-5
    for at in (0.,.42,1.):
        for direction in (-1,1):
            if not 0<=at+direction*2*h<=1:continue
            f0=recovery_pitch(at,28)
            f1=recovery_pitch(at+direction*h,28)
            f2=recovery_pitch(at+direction*2*h,28)
            assert abs((f1-f0)/h)<1e-5
            assert abs((f2-2*f1+f0)/h**2)<.2


def test_decorated_plan_declares_pad_not_metatarsal_push_angle():
    plan=build_airborne_plan(AirborneGait(push_off_pitch_degrees=55,foot_recovery_pitch_degrees=28),2.64)
    before=deepcopy(plan)
    result=decorate_plan(plan,Performance())
    assert plan==before
    for row in result['samples']:
        for foot in row['feet'].values():
            assert foot['pad_pitch_degrees']<=0
            if foot['contact']:assert foot['pad_pitch_degrees']==0
    assert any(f['foot_pitch_degrees']>40 and f['pad_pitch_degrees']==0 for r in result['samples'] for f in r['feet'].values())


@pytest.mark.parametrize('phase,amp,peak',[(math.nan,20,.42),(.2,math.inf,.42),(-.1,20,.42),(.2,61,.42),(.2,20,0),(.2,True,.42)])
def test_untrusted_pad_controls_fail_closed(phase,amp,peak):
    with pytest.raises(ContractError):recovery_pitch(phase,amp,peak)
