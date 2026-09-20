"""Analytical witnesses for the reduced dynamics, independent of gait curves."""
import numpy as np
import pytest
from eonwild_motion.solve.running_stride_fit import periodic_derivatives, inverse_dynamics


def test_periodic_derivatives_include_loop_neighbors():
    t=np.arange(256)/256;d1,d2=periodic_derivatives(t,1.)
    x=np.sin(2*np.pi*t)
    np.testing.assert_allclose(d1@x,2*np.pi*np.cos(2*np.pi*t),atol=.0007)
    np.testing.assert_allclose(d2@x,-(2*np.pi)**2*x,atol=.0021)
    np.testing.assert_allclose(d2@np.ones(len(t)),0,atol=1e-9)


def test_static_three_rod_moments_and_external_force_sign():
    t=np.arange(32)/32;_,d2=periodic_derivatives(t,1.)
    p=np.tile([[0.,0.],[1.,0.],[2.,0.],[3.,0.]],(32,1,1))
    force=np.tile([0.,20.],(32,1));g=9.81
    expected=np.tile([7*g-60,2.5*g-40,.5*g-20],(32,1))
    np.testing.assert_allclose(inverse_dynamics(p,force,[3,2,1],g,d2),expected,atol=1e-10)


def test_uniform_free_fall_has_no_required_joint_moment():
    # Exact quadratic acceleration, evaluated away from the artificial seam.
    t=np.arange(64)/64;_,d2=periodic_derivatives(t,1.)
    p=np.tile([[0.,0.],[1.,0.],[2.,0.],[3.,0.]],(64,1,1))
    p[:,:,1] = (-.5*9.81*t*t)[:,None]
    tau=inverse_dynamics(p,np.zeros((64,2)),[3,2,1],9.81,d2)
    np.testing.assert_allclose(tau[2:-2],0,atol=1e-9)
