"""Read-only joins between emitted transition and bound steady packages.

No phase search, fitting, retiming, crossfade or animation transfer occurs.
Only the declared motor displacement aligns the two coordinate frames.
Unity runtime blending and visual quality remain separate requirements.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from ..contact_gauge import _source_frames
from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import (
    _clip_state, _pose, _world_matrices, _world_position,
    _qinv, _qmul, _q_to_rotvec,
)
from ..solve.skin_targets import points
from .compiler import verify_package
from .quality import (
    CYCLIC_ANGULAR_VELOCITY_TOLERANCE_DEG_S,
    CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S, _endpoint_derivative,
)

POSITION_TOLERANCE_M = .001
SKIN_TOLERANCE_M = .0005
ROTATION_TOLERANCE_DEGREES = .5


def _json(path):
    return json.loads(path.read_text())


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _numeric(value):
    array = np.asarray(value)
    if array.dtype.kind not in 'fiu' or not np.isfinite(array).all():
        raise ContractError('handoff evidence must contain finite real numbers')
    return array.astype(float, copy=False)


def compare_boundaries(before: dict, after: dict, travel_alignment_m) -> dict:
    """Measure native three-sample windows, preserving the original endpoints."""
    shift = _numeric(travel_alignment_m)
    if shift.shape != (3,):
        raise ContractError('handoff alignment must be a finite vector')
    cooked = []
    for value in (before, after):
        t, p, q, s = [_numeric(value[key]) for key in ('times','positions','rotations','skin')]
        if (t.shape != (3,) or np.any(np.diff(t) <= 0)
            or p.ndim != 3 or p.shape[0] != 3 or p.shape[2] != 3 or not p.shape[1]
            or q.shape != (3,p.shape[1],4)
            or s.ndim != 3 or s.shape[0] != 3 or s.shape[2] != 3 or not s.shape[1]):
            raise ContractError('invalid native handoff boundary evidence')
        norms = np.linalg.norm(q,axis=2,keepdims=True)
        if np.max(np.abs(norms-1)) > 1e-4:
            raise ContractError('invalid handoff quaternion')
        contacts = value['contacts']
        if set(contacts) != {'left','right'} or any(type(x) is not bool for x in contacts.values()):
            raise ContractError('invalid handoff contact declaration')
        cooked.append((t,p,q/norms,s))
    a,b = cooked
    if a[1].shape != b[1].shape or a[3].shape != b[3].shape:
        raise ContractError('handoff node or material correspondence differs')
    errors,witnesses = {},{}
    def record(name,values):
        index = int(np.argmax(values))
        errors[name],witnesses[name] = float(values[index]),index
    record('position_m',np.linalg.norm(a[1][-1]-shift-b[1][0],axis=1))
    record('skin_position_m',np.linalg.norm(a[3][-1]-shift-b[3][0],axis=1))
    dots = np.abs(np.sum(a[2][-1]*b[2][0],axis=1))
    record('rotation_degrees',np.degrees(2*np.arccos(np.clip(dots,0,1))))
    def velocity(t,values,terminal):
        end = -1 if terminal else 0
        ids = [0,1] if terminal else [1,2]
        return _endpoint_derivative(t[ids]-t[end],(values[ids]-values[end]).reshape(2,-1)).reshape(values.shape[1:])
    record('linear_velocity_mps',np.linalg.norm(velocity(a[0],a[1],True)-velocity(b[0],b[1],False),axis=1))
    record('skin_velocity_mps',np.linalg.norm(velocity(a[0],a[3],True)-velocity(b[0],b[3],False),axis=1))
    def angular(t,qs,terminal):
        endpoint,ids = (-1,[0,1]) if terminal else (0,[1,2])
        deltas = np.array([[_q_to_rotvec(_qmul(_qinv(tuple(qs[endpoint,j])),tuple(qs[i,j])))
                            for j in range(qs.shape[1])] for i in ids])
        return _endpoint_derivative(t[ids]-t[endpoint],deltas.reshape(2,-1)).reshape(-1,3)
    record('angular_velocity_degrees_per_s',np.degrees(np.linalg.norm(angular(a[0],a[2],True)-angular(b[0],b[2],False),axis=1)))
    limits = {'position_m':POSITION_TOLERANCE_M,'skin_position_m':SKIN_TOLERANCE_M,
        'rotation_degrees':ROTATION_TOLERANCE_DEGREES,
        'linear_velocity_mps':CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S,
        'skin_velocity_mps':CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S,
        'angular_velocity_degrees_per_s':CYCLIC_ANGULAR_VELOCITY_TOLERANCE_DEG_S}
    checks = {key:errors[key]<=limit for key,limit in limits.items()}
    checks['contact_state'] = before['contacts']==after['contacts']
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
        'values':errors,'limits':limits,'witness_indices':witnesses,
        'before_times_s':a[0].tolist(),'after_times_s':b[0].tolist()}


def require_pair(transition: dict, steady: dict, runtime: dict) -> str:
    if transition.get('program')!='gait_transition' or steady.get('program') not in ('grounded_gait','airborne_gait'):
        raise ContractError('handoff requires a transition and a steady gait')
    for key in ('family','source','rig','contact_profile','performance_profile','forward_axis','up_axis'):
        if key not in transition or transition[key]!=steady.get(key):
            raise ContractError(f'handoff {key} binding differs')
    if transition.get('gait_profile')!=steady.get('program_profile'):
        raise ContractError('handoff gait profile is not the bound steady program')
    contract = runtime.get('transition_contract') or {}
    kind = contract.get('kind')
    phase = contract.get('steady_phase')
    if kind not in ('start','stop') or type(phase) not in (float,int) or phase!=0:
        raise ContractError('handoff requires an explicit phase-zero transition contract')
    return kind


def _boundary(package: Path, *, terminal: bool, mode: str, profile: dict):
    glb = Glb.from_bytes((package/f'{mode}.glb').read_bytes())
    runtime,plan = _json(package/'runtime.json'),_json(package/'plan.json')
    animations = glb.document.get('animations',[])
    if len(animations)!=1:
        raise ContractError('handoff requires exactly one exported clip')
    tracks,times = _clip_state(glb,animations[0]['name'])
    times = _numeric(times)
    pt = _numeric([row['time_s'] for row in plan['samples']])
    if len(times)<3 or pt.shape!=times.shape or np.any(np.diff(times)<=0) or np.max(np.abs(pt-times))>2e-6:
        raise ContractError('handoff serialized and planned timelines differ')
    # Every original sample is checked, including the real terminal quaternion.
    for channel in animations[0]['channels']:
        sampler = animations[0]['samplers'][channel['sampler']]
        tt = _numeric(glb.accessor_values(sampler['input'])).reshape(-1)
        values = _numeric(glb.accessor_values(sampler['output']))
        path = channel['target']['path']
        width = 4 if path=='rotation' else 3
        if (sampler.get('interpolation','LINEAR')!='LINEAR' or path not in ('rotation','translation','scale')
            or not np.array_equal(tt,times) or values.shape!=(len(times),width)):
            raise ContractError('invalid handoff serialized channel')
        if path=='rotation' and np.max(np.abs(np.linalg.norm(values,axis=1)-1))>1e-4:
            raise ContractError('invalid handoff serialized quaternion')
    ids = list(range(len(times)-3,len(times))) if terminal else [0,1,2]
    root = glb.name_to_node[runtime['rig_roles']['root']]
    descendants = []
    for index in range(len(glb.nodes)):
        cursor,seen = index,set()
        while cursor is not None:
            if cursor in seen:
                raise ContractError('cyclic handoff topology')
            seen.add(cursor)
            if cursor==root:
                descendants.append(index);break
            cursor = glb.parents[cursor]
    if not descendants:
        raise ContractError('handoff has no motion-owned nodes')
    forward = _numeric(runtime['forward_axis'])
    travel = _numeric([plan['samples'][i]['root_forward_m']-plan['samples'][0]['root_forward_m'] for i in ids])
    if forward.shape!=(3,) or abs(np.linalg.norm(forward)-1)>1e-6:
        raise ContractError('invalid handoff travel')
    world,rotations = [],[]
    for index,distance in zip(ids,travel):
        pose = _pose(glb,tracks,index)
        ws = _world_matrices(glb,*pose)
        offset = forward*distance if mode=='in_place' else np.zeros(3)
        world.append([np.asarray(_world_position(ws[n]))+offset for n in descendants])
        rotations.append([pose[1][n] for n in descendants])
    frames,_ = _source_frames(glb,profile,animation_name=animations[0]['name'],sample_times=times[ids].tolist())
    if len(frames)!=3:
        raise ContractError('handoff skin boundary is incomplete')
    skin = [np.concatenate([points(frame,side) for side in ('left','right')])+
            (forward*distance if mode=='in_place' else np.zeros(3)) for frame,distance in zip(frames,travel)]
    endpoint = -1 if terminal else 0
    data = {'times':times[ids],'positions':world,'rotations':rotations,'skin':skin,
        'contacts':{side:plan['samples'][endpoint]['feet'][side]['contact'] for side in ('left','right')}}
    return data,float(travel[-1 if terminal else 0]),[glb.nodes[i].get('name') for i in descendants]


def verify_handoff(transition: Path, steady: Path, *, root: Path) -> dict:
    paths = [Path(transition),Path(steady)]
    hashes = [_digest(p/'manifest.json') for p in paths]
    verifications = [verify_package(p) for p in paths]
    tr,sr = [_json(p/'recipe.json') for p in paths]
    kind = require_pair(tr,sr,_json(paths[0]/'runtime.json'))
    root = root.resolve()
    profile_path = (root/tr['contact_profile']['path']).resolve()
    if root not in profile_path.parents or _digest(profile_path)!=tr['contact_profile']['sha256']:
        raise ContractError('handoff contact profile is not the locked source')
    profile = _json(profile_path)
    before,after = paths if kind=='start' else paths[::-1]
    modes = {}
    for mode in ('root_motion','in_place'):
        a,da,names_a = _boundary(before,terminal=True,mode=mode,profile=profile)
        b,db,names_b = _boundary(after,terminal=False,mode=mode,profile=profile)
        if names_a!=names_b:
            raise ContractError('handoff motion-owned topology differs')
        modes[mode] = compare_boundaries(a,b,_numeric(tr['forward_axis'])*(da-db))
        modes[mode]['motion_owned_nodes'] = names_a
    for p,expected in zip(paths,hashes):
        verify_package(p)
        if _digest(p/'manifest.json')!=expected:
            raise ContractError('handoff input mutated during inspection')
    technical = all(v['technical_status']=='PASS' for v in verifications)
    return {'schema':'eonwild.motion.handoff-validation.v1','kind':kind,
        'status':'PASS' if technical and all(v['status']=='PASS' for v in modes.values()) else 'BLOCKED',
        'individual_technical_status':[v['technical_status'] for v in verifications],
        'packages':[{'id':r['id'],'manifest_sha256':s,'root_motion_sha256':_digest(p/'root_motion.glb'),
                     'in_place_sha256':_digest(p/'in_place.glb')} for p,r,s in zip(paths,[tr,sr],hashes)],
        'modes':modes,'visual_review':'PENDING','unity_validation':'NOT_RUN','production_approved':False,
        'classification':'independent native-time emitted pose, velocity, contact and material join; no crossfade or runtime claim'}
