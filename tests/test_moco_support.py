"""Focused support-task tests: load gating, units, symmetry and no hip dragging."""
import unittest
import numpy as np
from eonwild_motion.solve.moco_support import recovery_residual,lane_residual,ankle_support_residual

class SupportTasks(unittest.TestCase):
    def test_shared_support_retains_loaded_and_recovery_acceleration_at_each_sample(self):
        policy=dict(ankle_recovery=dict(unloaded_load_BW=.08,comfortable_max_angle_rad=1.8,
            comfortable_max_rate_rad_s=7.5,angle_weight=18,rate_weight=8,acceleration_weight=1),
            ankle_loaded=dict(rate_weight=.5,acceleration_weight=.25))
        angle=np.array([1.5,2.1,1.7]);speed=np.array([4.,10.5,-3.])
        acceleration=np.array([30.,-20.,15.]);load=np.array([0.,.08,1.])
        result=ankle_support_residual(angle,speed,acceleration,load,1.2,2.4,policy)
        self.assertEqual(result.shape,(3,5))
        old_recovery=recovery_residual(angle,speed,acceleration,load,1.2,policy['ankle_recovery'])
        np.testing.assert_allclose(result[:,:3].T.ravel(),old_recovery)
        self.assertGreater(abs(result[0,2]),0)  # recovery acceleration was omitted in finite motion
        np.testing.assert_array_equal(result[0,3:],0)
        self.assertGreater(abs(result[-1,3]),0)  # loaded speed remains controlled
        self.assertGreater(abs(result[-1,4]),0)  # loaded acceleration remains controlled
        for j in range(3):
            one=ankle_support_residual(angle[j:j+1],speed[j:j+1],acceleration[j:j+1],
                load[j:j+1],1.2,2.4,policy)
            np.testing.assert_allclose(result[j:j+1],one)
        # Existing running cost is unchanged by extraction (only row ordering).
        gate=np.sqrt(load/(load+.08));omega=np.sqrt(9.80665/2.4)
        np.testing.assert_allclose(result[:,3],.5*gate*speed/omega)
        np.testing.assert_allclose(result[:,4],.25*gate*acceleration/omega**2)

    def test_loaded_ankle_is_not_forced_into_swing_comfort_pose(self):
        policy=dict(unloaded_load_BW=.08,comfortable_max_angle_rad=1.8,comfortable_max_rate_rad_s=7.5,angle_weight=18,rate_weight=8,acceleration_weight=1)
        args=[np.array([2.1]),np.array([10.5]),np.array([30.])]
        unloaded=recovery_residual(*args,np.array([0.]),1.2,policy)
        loaded=recovery_residual(*args,np.array([1.]),1.2,policy)
        self.assertGreater(np.linalg.norm(unloaded),20)
        self.assertLess(np.linalg.norm(loaded),.002)
        # The gate changes continuously as weight leaves the foot.
        around=[recovery_residual(*args,np.array([load]),1.2,policy) for load in [.08-1e-7,.08+1e-7]]
        self.assertLess(np.max(abs(around[0]-around[1])),.001)

    def test_no_penalty_within_comfort_or_world_support_lane(self):
        policy=dict(unloaded_load_BW=.08,comfortable_max_angle_rad=1.8,comfortable_max_rate_rad_s=7.5,angle_weight=18,rate_weight=8,acceleration_weight=1)
        np.testing.assert_array_equal(recovery_residual(np.array([1.5]),np.array([4.]),np.array([0.]),np.array([0.]),1.2,policy),0)
        # A moving pelvis is deliberately absent: world-planted feet remain
        # within their track as the body transfers to the next support.
        feet=np.array([[-.66,.66],[-.66,.66]])
        np.testing.assert_array_equal(lane_residual(feet,np.ones((2,2)),.66,.08,2.4,20),0)
        outward=np.array([[-.9,.9]])
        r=lane_residual(outward,np.ones((1,2)),.66,.08,2.4,20)
        self.assertGreater(r[0],0);self.assertEqual(r[0],r[1])
        np.testing.assert_array_equal(lane_residual(outward,np.zeros((1,2)),.66,.08,2.4,20),0)

if __name__=='__main__':unittest.main()
