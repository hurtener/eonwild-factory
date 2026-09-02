import json
from pathlib import Path
import numpy as np
import pytest
import feeding as F

HERE=Path(__file__).resolve().parent


def test_reopened_candidate_gates():
    receipt=json.loads((HERE/'receipt.json').read_text())
    assert F.B.sha((HERE/'feeding.glb').read_bytes())==receipt['candidate_sha256']
    g=receipt['gates']
    assert g['bone_attachments_unchanged'] and g['bone_scales_unchanged']
    assert g['max_foot_transform_error']<1e-5
    assert g['max_ankle_drift_m']<1e-5
    assert g['ground_band_skin_max_drift_m']<.005
    assert g['maximum_cervical_adjacent_pitch_degrees']<=10
    assert g['minimum_cervical_pitch_degrees']>=-1
    assert g['max_joint_rate_degrees_per_second']<220


def test_proximal_twist_and_bend_plane_continuity():
    p=json.loads((HERE/'profile.json').read_text())
    source,rig=F.setup(p)
    glb=F.B.Glb.from_bytes((HERE/'feeding.glb').read_bytes())
    tracks,times=F.B._clip_state(glb,F.CLIP)
    nodes=sum(rig.legs.values(),[])
    rotations=np.asarray([F.B._pose(glb,tracks,i)[1] for i in range(len(times))])[:,nodes]
    dots=np.clip(np.abs(np.sum(rotations[1:]*rotations[:-1],axis=2)),0.,1.)
    rates=np.degrees(2*np.arccos(dots))/np.diff(times)[:,None]
    assert rates.max()<80
    samples=json.loads((HERE/'receipt.json').read_text())['samples']
    for side in rig.legs:
        normals=np.asarray([row['support'][side]['bend_normal'] for row in samples])
        steps=np.degrees(np.arccos(np.clip(np.sum(normals[1:]*normals[:-1],axis=1),-1,1)))
        assert steps.max()<.1


def test_planted_body_moves_and_hips_rise_while_head_descends():
    rows=json.loads((HERE/'receipt.json').read_text())['samples']
    def at(t):return min(rows,key=lambda r:abs(r['time_seconds']-t))
    a,b=at(1.95),at(2.48)
    assert b['pelvis_world'][1]>a['pelvis_world'][1]+.04
    assert b['upper_mouth'][1]<a['upper_mouth'][1]
    profile=json.loads((HERE/'profile.json').read_text())
    _,rig=F.setup(profile)
    displacement=np.asarray(b['upper_mouth'])-a['upper_mouth']
    assert displacement@rig.forward>.025, 'first pull must move head forward/down, not retract'
    hold=[r for r in rows if 1.95<=r['time_seconds']<=4.2]
    assert np.ptp([r['pelvis_world'][1] for r in hold])>.04
    assert np.ptp([r['upper_mouth'][2] for r in hold])>.07
    assert np.ptp([r['state']['actual_jaw_degrees'] for r in hold])>8


def test_timing_scale_and_semantic_parameters():
    p=json.loads((HERE/'profile.json').read_text())
    q=json.loads(json.dumps(p));q['duration_seconds']=9.
    for t in np.linspace(0,6,31):
        assert F.signal(t,p)==pytest.approx(F.signal(t*1.5,q))
    assert 'Tarbosaurus' not in (HERE/'feeding.py').read_text()
    assert F.signal(2.48,p)['drop']<F.signal(1.95,p)['drop']


def test_support_rejects_unreachable_without_attachment_edits():
    p=json.loads((HERE/'profile.json').read_text())
    source,rig=F.setup(p)
    t,r,s=rig.pose(0);neutral=rig.world(t,r,s)
    t[rig.roles['pelvis'][0]][1]+=10.
    with pytest.raises(ValueError,match='unreachable planted'):
        F.support(rig,t,r,s,neutral,'left',p['support_limits'])


def test_continuity_at_all_phase_boundaries():
    p=json.loads((HERE/'profile.json').read_text())
    for row in p['keyframes'][1:-1]:
        t=row[0];left=F.signal(t-1e-6,p);right=F.signal(t+1e-6,p)
        assert max(abs(left[k]-right[k]) for k in left)<1e-8


def test_renamed_scaled_rig_same_proximal_solution(tmp_path):
    p=json.loads((HERE/'profile.json').read_text())
    source,rig=F.setup(p)
    expected=F.pose(rig,source,p,2.48)
    d,bi=F.B.S.parse_glb((F.ROOT/source['source']['path']).read_bytes())
    rename={n['name']:f'Joint_{i}' for i,n in enumerate(d['nodes']) if 'name' in n}
    for node in d['nodes']:
        if 'name' in node:node['name']=rename[node['name']]
    for node in d['scenes'][d.get('scene',0)]['nodes']:
        d['nodes'][node]['scale']=[2.,2.,2.]
    raw=F.B.S.encode_glb(d,bi);path=tmp_path/'scaled.glb';path.write_bytes(raw)
    p['source']={**source['source'],'path':str(path),'sha256':F.B.sha(raw)}
    def rewrite(v):
        if isinstance(v,str):return rename.get(v,v)
        if isinstance(v,list):return [rewrite(x) for x in v]
        if isinstance(v,dict):return {k:rewrite(x) for k,x in v.items()}
        return v
    for key in ('semantic_rig','semantic_binding'):
        path=tmp_path/(key+'.json')
        path.write_text(json.dumps(rewrite(json.loads((F.ROOT/source[key]['path']).read_text()))))
        p[key]={'path':str(path),'sha256':F.B.sha(path.read_bytes())}
    p['body_metrics']={**source['body_metrics']}
    for key in ('body_height_m','body_length_m','body_width_m'):p['body_metrics'][key]*=2
    scaled,srig=F.setup(p)
    actual=F.pose(srig,scaled,p,2.48)
    ew=rig.world(*expected[:3]);aw=srig.world(*actual[:3])
    assert np.allclose(aw[:,:3,3],ew[:,:3,3]*2,atol=2e-6)
