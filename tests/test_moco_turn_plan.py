import numpy as np
from eonwild_motion.solve.moco_turn_plan import TurnPlan
from eonwild_motion.solve.moco_path_task import foot_task
from scipy.spatial.transform import Rotation
from types import SimpleNamespace


def plan():
    return TurnPlan(dict(yaw_rate_keys=[[0,0],[2,0],[4,.2],[8,.2],[10,0],[16,0]],
        attention_lookahead_s=3.,attention_shares={'neck_yaw':.4,'head_yaw':.6},
        tail_follow_delay_s=1.5),16.,lambda t:np.zeros_like(t)+1.6)


def test_head_leads_heading_and_path_speed_is_preserved():
    p=plan()
    assert p.heading(1.)==0 and p.attention(1.)>0
    for t in [1.,3.,5.,9.,11.]:
        velocity=p.position(t,1)
        np.testing.assert_allclose(np.linalg.norm(velocity),1.6,atol=1e-7)
        np.testing.assert_allclose(velocity[2]/velocity[0],-np.tan(p.heading(t)),atol=1e-7)
    assert p.attention(12.)==0
    assert p.body_offsets(5.,12)['roll']<0


def test_finite_turn_keeps_loaded_toe_witness_and_heading_fixed():
    p=plan()
    geo={'toe_midpoint_m':[.25,-.10,0], 'sites':[{'center_local_m':[.39,.01,0],'radius_m':.10}]}
    task=dict(duty_factor=.62,yaw_rate_rad_s=0.,half_track_hip_width_ratio=.5,
        catch_bias_m=.1,toe_out_radians=.06,toe_off_radians=.28,
        recovery_toe_radians=.45,clearance_m=.25,initial_pad_compression_m=.0045)
    obj=SimpleNamespace(policy={'path_task':task},period=1.7,speed=1.6,
        admission={'points':{'leftLeg.0':[0,2,-.4],'rightLeg.0':[0,2,.4]}},
        metadata={'foot_geometry':geo},anchor_frame=lambda start,mid,side:p.frame(mid))
    tips=[];headings=[]
    # Late stance: distal toe stays down while the rear foot peels upward.
    for t in np.linspace(3.4+.62*1.7*.90,3.4+.62*1.7*.99,15):
        pos,rot,digit=foot_task(obj,t,'l')
        distal=rot@Rotation.from_rotvec([0,0,digit]).as_matrix()
        tips.append(pos+rot@geo['toe_midpoint_m']+distal@np.array([.39,-.09,0]))
        headings.append(np.arctan2(rot[0,2],rot[2,2]))
    np.testing.assert_allclose(tips,np.tile(tips[0],(len(tips),1)),atol=1e-9)
    np.testing.assert_allclose(headings,headings[0],atol=1e-10)
