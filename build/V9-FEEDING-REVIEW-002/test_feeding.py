import json
from pathlib import Path
import numpy as np
import pytest
import feeding as F

HERE=Path(__file__).resolve().parent


def profile():return json.loads((HERE/'profile.json').read_text())


def test_shape_preserving_continuous_channel_waypoints():
    p=profile()
    for name,keys in p['channels'].items():
        for left,right in zip(keys,keys[1:]):
            values=[F.curve(t,keys) for t in np.linspace(left[0],right[0],25)]
            assert min(values)>=min(left[1],right[1])-1e-10
            assert max(values)<=max(left[1],right[1])+1e-10
        for i in range(1,len(keys)-1):
            t,v=keys[i];eps=1e-5
            l=(F.curve(t,keys)-F.curve(t-eps,keys))/eps
            r=(F.curve(t+eps,keys)-F.curve(t,keys))/eps
            assert abs(l-r)<.015
            if (v-keys[i-1][1])*(keys[i+1][1]-v)>0:
                assert abs((l+r)/2)>1e-7, name


def test_motion_overlaps_at_each_body_waypoint():
    p=profile()
    for t,_ in p['channels']['body'][1:-1]:
        before=F.signal(t-.001,p);after=F.signal(t+.001,p)
        assert any(abs(after[k]-before[k])>.00001 for k in before),t


def test_timing_parameter_and_new_profile_yaw_extent():
    p=profile();q=json.loads(json.dumps(p));q['duration_seconds']=9.
    assert F.signal(2.4,p)==pytest.approx(F.signal(3.6,q))
    assert np.ptp([F.signal(t,p)['yaw'] for t in np.linspace(1.95,3.25,100)])>12


def test_exact_candidate_and_unchanged_checkpoint():
    r=json.loads((HERE/'receipt.json').read_text());g=r['gates']
    assert F.BASE.B.sha((HERE/'feeding.glb').read_bytes())==r['candidate_sha256']
    assert F.BASE.B.sha((F.ROOT/'build/V9-FEEDING-REVIEW-001/feeding.glb').read_bytes())==r['preserved_checkpoint_sha256']
    assert g['bone_attachments_unchanged'] and g['bone_scales_unchanged']
    assert g['max_foot_transform_error']<1e-5
    assert g['max_ankle_drift_m']<1e-5
    assert g['ground_band_skin_max_drift_m']<.005
    assert g['maximum_cervical_adjacent_pitch_degrees']<10
    assert g['max_joint_rate_degrees_per_second']<220


def test_preserved_first_pull_direction_and_stronger_compensation():
    rows=json.loads((HERE/'receipt.json').read_text())['samples']
    at=lambda t:min(rows,key=lambda row:abs(row['time_seconds']-t))
    a,b=at(1.95),at(2.60)
    _,rig=F.setup(profile())
    assert b['pelvis_world'][1]-a['pelvis_world'][1]>.06
    delta=np.asarray(b['upper_mouth'])-a['upper_mouth']
    assert delta[1]<0 and delta@rig.forward>0
    assert np.ptp([row['upper_mouth'][0] for row in rows if 1.95<row['time_seconds']<3.25])>.20


def test_unreachable_support_still_rejects():
    p=profile();_,rig=F.setup(p)
    t,r,s=rig.pose(0);w=rig.world(t,r,s)
    t[rig.roles['pelvis'][0]][1]+=10
    with pytest.raises(ValueError,match='unreachable planted'):
        F.BASE.support(rig,t,r,s,w,'left',p['support_limits'])
