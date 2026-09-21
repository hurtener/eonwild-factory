#!/usr/bin/env python3
"""Diagnostic semantic skin adapter for a saved planar or spatial Moco replay.

No running solver, contact correction or time warp is applied. Optional jaw-only
breathing is explicitly authored. Artist lengths/rest curvature are retained.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from eonwild_motion.factory.compiler import compile_motion_set
from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from eonwild_motion.solve.skin_rig import SkinRig
from eonwild_motion.layers.leg_contact_resolve_v3 import _world_matrices
from eonwild_motion.solve.whole_body_gait_transition import _append_accessor, _encode
from eonwild_motion.glb.container import Glb
from eonwild_motion.glb.animation import read_animation_tracks


def align(a, b):
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    axis = np.cross(a, b)
    sine, cosine = np.linalg.norm(axis), np.clip(a @ b, -1, 1)
    if sine < 1e-10:
        if cosine > 0:
            return np.eye(3)
        axis = np.cross(a, np.eye(3)[np.argmin(abs(a))])
        return Rotation.from_rotvec(axis / np.linalg.norm(axis) * np.pi).as_matrix()
    return Rotation.from_rotvec(axis / sine * np.arctan2(sine, cosine)).as_matrix()


def main():
    ap = argparse.ArgumentParser()
    for name in ('motion-set', 'profile', 'replay', 'output'):
        ap.add_argument('--' + name, type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise ValueError('Refusing to overwrite a retarget candidate')
    captured = {}
    class Captured(Exception): pass
    original = CanonicalConstantSkinTargetLaw.__dict__['build']
    def intercept(cls, query, provider, **kw):
        captured.update(context=query.context, source=kw['source'], contact=kw['contact_profile'])
        raise Captured()
    CanonicalConstantSkinTargetLaw.build = classmethod(intercept)
    try:
        try:
            compile_motion_set(a.motion_set.resolve(), 'walk', root=Path.cwd(), output=a.output.with_suffix('.never-published'))
        except Captured:
            pass
    finally:
        CanonicalConstantSkinTargetLaw.build = original
    c, source = captured['context'], captured['source']
    data, profile = json.loads(a.replay.read_text()), json.loads(a.profile.read_text())
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    admission = data['metadata']['admission']
    if sha(source.raw) != admission['source_geometry_sha256'] or sha(a.profile.read_bytes()) != admission['profile_sha256']:
        raise ValueError('Saved Moco anatomy does not match the fresh admitted rig/profile')
    roles = {b['role']: source.name_to_node[b['bone']] for b in profile['bindings']}
    base = np.asarray(c.base_w)
    basis = np.column_stack((c.forward, c.up, c.lateral))
    origin = (base[roles['leftLeg.0'], :3, 3] + base[roles['rightLeg.0'], :3, 3]) / 2
    skin = SkinRig(source, c.roles, c.forward, c.up, captured['contact'])
    nose_local=None
    if 'nose' in admission['points']:
        nose_world=origin+basis@np.array(admission['points']['nose'])
        nose_local=np.linalg.inv(base[roles['head']])@np.r_[nose_world,1.]
    ground = np.asarray(c.up) * skin.ground
    period = data['frames'][-1]['time_s']
    step = admission['step_length_m']
    def pitch(angle):
        return basis @ Rotation.from_rotvec([0, 0, angle]).as_matrix() @ basis.T
    breathing=data['metadata'].get('recipe',{}).get('jaw_breathing')
    cycles=breathing.get('period_strides',1) if breathing else 1
    if cycles not in (1,2,3,4):raise ValueError('Jaw breathing period must be 1 to 4 full strides')
    cycles=int(cycles)
    halves=2*cycles
    times, poses, target_rows = [], [], []
    for half in range(halves):
        for row in data['frames'][:-1]:
            times.append(half * period + row['time_s'])
            target_rows.append((half, row))
    times.append(halves * period)
    target_rows.append((halves, data['frames'][0]))
    spatial=data['metadata'].get('spatial')
    targets = []
    for half, row in target_rows:
        tr, ro = np.array(c.base_t).copy(), np.array(c.base_r).copy()
        if 'foot_geometry' in data['metadata'] and c.jaw is not None and c.jaw_neutral_close_degrees:
            from eonwild_motion.solve.jaw_response import compose_jaw_rotation
            gape=0.
            if breathing:
                phase=2*np.pi*(half*period+row['time_s'])/(halves*period)
                gape=breathing['minimum_gape_degrees']+.5*(1-np.cos(phase))*(breathing['maximum_gape_degrees']-breathing['minimum_gape_degrees'])
            ro[c.jaw]=compose_jaw_rotation(c.base_r[c.jaw],c.jaw_axis,
                neutral_close_degrees=c.jaw_neutral_close_degrees,breathing_gape_degrees=float(gape),gain=1.)
        def worlds(): return np.asarray(_world_matrices(source, tr, ro, c.base_s))
        def set_world(node, rotation, position=None):
            w = worlds()
            parent = source.parents[node]
            pr = np.eye(3) if parent is None else Rotation.from_matrix(w[parent, :3, :3]).as_matrix()
            ro[node] = Rotation.from_matrix(pr.T @ rotation).as_quat()
            if position is not None:
                tr[node] = position if parent is None else (np.linalg.inv(w[parent]) @ np.r_[position, 1])[:3]
        q = {name: value['value'] for name, value in row['coordinates'].items()}
        reflection=np.diag([1,1,-1]) if half%2 else np.eye(3)
        def body_rotation(name):
            return basis@reflection@np.array(row['bodies'][name]['rotation'])@reflection@basis.T
        trunk = body_rotation('trunk') if spatial else pitch(q['pitch'])
        root = roles['root']
        root_origin = ground + basis @ (reflection@np.array(row['bodies']['trunk']['origin']) + [half * step, 0, 0])
        set_world(root, trunk @ base[root, :3, :3], root_origin + trunk @ (base[root, :3, 3] - origin))
        frame_targets = {}
        if spatial:
            for binding in data['metadata']['axial_bindings']:
                node=roles[binding['role']]
                set_world(node,body_rotation(binding['body'])@base[node,:3,:3])
                frame_targets[binding['role']]=(ground+basis@(reflection@np.array(row['bodies'][binding['body']]['origin'])+[half*step,0,0])).tolist()
            tail_end=max((r for r in roles if r.startswith('tail.')),key=lambda r:int(r.split('.')[-1]))
            frame_targets[tail_end]=(ground+basis@(reflection@np.array(row['bodies']['tail_3']['end'])+[half*step,0,0])).tolist()
        else:
            # One mechanical neck and two tail regions. Retain the artist's rest
            # curvature within each rigid region; do not invent lateral motion.
            if 'chest' in q:
                node=roles[data['metadata']['chest_semantic_role']]
                set_world(node,pitch(q['pitch']+q['chest'])@base[node,:3,:3])
            for role, angle in [('neck.0', q['pitch'] + q.get('chest',0) + q['neck']),
                                ('tail.0', q['pitch'] + q['tail_proximal']),
                                ('tail.4', q['pitch'] + q['tail_proximal'] + q['tail_distal'])]:
                node = roles[role]
                set_world(node, pitch(angle) @ base[node, :3, :3])
        for side, suffix in [('left', 'l'), ('right', 'r')]:
            source_side = suffix if half % 2 == 0 else ('r' if suffix == 'l' else 'l')
            def point(part, endpoint):
                p = np.array(row['bodies'][part + '_' + source_side][endpoint])
                p[0] += half * step
                if half % 2: p[2] *= -1
                return ground + basis @ p
            for i, part in enumerate(('thigh', 'shin', 'metatarsus')):
                node, child = roles[f'{side}Leg.{i}'], roles[f'{side}Leg.{i+1}']
                direction = point(part, 'end') - point(part, 'origin')
                if spatial:
                    # The model limb is -Y at zero angle. Transfer full rotation,
                    # including hip yaw/roll, with the artist's rest orientation.
                    correction=align(base[child,:3,3]-base[node,:3,3],basis@np.array([0,-1,0]))
                    rotation=body_rotation(part+'_'+source_side)@correction@base[node,:3,:3]
                else:
                    rotation = align(base[child, :3, 3] - base[node, :3, 3], direction) @ base[node, :3, :3]
                set_world(node, rotation)
                frame_targets[f'{side}Leg.{i}'] = point(part, 'origin').tolist()
            frame_targets[f'{side}Leg.3'] = point('toe', 'origin').tolist()
            if 'foot_geometry' in data['metadata']:
                # The calibrated toe's local extent is slanted in the artist
                # rest frame. Use its solved body rotation, not extent angle.
                angle=sum(q[k] for k in ['pitch','hip_'+source_side,'knee_'+source_side,'ankle_'+source_side,'mtp_'+source_side])
            else:
                toe = point('toe', 'end') - point('toe', 'origin')
                angle = np.arctan2(toe @ c.up, toe @ c.forward)
            foot = roles[f'{side}Leg.3']
            foot_rotation=body_rotation('toe_'+source_side) if spatial else pitch(angle)
            set_world(foot, foot_rotation @ base[foot, :3, :3])
            if 'digit_'+source_side in q:
                for role,node in roles.items():
                    if role.startswith('legs.'+side+'.toeChains.') and role.endswith('.1'):
                        digit_rotation=body_rotation('digit_'+source_side) if spatial else pitch(angle+q['digit_'+source_side])
                        set_world(node,digit_rotation@base[node,:3,:3])
        poses.append((tr, ro))
        targets.append(frame_targets)
    tr = np.asarray([p[0] for p in poses]); ro = np.asarray([p[1] for p in poses])
    for i in range(1, len(ro)):
        ro[i, np.sum(ro[i-1] * ro[i], axis=1) < 0] *= -1
    document, binary = deepcopy(source.document), bytearray(source.binary)
    ta = _append_accessor(document, binary, np.asarray(times), 'SCALAR')
    samplers, channels = [], []
    for node in range(len(source.nodes)):
        for path, values, kind in [('translation', tr[:, node], 'VEC3'), ('rotation', ro[:, node], 'VEC4')]:
            acc = _append_accessor(document, binary, values, kind)
            samplers.append(dict(input=ta, output=acc, interpolation='LINEAR'))
            channels.append(dict(sampler=len(samplers)-1, target=dict(node=node, path=path)))
    document['animations'] = [dict(name='moco-prototype', samplers=samplers, channels=channels)]
    document['buffers'][0]['byteLength'] = len(binary)
    a.output.mkdir(parents=True)
    payload = _encode(document, binary)
    (a.output / 'root_motion.glb').write_bytes(payload)
    (a.output / 'source-animal.profile.json').write_bytes(a.profile.read_bytes())
    emitted = Glb(a.output / 'root_motion.glb')
    tracks, _ = read_animation_tracks(emitted, 'moco-prototype', require_common_timeline=True)
    reopened = SkinRig(emitted, c.roles, c.forward, c.up, captured['contact'])
    measurements = []
    for t, frame_targets in zip(times, targets):
        ts, rs = list(c.base_t), list(c.base_r)
        for (node, path), track in tracks.items():
            if path == 'translation': ts[node] = tuple(track.sample(t))
            elif path == 'rotation': rs[node] = tuple(track.sample(t))
        w = np.asarray(_world_matrices(emitted, ts, rs, c.base_s))
        landmarks={role: w[node, :3, 3].tolist() for role, node in roles.items()}
        if nose_local is not None:landmarks['skull_fixed_nose']=(w[roles['head']]@nose_local)[:3].tolist()
        measurements.append(dict(time_s=t,
            joint_error_m={role: float(np.linalg.norm(w[roles[role], :3, 3] - p)) for role, p in frame_targets.items()},
            skin_floor_min_m={s: float((reopened.skin(w, ids) @ c.up).min() - skin.ground) for s, ids in reopened.foot_masks.items()},
            landmarks=landmarks))
    optimization_status=data['report']['optimizer']['status']
    source_method='Spatial inverse-dynamics initializer' if optimization_status=='REDUCED_COORDINATE_INITIALIZER' else ('Spatial Moco trajectory' if spatial else 'Planar Moco trajectory')
    receipt = dict(schema='eonwild.motion.moco-skin-diagnostic.v1', status='EXPERIMENTAL_RETARGET', production=False,
        visual='PENDING', source_sha256=sha(source.raw), replay_sha256=sha(a.replay.read_bytes()),
        model_sha256=data['metadata']['model_sha256'], emitted_sha256=sha(payload), duration_s=halves*period,
        root_advance_m=halves*step, frames=len(times),jaw_breathing=breathing,
        source_optimization_status=optimization_status,
        method=source_method+'. Saved body rotations/directions and reflected half-stride symmetry. '+
            'Rotation-only limb transfer, original artist lengths and rest curvature. Calibrated models include chest and distal toe motion plus admitted jaw-neutral closure. No contact correction. '+('Explicit authored jaw breathing, not simulated respiration.' if breathing else 'No dynamic secondary layer.'),
        maximum_joint_error_m=max(v for m in measurements for v in m['joint_error_m'].values()),
        minimum_skin_floor_m=min(v for m in measurements for v in m['skin_floor_min_m'].values()),
        measurements=measurements)
    (a.output / 'retarget.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k != 'measurements'}, indent=2))


if __name__ == '__main__': main()
