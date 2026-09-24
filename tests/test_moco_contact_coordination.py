import numpy as np
from eonwild_motion.solve.moco_contact_coordination import acceleration_rows


def test_acceleration_cost_respects_sample_rate_and_geometric_similarity():
    for length in [1.,3.]:
        for dt in [1/24,1/48,1/96]:
            t=np.arange(8)*dt
            q=np.c_[.5*9.80665*t*t,.5*9.80665/length*t*t]
            np.testing.assert_allclose(acceleration_rows(q,dt,length,np.array([1/length,1.])),1.,atol=1e-12)


def test_constant_velocity_has_no_artificial_acceleration_penalty():
    t=np.arange(16)/48
    np.testing.assert_allclose(acceleration_rows(np.c_[3*t+1,-2*t],1/48,2.,np.array([.5,1.])),0.,atol=1e-11)
