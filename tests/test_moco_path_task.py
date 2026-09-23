import numpy as np
from types import SimpleNamespace

from eonwild_motion.solve.moco_path_task import path_frame, foot_task


def test_curved_stride_composes_without_moving_the_path_center():
    speed, rate, period = 1., .12, 2.74
    start, rotation = path_frame(period, speed, rate)
    for time in np.linspace(0, period, 11):
        p, r = path_frame(time, speed, rate)
        actual, actual_r = path_frame(time+period, speed, rate)
        np.testing.assert_allclose(start+rotation@p, actual, atol=1e-12)
        np.testing.assert_allclose(rotation@r, actual_r, atol=1e-12)
        h=1e-5
        velocity=(path_frame(time+h,speed,rate)[0]-path_frame(time-h,speed,rate)[0])/(2*h)
        np.testing.assert_allclose(np.linalg.norm(velocity),speed,atol=1e-9)


def test_turning_support_pad_stays_planted_while_root_turns():
    geometry={'toe_midpoint_m':[.25,-.10,0],
              'sites':[{'center_local_m':[.39,.01,0],'radius_m':.10}]}
    task=dict(duty_factor=.62,yaw_rate_rad_s=.12,half_track_hip_width_ratio=.5,
              catch_bias_m=.1,toe_out_radians=.06,toe_off_radians=.38,
              recovery_toe_radians=.45,clearance_m=.25,initial_pad_compression_m=.0045)
    problem=SimpleNamespace(policy={'path_task':task},period=2.74,speed=1.,
        admission={'points':{'leftLeg.0':[0,0,-.56],'rightLeg.0':[0,0,.56]}},
        metadata={'foot_geometry':geometry})
    from eonwild_motion.solve.moco_tasks import rot
    for side in ['l','r']:
        offset=0 if side=='l' else .5
        points=[]
        for phase in [.20,.30,.45,.60]:
            mtp,R,digit=foot_task(problem,(phase-offset)*problem.period,side)
            toe=mtp+R@np.array(geometry['toe_midpoint_m'])
            # Digit rotation is relative to toe; this is its front sole witness.
            points.append(toe+R@rot(digit)@np.array([.39,-.09,0]))
        np.testing.assert_allclose(np.array(points),np.tile(points[0],(4,1)),atol=1e-12)
