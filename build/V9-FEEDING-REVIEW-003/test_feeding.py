import json
from pathlib import Path
import numpy as np
import pytest
import feeding as F

HERE=Path(__file__).resolve().parent

def data():
    return json.loads((HERE/'profile.json').read_text()),json.loads((HERE/'receipt.json').read_text())

def test_resisted_oral_contact_closed_jaw_and_moving_body():
    p,r=data();a=p['anchor'];rows=r['samples']
    held=[x for x in rows if a['capture']<=x['time_seconds']<=a['resisted_end']]
    tip=np.asarray([x['upper_mouth'] for x in held]);hips=np.asarray([x['pelvis_world'] for x in held])
    assert np.linalg.norm(tip-tip[0],axis=1).max()<a['tolerance_m']
    assert max(x['state']['actual_jaw_degrees'] for x in held)<.01
    assert np.ptp(hips[:,1])>.03
    assert np.ptp([x['state']['yaw'] for x in held])>9

def test_retract_precedes_chewing_and_grip_stays_closed():
    p,r=data();rows=r['samples'];at=lambda t:min(rows,key=lambda x:abs(x['time_seconds']-t))
    _,rig=F.setup(p)
    assert r['gates']['minimum_lower_jaw_y_m']>=rig.ground
    delta=np.asarray(at(4.2)['upper_mouth'])-at(p['anchor']['resisted_end'])['upper_mouth']
    assert delta@rig.forward<-.08
    assert all(x['state']['actual_jaw_degrees']<.01 for x in rows if 1.94<=x['time_seconds']<=4.2)
    assert max(x['state']['actual_jaw_degrees'] for x in rows if 4.2<x['time_seconds']<5.6)>20

def test_emitted_contacts_limits_continuity_and_checkpoint():
    p,r=data();g=r['gates']
    assert F.BASE.B.sha((HERE/'feeding.glb').read_bytes())==r['candidate_sha256']
    assert F.BASE.B.sha((F.ROOT/'build/V9-FEEDING-REVIEW-002/feeding.glb').read_bytes())=='93310474d65a00d601a60c0b3f8ba9d6cb4150dae632e206f4a6188cf618d181'
    assert g['bone_attachments_unchanged'] and g['bone_scales_unchanged']
    assert g['max_foot_transform_error']<1e-5 and g['max_ankle_drift_m']<1e-5
    assert g['ground_band_skin_max_drift_m']<.005
    assert g['max_joint_rate_degrees_per_second']<220
    assert g['maximum_cervical_adjacent_pitch_degrees']<10
    assert g['minimum_cervical_pitch_degrees']>=-1
    _,rig=F.setup(p)
    glb=F.BASE.B.Glb.from_bytes((HERE/'feeding.glb').read_bytes())
    tracks,times=F.BASE.B._clip_state(glb,r['clip'])
    oral=[]
    for i,time in enumerate(times):
        if p['anchor']['capture']<=time<=p['anchor']['resisted_end']:
            pose=map(np.asarray,F.BASE.B._pose(glb,tracks,i))
            oral.append(rig.centroid(rig.world(*pose),'upper'))
    assert np.linalg.norm(np.asarray(oral)-oral[0],axis=1).max()<p['anchor']['tolerance_m']

def test_c1_anchor_handoff_and_duration_parameter():
    p,_=data();q=json.loads(json.dumps(p));q['duration_seconds']=9
    assert F.signal(2.8,p)==pytest.approx(F.signal(4.2,q))
    a=p['anchor'];h=1e-5
    for t in a['enter'],a['capture'],a['resisted_end'],a['release']:
        left=(F.anchor_gain(t,a)-F.anchor_gain(t-h,a))/h
        right=(F.anchor_gain(t+h,a)-F.anchor_gain(t,a))/h
        assert abs(left-right)<1e-5
    source,rig=F.setup(p)
    head=rig.roles['head'][0]
    poses=[F.pose(rig,source,p,t) for t in (2.4,3.02)]
    origins=[rig.world(*x[:3])[head,:3,3] for x in poses]
    assert np.linalg.norm(origins[1]-origins[0])>.01

def test_yield_pose_space_handoff_matches_joint_velocity():
    p,_=data();source,rig=F.setup(p);h=.001
    for t in (p['anchor']['resisted_end'],p['anchor']['release']):
        rotations=[F.pose(rig,source,p,at)[1] for at in (t-h,t,t+h)]
        left=(rotations[1]-rotations[0])/h
        right=(rotations[2]-rotations[1])/h
        # Quaternion-component velocity estimate, radians/s; finite-difference
        # truncation at the handoff is allowed, a visible velocity pop is not.
        assert np.max(np.linalg.norm(left-right,axis=1))*2<.08

def test_unreachable_oral_target_rejects_instead_of_attachment_edits():
    p,_=data();source,rig=F.setup(p)
    t,r,s,state,_=F.FREE_POSE(rig,source,p,2.05)
    target=rig.centroid(rig.world(t,r,s),'upper')+np.array([0.,10.,0.])
    with pytest.raises(ValueError,match='unreachable bounded oral anchor'):
        F.solve_oral_anchor(rig,t,r,s,target,p,state)
