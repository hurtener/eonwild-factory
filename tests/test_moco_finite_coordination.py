import numpy as np
from types import SimpleNamespace
from eonwild_motion.solve.moco_finite_coordination import FiniteBasis
from eonwild_motion.solve.moco_coordination_costs import shared_cf_residual,shared_effort_residual,shared_tail_carriage_residual


def test_finite_correction_preserves_state_speed_and_acceleration_at_boundaries():
    b=FiniteBasis(2.,9.,12)
    for a in b.arrays([0.,2.,9.,16.]):np.testing.assert_allclose(a,0,atol=1e-12)
    assert np.max(abs(b.arrays(np.linspace(2,9,81))[0]))>0
    t=np.array([3.12,4.63,6.89]);h=1e-5
    for d in [0,1]:
        numeric=(b.arrays(t+h)[d]-b.arrays(t-h)[d])/(2*h)
        np.testing.assert_allclose(numeric,b.arrays(t)[d+1],atol=1e-7)


def test_shared_cf_cost_uses_actuator_order_and_capacity():
    p=SimpleNamespace(policy={'cf_coupling_weight':40,'cf_moment_arm_ratio':.6},
        motors=['motor_hip_r','motor_tail_0_yaw','motor_hip_l'],capacities=np.array([10,20,30]),bw=100,L=2)
    effort=np.array([[.8,.09,.1]]) # tail 1.8 vs .6*(8-3) = 3
    np.testing.assert_allclose(shared_cf_residual(p,effort),[[-.24]])
    costs=shared_effort_residual(np.array([[1.2]]),np.array([[1.3]]),{'effort_weight':.03,'capacity_weight':50})
    np.testing.assert_allclose([v.item() for v in costs],[.036,12.5,8.])



def test_shared_carriage_cost_retains_existing_loaded_envelope_and_ignores_non_tail_frames():
    p=SimpleNamespace(policy={'tail_carriage_weight':30.,'tail_carriage_half_range_leg_lengths':.075},
        L=2.,index={'height':0},metadata={'clearance_frames':[
            {'path':'/tip_tail_0','minimum_height_m':.1}, {'path':'/material_l_0','minimum_height_m':0.}],
            'bracing':{'loaded_tail_end_heights_relative_root_m':{'tail_0':-.5}}})
    m={'q':np.array([[2.],[2.]]),'clearance':np.array([[1.4,0.],[2.4,0.]])}
    np.testing.assert_allclose(shared_tail_carriage_residual(p,m),[[0.],[12.75]])


def test_coordinate_search_radius_tightens_only_matching_coordinates():
    import pytest
    from eonwild_motion.solve.moco_finite_coordination import coefficient_limits
    names=['hip_l','tail_0_pitch','tail_1_yaw']
    np.testing.assert_allclose(coefficient_limits(names,2.,{'tail_':.05}),[2.,.05,.05])
    for overrides in ({'tail_':3.},{'tail_':0.},{'missing_':.05},{'tail_':float('nan')}):
        with pytest.raises(ValueError):coefficient_limits(names,2.,overrides)
