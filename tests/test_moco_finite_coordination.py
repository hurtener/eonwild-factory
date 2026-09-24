import numpy as np
from types import SimpleNamespace
from eonwild_motion.solve.moco_finite_coordination import FiniteBasis,shared_cf_residual,shared_effort_residual


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
