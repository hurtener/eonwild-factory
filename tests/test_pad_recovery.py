from copy import deepcopy
import math
import numpy as np
import pytest
from eonwild_motion.errors import ContractError
from eonwild_motion.planning.foot_articulation import recovery_pitch,signed_recovery_pitch,declare_pad_recovery
from eonwild_motion.planning.airborne_gait import AirborneGait,build_airborne_plan
from eonwild_motion.planning.grounded_gait import GroundedGait,build_grounded_plan
from eonwild_motion.solve.performance import decorate_plan,Performance


def test_pad_has_zero_pitch_at_lift_and_land_even_with_large_metatarsal_push():
    assert recovery_pitch(0,28)==0
    assert recovery_pitch(1,28)==0
    assert recovery_pitch(.42,28)==-28
    for phase in np.linspace(0,1,81):assert -28<=recovery_pitch(float(phase),28)<=0


def test_pitch_is_c2_at_support_and_recovery_joins():
    # A one-sided finite difference is O(h), not an exact second derivative.
    # Use a small enough h to distinguish a true endpoint kink from truncation.
    h=1e-6
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


def test_existing_zero_recovery_crown_sentinel_means_mid_swing():
    plan={'parameters':{'foot_recovery_pitch_degrees':28,'swing_recovery_peak_fraction':0},
          'samples':[{'feet':{'left':{'contact':False,'swing_phase':.5}}}]}
    declare_pad_recovery(plan)
    assert plan['samples'][0]['feet']['left']['pad_pitch_degrees']==-28


def test_grounded_profile_can_author_a_hanging_pad_without_reversing_metatarsal_recovery():
    plan={'parameters':{'foot_recovery_pitch_degrees':36,'pad_recovery_pitch_degrees':36,
                       'swing_recovery_peak_fraction':.42},
          'samples':[{'feet':{'left':{'contact':False,'swing_phase':.42,
                                     'foot_pitch_degrees':-36}}}]}
    declare_pad_recovery(plan)
    foot=plan['samples'][0]['feet']['left']
    assert foot['foot_pitch_degrees']==-36
    assert foot['pad_pitch_degrees']==36
    assert signed_recovery_pitch(.42,-36,.42)==-36


def test_unset_grounded_recovery_controls_do_not_change_legacy_plan_parameters():
    plan=build_grounded_plan(GroundedGait(),2.)
    assert 'pad_recovery_pitch_degrees' not in plan['parameters']
    assert 'toe_recovery_peak_fraction' not in plan['parameters']


@pytest.mark.parametrize('phase,amp,peak',[(math.nan,20,.42),(.2,math.inf,.42),(-.1,20,.42),(.2,61,.42),(.2,20,0),(.2,True,.42)])
def test_untrusted_pad_controls_fail_closed(phase,amp,peak):
    with pytest.raises(ContractError):recovery_pitch(phase,amp,peak)


@pytest.mark.parametrize('pitch',[math.nan,math.inf,-61,61,True,'20'])
def test_untrusted_signed_pad_controls_fail_closed(pitch):
    with pytest.raises(ContractError):
        signed_recovery_pitch(.42,pitch,.42)
