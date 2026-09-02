"""Bounded feeding composition: persistent contacts, not a gait schedule.

This review-only compiler reuses skin/GLB helpers and limb geometry, never the
airborne planner. Fixed ankle transforms are a conservative prototype choice.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "build/V9-GROUNDED-COMMITTED-BITE-001"))
sys.path.insert(0, str(ROOT))
import attack_solver as A
import grounded_committed_bite as B
from src.eonwild_motion.solve.airborne_gait import (
    stable_knee_geometry, _orientation_from_bend, _between, _world_rotation, _interior,
)
from src.eonwild_motion.layers.leg_contact_resolve_v3 import _rotation_from_matrix, _qmul

CLIP = "feeding_planted_wholebody_review"


def signal(time, profile):
    """Physical time is normalized to authored phase time; no periodic wag."""
    keys = profile["keyframes"]
    time = float(time) * 6.0 / profile["duration_seconds"]
    columns = profile["keyframe_columns"]
    for left, right in zip(keys, keys[1:]):
        if time <= right[0]:
            u = B.smooth((time - left[0]) / (right[0] - left[0]))
            return dict(zip(columns, (1-u)*np.asarray(left[1:]) + u*np.asarray(right[1:])))
    return dict(zip(columns, keys[-1][1:]))


def unit(value):
    value = np.asarray(value, dtype=float)
    norm = np.linalg.norm(value)
    if norm < 1e-10:
        raise ValueError("degenerate limb basis")
    return value / norm


def support(rig, t, r, s, neutral, side, limits):
    """Two-link proximal solve, anchored ankle and full distal foot transform.

    No distal search, bone offset edits, source-idle foot trajectories, or target
    projection. Reject unreachable poses before serialization.
    """
    hip, knee, ankle, foot = rig.legs[side]
    w = rig.world(t, r, s)
    hp, kp, ap = [w[n, :3, 3] for n in (hip, knee, ankle)]
    upper, lower = np.linalg.norm(kp-hp), np.linalg.norm(ap-kp)
    old_normal = unit(np.cross(kp-hp, ap-kp))
    desired_normal = unit(np.cross(neutral[knee,:3,3]-neutral[hip,:3,3], neutral[ankle,:3,3]-neutral[knee,:3,3]))
    target = neutral[ankle,:3,3]
    knee_target, ankle_target, error = stable_knee_geometry(hp, target, upper, lower, desired_normal)
    if error > 1e-6*(upper+lower):
        raise ValueError(f"unreachable planted {side} ankle: {error}")
    normal = unit(np.cross(knee_target-hp, ankle_target-knee_target))
    delta = _orientation_from_bend(kp-hp, old_normal, knee_target-hp, normal)
    r[hip] = _world_rotation(rig.glb, w, hip, _qmul(delta, _rotation_from_matrix(w[hip])))
    w = rig.world(t, r, s)
    kp, ap = [w[n,:3,3] for n in (knee, ankle)]
    r[knee] = _world_rotation(rig.glb, w, knee, _qmul(_between(ap-kp, ankle_target-kp), _rotation_from_matrix(w[knee])))
    for node in (ankle, foot):
        w = rig.world(t, r, s)
        r[node] = _world_rotation(rig.glb, w, node, _rotation_from_matrix(neutral[node]))
    w = rig.world(t, r, s)
    h,k,a,f = [w[n,:3,3] for n in (hip,knee,ankle,foot)]
    values = {
        "knee_interior_degrees": _interior(h-k,a-k),
        "ankle_interior_degrees": _interior(k-a,f-a),
        "hip_sagittal_degrees": float(np.degrees(np.arctan2((k-h)@rig.forward,-(k-h)[1]))),
    }
    for key,value in values.items():
        lo,hi = limits[key]
        if not lo-1e-4 <= value <= hi+1e-4:
            raise ValueError(f"{side} {key} {value} outside unchanged limits {lo,hi}")
    return {**values, "foot_transform_error": float(np.abs(w[foot]-neutral[foot]).max()),
            "ankle_drift_m": float(np.linalg.norm(a-neutral[ankle,:3,3])),
            "bend_normal": normal.tolist()}


def setup(profile):
    source = json.loads((ROOT / profile["foundation_profile"]).read_text())
    # Only immutable source/mapping coordinates are inherited, never R6 motion.
    for key in ("source", "semantic_rig", "semantic_binding", "body_metrics"):
        if key in profile:
            source[key] = profile[key]
    for key in ("source", "semantic_rig", "semantic_binding"):
        raw = (ROOT/source[key]["path"]).read_bytes()
        if B.sha(raw) != source[key]["sha256"]:
            raise ValueError(f"{key} hash mismatch")
    rig = A.Rig((ROOT/source["source"]["path"]).read_bytes(),source)
    return source,rig


def pose(rig, source, profile, time):
    t,r,s = rig.pose(0)
    neutral = rig.world(t,r,s)
    state = signal(time,profile)
    metrics = source["body_metrics"]
    pelvis = rig.roles["pelvis"][0]
    lateral = np.cross([0.,1.,0.],rig.forward)
    shift = (rig.forward * state["forward"] * metrics["body_length_m"]
             + lateral * state["lateral"] * metrics["body_width_m"]
             + np.array([0.,-state["drop"]*metrics["body_height_m"],0.]))
    t[pelvis] += np.linalg.solve(neutral[rig.parents[pelvis],:3,:3],shift)
    for role, angles in profile["base_pitch_degrees"].items():
        if len(angles) != len(rig.roles[role]):
            raise ValueError(f"semantic chain size mismatch: {role}")
        for i,(node,angle) in enumerate(zip(rig.roles[role],angles)):
            pitch_axis = unit(np.linalg.solve(neutral[node,:3,:3],lateral))
            yaw_axis = unit(np.linalg.solve(neutral[node,:3,:3],[0.,1.,0.]))
            gain = state["body"]
            if role == "tail":
                gain = state["tail"]
            pitch = angle*gain
            yaw = state["yaw"] * profile["yaw_weights"].get(role,0.) / len(angles)
            r[node] = _qmul(r[node],_qmul(A.axis_q(pitch_axis,np.radians(pitch)),A.axis_q(yaw_axis,np.radians(yaw))))
    jaw = rig.roles["jaw_lower"][0]
    basejaw = r[jaw].copy()
    # Same rostral-surface opening polarity as R5; determine from actual skin.
    def jaw_at(fraction):
        r[jaw] = _qmul(basejaw,A.axis_q(source["axes_local_xyz"]["pitch"],np.radians(profile["gape_degrees"])*fraction))
        return float(rig.skin(rig.world(t,r,s),rig.lower_jaw_indices)[:,1].min())
    gape = state["jaw"]
    floor = rig.ground + profile["jaw_clearance_height_fraction"]*metrics["body_height_m"]
    if jaw_at(gape) < floor:
        if jaw_at(0.) < floor:
            raise ValueError("closed jaw below floor: reject body pose")
        lo,hi = 0.,gape
        for _ in range(16):
            mid=(lo+hi)/2
            if jaw_at(mid)>=floor:lo=mid
            else:hi=mid
        gape=lo
        jaw_at(gape)
    legs = {side:support(rig,t,r,s,neutral,side,profile["support_limits"]) for side in rig.legs}
    state["actual_jaw_degrees"] = gape*profile["gape_degrees"]
    return t,r,s,state,legs


def build(profile_path=HERE/"profile.json",output=HERE/"feeding.glb",receipt_path=HERE/"receipt.json"):
    profile_raw=profile_path.read_bytes()
    profile=json.loads(profile_raw)
    source,rig=setup(profile)
    d,bi=rig.d,rig.binary
    anim=B.S.animation_by_name(d,source["source"]["clip"])
    channels=B.channel_accessors(d,anim)
    count=source["source"]["sample_count"]
    times=np.linspace(0,profile["duration_seconds"],count)
    t0,r0,s0=rig.pose(0)
    w0=rig.world(t0,r0,s0)
    rows={key:[] for key in channels}
    samples=[]
    for time in times:
        t,r,s,state,legs=pose(rig,source,profile,float(time))
        w=rig.world(t,r,s)
        for key in rows:
            node,path=key
            rows[key].append(tuple({"translation":t,"rotation":r,"scale":s}[path][node]))
        samples.append({"time_seconds":float(time),"state":{k:float(v) for k,v in state.items()},
                        "pelvis_world":w[rig.roles["pelvis"][0],:3,3].tolist(),
                        "upper_mouth":rig.centroid(w,"upper").tolist(),"lower_mouth":rig.centroid(w,"lower").tolist(),"support":legs})
    for key,values in rows.items():
        # Quaternion sign continuity is explicit, including serialization.
        if key[1]=="rotation":
            for i in range(1,len(values)):
                if np.dot(values[i-1],values[i])<0:values[i]=tuple(-np.asarray(values[i]))
        B.S.write_accessor(d,bi,channels[key][1],values)
    for ia in {v[0] for v in channels.values()}:
        B.S.write_accessor(d,bi,ia,[(float(t),) for t in times])
        d["accessors"][ia]["min"]=[0.]
        d["accessors"][ia]["max"]=[profile["duration_seconds"]]
    anim["name"]=CLIP
    encoded=B.S.encode_glb(d,bi)
    reopened=B.Glb.from_bytes(encoded)
    tracks,emitted_times=B._clip_state(reopened,CLIP)
    pelvis=rig.roles["pelvis"][0]
    protected=[n for n in range(len(t0)) if n!=pelvis]
    prior_r=None
    max_rate=0.;rate_peak=None;foot_drift=0.;ankle_drift=0.;sole_drift=0.;min_jaw=float('inf')
    neutral_sole=rig.skin(w0,rig.sole_indices)
    articulation=json.loads((ROOT/"profiles/v9/body-articulation.grounded-bite.v1.json").read_text())
    max_curve=0.;min_pitch=0.;head_range=[]
    lateral=np.cross([0.,1.,0.],rig.forward)
    head=rig.roles['head'][0]
    local_forward=np.linalg.solve(w0[head,:3,:3],rig.forward)
    for i,time in enumerate(emitted_times):
        t,r,s=map(np.asarray,B._pose(reopened,tracks,i))
        if not np.array_equal(t[protected],t0[protected]) or not np.array_equal(s,s0):
            raise ValueError("bone attachment or scale changed")
        w=rig.world(t,r,s)
        for chain in rig.legs.values():
            foot_drift=max(foot_drift,float(np.abs(w[chain[-1]]-w0[chain[-1]]).max()))
            ankle_drift=max(ankle_drift,float(np.linalg.norm(w[chain[-2],:3,3]-w0[chain[-2],:3,3])))
        sole_drift=max(sole_drift,float(np.linalg.norm(rig.skin(w,rig.sole_indices)-neutral_sole,axis=1).max()))
        min_jaw=min(min_jaw,float(rig.skin(w,rig.lower_jaw_indices)[:,1].min()))
        curve=[]
        for role,bounds in articulation['joint_pitch_limits_degrees'].items():
            for node,(low,high) in zip(rig.roles[role],bounds):
                q=np.asarray(_qmul(np.r_[-r0[node,:3],r0[node,3]],r[node]))
                if q[3]<0:q=-q
                axis=unit(np.linalg.solve(w0[node,:3,:3],lateral))
                pitch=float(np.degrees(2*np.arctan2(q[:3]@axis,q[3])))
                if not low-1e-4<=pitch<=high+1e-4:raise ValueError(f"articulation {role} outside R5 envelope")
                if role in ('chest','neck','head'):curve.append(pitch)
        max_curve=max(max_curve,float(np.abs(np.diff(curve)).max()))
        min_pitch=min(min_pitch,min(curve))
        f=w[head,:3,:3]@local_forward
        head_range.append(float(np.degrees(np.arctan2(-f[1],f@rig.forward))))
        if prior_r is not None:
            dots=np.clip(np.abs(np.sum(prior_r*r,axis=1)),0.,1.)
            rates=np.degrees(2*np.arccos(dots))/(time-emitted_times[i-1])
            if rates.max()>max_rate:
                max_rate=float(rates.max());rate_peak=(float(time),int(rates.argmax()))
        prior_r=r
    if foot_drift>1e-5*source['body_metrics']['body_width_m']:raise ValueError('emitted foot drift')
    if max_rate>profile['max_joint_rate_degrees_per_second']:raise ValueError(f'emitted joint rate {max_rate} at {rate_peak}')
    if max_curve>10.0001 or min_pitch < -1.0001:raise ValueError('cervical kink')
    # Place a grounded soft-body proxy under the nominal mouth, not a flying target.
    nominal=samples[int(np.argmin(np.abs(times-1.95/6*profile['duration_seconds'])))]['upper_mouth']
    radius=profile['prop_radius_width_fraction']*source['body_metrics']['body_width_m']
    target=list(nominal);target[1]=rig.ground+radius
    receipt={'status':'REVIEW_CANDIDATE_NOT_USER_ACCEPTED','candidate_sha256':B.sha(encoded),
             'clip':CLIP,'duration_seconds':profile['duration_seconds'],'sample_count':count,
             'source':source['source'],'profile_sha256':B.sha(profile_raw),
             'target':{'world_position_m':target,'preview_prop_radius_m':radius,'ground_y_m':rig.ground},
             'gates':{'bone_attachments_unchanged':True,'bone_scales_unchanged':True,
                      'max_foot_transform_error':foot_drift,'max_ankle_drift_m':ankle_drift,
                      'ground_band_skin_max_drift_m':sole_drift,'minimum_lower_jaw_y_m':min_jaw,
                      'max_joint_rate_degrees_per_second':max_rate,'maximum_cervical_adjacent_pitch_degrees':max_curve,
                      'minimum_cervical_pitch_degrees':min_pitch,'head_nose_down_range_degrees':[min(head_range),max(head_range)]},
             'events':[dict(e,time_seconds=e['reference_time_seconds']/6*profile['duration_seconds']) for e in profile['events']],
             'limitations':profile['limitations'],'samples':samples}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(encoded)
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',type=Path,default=HERE/'profile.json')
    parser.add_argument('--output',type=Path,default=HERE/'feeding.glb')
    parser.add_argument('--receipt',type=Path,default=HERE/'receipt.json')
    args=parser.parse_args()
    result=build(args.profile,args.output,args.receipt)
    print(json.dumps({k:v for k,v in result.items() if k!='samples'},indent=2))
