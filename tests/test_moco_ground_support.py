import numpy as np
from eonwild_motion.solve.moco_ground_support import recovery_reference


def test_roll_and_fold_precede_rise_without_widening_joint_limits():
    names=['pitch','yaw','roll','height','hip_l','knee_l','ankle_l']
    ix={n:i for i,n in enumerate(names)}
    rest=np.array([0.,0.,1.4,.55,.1,-1.2,.5])
    standing=np.array([0.,0.,0.,2.,.3,-.6,.8])
    bounds={'hip_l':(-.8,1.45),'knee_l':(-2.,-.16),'ankle_l':(.15,2.25)}
    policy=dict(fold_keys=[[0,0],[1,1],[6,1]],roll_keys=[[0,0],[1,0],[3,1],[6,1]],
                rise_keys=[[0,0],[3,0],[6,1]],crouch_radians={'hip_l':.65,'knee_l':-1.9,'ankle_l':1.0})
    np.testing.assert_allclose(recovery_reference(rest,standing,0,policy,ix,bounds),rest)
    crouch=recovery_reference(rest,standing,3,policy,ix,bounds)
    assert crouch[ix['height']]==rest[ix['height']]
    assert crouch[ix['roll']]==0
    assert crouch[ix['knee_l']] < rest[ix['knee_l']]
    np.testing.assert_allclose(recovery_reference(rest,standing,6,policy,ix,bounds),standing)
    for t in np.linspace(0,6,121):
        q=recovery_reference(rest,standing,t,policy,ix,bounds)
        for n,(lo,hi) in bounds.items():
            assert lo <= q[ix[n]] <= hi
