import numpy as np
import pytest
from types import SimpleNamespace

from eonwild_motion.solve.moco_path_task import path_frame, foot_task


def test_full_moco_does_not_silently_mirror_a_curved_path_task():
    from eonwild_motion.solve.moco_prototype import make_study
    with pytest.raises(ValueError,match='half-stride reflection'):
        make_study(None,None,None,{'coordination':{'path_task':{'yaw_rate_rad_s':.12}}})


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


def test_support_center_is_independent_of_split_pad_sampling():
    from eonwild_motion.solve.moco_path_task import sole_center_offset
    geom={'toe_midpoint_m':[.25,-.1,0], 'sites':[
        {'center_local_m':[-.1,0,0],'radius_m':.1},
        {'center_local_m':[.15,0,0],'radius_m':.1},
        {'center_local_m':[.4,0,0],'radius_m':.1,'distal':True}]}
    expected=sole_center_offset(geom)
    geom['sites'][1:2]=[
        {'center_local_m':[.15,0,-.2],'radius_m':.1,'stiffness_share':.5},
        {'center_local_m':[.15,0,.2],'radius_m':.1,'stiffness_share':.5}]
    np.testing.assert_allclose(sole_center_offset(geom),expected,atol=1e-12)


def test_mass_centered_sole_places_support_region_beneath_mass():
    from eonwild_motion.solve.moco_path_task import sole_center_offset
    geometry={'toe_midpoint_m':[.25,-.1,0], 'sites':[
        {'center_local_m':[-.1,-.1,0],'radius_m':.1},
        {'center_local_m':[.4,0,0],'radius_m':.1,'distal':True}]}
    task=dict(duty_factor=.62,yaw_rate_rad_s=0,half_track_hip_width_ratio=.5,
              catch_bias_m=0.,toe_out_radians=0.,toe_off_radians=.38,
              recovery_toe_radians=.45,clearance_m=.25,initial_pad_compression_m=.0045,
              support_reference='mass_centered_sole')
    problem=SimpleNamespace(policy={'path_task':task},period=2.74,speed=1.,
        admission={'points':{'leftLeg.0':[0,0,-.56],'rightLeg.0':[0,0,.56]}},
        metadata={'foot_geometry':geometry,'path_support':{'mean_com_forward_m':.05}})
    t=.31*problem.period
    mtp,rotation,digit=foot_task(problem,t,'l')
    # First site and front site have equal area. Unroll does not change the
    # planted front witness; its placement must carry the sole-center lever.
    from eonwild_motion.solve.moco_tasks import rot
    front=mtp+rotation@np.array([.25,-.1,0])+rotation@rot(digit)@np.array([.4,-.1,0])
    np.testing.assert_allclose(front[0]-sole_center_offset(geometry)[0],t+.05,atol=1e-12)


def test_support_phase_maps_stance_without_a_release_velocity_corner():
    from eonwild_motion.solve.moco_path_task import support_phase
    phase=np.linspace(0,1,1001)
    mapped=support_phase(phase,.43,.62)
    assert np.all(np.diff(mapped)>0)
    np.testing.assert_allclose(support_phase(np.array([0,.62,1]),.43,.62),[0,.43,1])
    h=1e-5
    slopes=(support_phase(np.array([.62,.62+h]),.43,.62)-support_phase(np.array([.62-h,.62]),.43,.62))/h
    np.testing.assert_allclose(slopes,[1,1],atol=1e-7)


def test_joint_spline_obeys_stops_between_nodes_with_smooth_derivatives():
    from eonwild_motion.solve.moco_joint_spline import BoundedJointSpline
    # Ordinary cubic interpolation overshoots this near-stop sequence.
    times=np.arange(6,dtype=float);q=np.array([[v,2*v] for v in [0.,.99,1.,.99,0.,.1]])
    spline=BoundedJointSpline(times,q,{0:(0.,1.)})
    grid=np.linspace(0,5,2001);x=spline(grid)
    assert np.all(x[:,0]>=0) and np.all(x[:,0]<=1)
    t=np.array([.3,1.7,3.2,4.4]);h=1e-5
    np.testing.assert_allclose(spline(t,1),(spline(t+h)-spline(t-h))/(2*h),atol=1e-6)
    np.testing.assert_allclose(spline(t,2),(spline(t+h,1)-spline(t-h,1))/(2*h),atol=1e-5)
