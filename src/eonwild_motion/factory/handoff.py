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
from ..glb.animation import read_animation_tracks
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import (
    _clip_state, _pose, _world_matrices, _world_position,
    _qinv, _qmul, _q_to_rotvec,
)
from ..solve.skin_targets import points
from .emitted_tangent import descendant_indices, endpoint_tangent, skinned_velocity
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


def _motion_set_baseline_identity(package: Path):
    names = ("motion-set.json", "motion-baseline.json", "motion-intent.json")
    present = [name for name in names if (package / name).is_file()]
    if not present:
        return None
    if len(present) != len(names):
        raise ContractError("handoff motion-set provenance is incomplete")
    lock = _json(package / "inputs.lock.json").get("motion_set_resolution")
    if not isinstance(lock, dict):
        raise ContractError("handoff motion-set resolution is missing")
    return {
        "binding": lock.get("baseline"),
        "identity": lock.get("identities", {}).get("baseline"),
        "snapshot_sha256": _digest(package / "motion-baseline.json"),
    }


def require_shared_motion_baseline(packages):
    identities = [_motion_set_baseline_identity(Path(package)) for package in packages]
    if len(identities) < 2 or any(value != identities[0] for value in identities[1:]):
        raise ContractError("handoff packages differ in shared motion baseline")
    return identities[0]


def _numeric(value):
    array = np.asarray(value)
    if array.dtype.kind not in 'fiu' or not np.isfinite(array).all():
        raise ContractError('handoff evidence must contain finite real numbers')
    return array.astype(float, copy=False)


def require_runtime_axes(runtime, recipe):
    for key in ('forward_axis','up_axis'):
        actual,declared = _numeric(runtime[key]),_numeric(recipe[key])
        if actual.shape!=(3,) or declared.shape!=(3,) or np.linalg.norm(declared)<1e-12:
            raise ContractError('invalid handoff coordinate vector')
        # The compiler normalizes declared axes. Compare in that same canonical
        # representation; do not confuse a float64 normalization ULP with drift.
        expected = declared/np.linalg.norm(declared)
        if not np.allclose(actual,expected,rtol=0,atol=1e-12):
            raise ContractError('handoff runtime coordinate declaration differs from recipe')


def compare_boundaries(before: dict, after: dict, travel_alignment_m, *, test_only_allow_sampled_tangents: bool = False) -> dict:
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
    quadratic = {}
    quadratic['linear_velocity_mps'] = np.linalg.norm(velocity(a[0],a[1],True)-velocity(b[0],b[1],False),axis=1)
    quadratic['skin_velocity_mps'] = np.linalg.norm(velocity(a[0],a[3],True)-velocity(b[0],b[3],False),axis=1)
    def angular(t,qs,terminal):
        endpoint,ids = (-1,[0,1]) if terminal else (0,[1,2])
        deltas = np.array([[_q_to_rotvec(_qmul(_qinv(tuple(qs[endpoint,j])),tuple(qs[i,j])))
                            for j in range(qs.shape[1])] for i in ids])
        return _endpoint_derivative(t[ids]-t[endpoint],deltas.reshape(2,-1)).reshape(-1,3)
    quadratic['angular_velocity_degrees_per_s'] = np.degrees(np.linalg.norm(angular(a[0],a[2],True)-angular(b[0],b[2],False),axis=1))
    quadratic_witness_indices = {key:int(np.argmax(value)) for key,value in quadratic.items()}
    exact_before, exact_after = before.get('exact'), after.get('exact')
    if type(test_only_allow_sampled_tangents) is not bool:
        raise ContractError('handoff test-only tangent option must be boolean')
    if (exact_before is None) != (exact_after is None):
        raise ContractError('handoff exact tangent evidence is incomplete')
    if exact_before is None:
        if not test_only_allow_sampled_tangents:
            raise ContractError('handoff requires exact emitted tangent evidence')
        # This route is deliberately available only to isolated unit fixtures;
        # it cannot be mistaken for emitted FK/LBS tangent validation.
        def adjacent(t, values, terminal):
            left, right = (-2, -1) if terminal else (0, 1)
            return (values[right] - values[left]) / (t[right] - t[left])
        def adjacent_angular(t, qs, terminal):
            left, right = (-2, -1) if terminal else (0, 1)
            return np.asarray([_q_to_rotvec(_qmul(_qinv(tuple(qs[left, index])), tuple(qs[right, index])))
                               for index in range(qs.shape[1])]) / (t[right] - t[left])
        exact = {'linear_velocity_mps':np.linalg.norm(adjacent(a[0],a[1],True)-adjacent(b[0],b[1],False),axis=1),
                 'skin_velocity_mps':np.linalg.norm(adjacent(a[0],a[3],True)-adjacent(b[0],b[3],False),axis=1),
                 'angular_velocity_degrees_per_s':np.degrees(np.linalg.norm(adjacent_angular(a[0],a[2],True)-adjacent_angular(b[0],b[2],False),axis=1))}
        exact_kind = 'adjacent sampled synthetic boundary values'
    else:
        required = {'node_names','world_velocity','skin_labels','skin_velocity','angular_velocity','interpolation'}
        if (not isinstance(exact_before, dict) or not isinstance(exact_after, dict)
            or set(exact_before) != required or set(exact_after) != required
            or exact_before['node_names'] != exact_after['node_names']
            or exact_before['skin_labels'] != exact_after['skin_labels']
            or not isinstance(exact_before['node_names'], list) or not isinstance(exact_before['skin_labels'], list)
            or any(not isinstance(value, str) for value in (*exact_before['node_names'], *exact_before['skin_labels']))
            or not isinstance(exact_before['interpolation'], list) or not isinstance(exact_after['interpolation'], list)
            or not exact_before['interpolation'] or not exact_after['interpolation']
            or any(value not in ('LINEAR', 'CUBICSPLINE') for value in (*exact_before['interpolation'], *exact_after['interpolation']))
            or len(set(exact_before['interpolation'])) != len(exact_before['interpolation'])
            or len(set(exact_after['interpolation'])) != len(exact_after['interpolation'])
            or len(set(exact_before['node_names'])) != len(exact_before['node_names'])
            or len(set(exact_before['skin_labels'])) != len(exact_before['skin_labels'])):
            raise ContractError('handoff exact tangent correspondence differs')
        aw, bw = _numeric(exact_before['world_velocity']), _numeric(exact_after['world_velocity'])
        ask, bsk = _numeric(exact_before['skin_velocity']), _numeric(exact_after['skin_velocity'])
        aa, ba = _numeric(exact_before['angular_velocity']), _numeric(exact_after['angular_velocity'])
        if (aw.shape != bw.shape or aw.ndim != 2 or aw.shape[1] != 3 or len(exact_before['node_names']) != aw.shape[0]
            or aw.shape[0] != a[1].shape[1] or ask.shape != bsk.shape or len(exact_before['skin_labels']) != ask.shape[0]
            or ask.shape[0] != a[3].shape[1]
            or ask.ndim != 2 or ask.shape[1] != 3 or aa.shape != ba.shape or aa.shape != aw.shape):
            raise ContractError('handoff exact tangent shape differs')
        exact = {'linear_velocity_mps':np.linalg.norm(aw-bw,axis=1),
                 'skin_velocity_mps':np.linalg.norm(ask-bsk,axis=1),
                 'angular_velocity_degrees_per_s':np.degrees(np.linalg.norm(aa-ba,axis=1))}
        exact_kind = 'exact serialized TRS endpoint FK/LBS tangents'
    for key, value in exact.items():
        record(key, value)
    limits = {'position_m':POSITION_TOLERANCE_M,'skin_position_m':SKIN_TOLERANCE_M,
        'rotation_degrees':ROTATION_TOLERANCE_DEGREES,
        'linear_velocity_mps':CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S,
        'skin_velocity_mps':CYCLIC_LINEAR_VELOCITY_TOLERANCE_M_S,
        'angular_velocity_degrees_per_s':CYCLIC_ANGULAR_VELOCITY_TOLERANCE_DEG_S}
    checks = {key:errors[key]<=limit for key,limit in limits.items()}
    checks['contact_state'] = before['contacts']==after['contacts']
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
        'values':errors,'limits':limits,'witness_indices':witnesses,
        'before_times_s':a[0].tolist(),'after_times_s':b[0].tolist(),
        'classification':exact_kind,
        'source_interpolation':{'before':exact_before['interpolation'], 'after':exact_after['interpolation']} if exact_before is not None else None,
        'diagnostics':{'quadratic_three_sample_estimate':{'values':{key:float(np.max(value)) for key,value in quadratic.items()},
            'witness_indices':quadratic_witness_indices}}
        }


def require_pair(transition: dict, steady: dict, runtime: dict) -> str:
    if transition.get('program')!='gait_transition' or steady.get('program') not in ('grounded_gait','airborne_gait'):
        raise ContractError('handoff requires a transition and a steady gait')
    for key in ('family','source','rig','contact_profile','performance_profile','forward_axis','up_axis'):
        if key not in transition or transition[key]!=steady.get(key):
            raise ContractError(f'handoff {key} binding differs')
    if transition.get('animal') != steady.get('animal'):
        raise ContractError('handoff animal binding differs')
    if transition.get('articulation_profile') != steady.get('articulation_profile'):
        raise ContractError('handoff articulation profile binding differs')
    if transition.get('gait_profile')!=steady.get('program_profile'):
        raise ContractError('handoff gait profile is not the bound steady program')
    contract = runtime.get('transition_contract') or {}
    kind = contract.get('kind')
    phase = contract.get('steady_phase_s')
    interface = contract.get('interface_schema', 'eonwild.motion.gait-interface.v1')
    if (kind not in ('start','stop') or type(phase) not in (float,int) or not np.isfinite(phase)
        or phase < 0 or interface not in ('eonwild.motion.gait-interface.v1', 'eonwild.motion.gait-interface.v2')
        or (interface == 'eonwild.motion.gait-interface.v1' and phase != 0)):
        raise ContractError('handoff requires an explicit supported phase contract')
    return kind


def _skin_boundary(glb, profile, name, times, indices):
    # The extractor validates the complete clip, including both real endpoints.
    # Never replace its full-timeline requirement with a cropped witness set.
    frames,_ = _source_frames(glb,profile,animation_name=name,sample_times=times.tolist())
    if len(frames)!=len(times):
        raise ContractError('handoff skin timeline is incomplete')
    actual = _numeric([frame['time_s'] for frame in frames])
    if not np.allclose(actual,times,rtol=0,atol=2e-6):
        raise ContractError('handoff skin timeline differs from serialized samples')
    sizes = None
    for frame in frames:
        shape = tuple(points(frame,side).shape for side in ('left','right'))
        if sizes is not None and shape!=sizes:
            raise ContractError('handoff skin material correspondence changes')
        sizes = shape
    return [frames[i] for i in indices]


def _endpoint_index(times: np.ndarray, *, terminal: bool, phase_s: float) -> int:
    endpoint = len(times) - 1 if terminal else 0
    if phase_s:
        matches = np.flatnonzero(np.abs(times - phase_s) <= 2e-6)
        if len(matches) != 1:
            raise ContractError('declared handoff phase must identify one actual native sample')
        endpoint = int(matches[0])
    return endpoint


def _serialized_motor_velocity(package: Path, *, terminal: bool, phase_s: float = 0.) -> np.ndarray:
    """Recover the motor velocity from the two exact serialized root tangents."""
    runtime, recipe = _json(package/'runtime.json'), _json(package/'recipe.json')
    require_runtime_axes(runtime, recipe)
    values = []
    binding = None
    for mode in ('root_motion', 'in_place'):
        glb = Glb.from_bytes((package/f'{mode}.glb').read_bytes())
        animations = glb.document.get('animations', [])
        if len(animations) != 1:
            raise ContractError('handoff requires exactly one exported clip')
        tracks, times = read_animation_tracks(glb, animations[0]['name'], require_common_timeline=True)
        times = _numeric(times)
        endpoint = _endpoint_index(times, terminal=terminal, phase_s=phase_s)
        root_name = runtime['rig_roles']['root']
        try:
            root = glb.name_to_node[root_name]
        except (KeyError, TypeError) as exc:
            raise ContractError('handoff serialized root binding is invalid') from exc
        topology = tuple((node.get('name'), glb.parents[index]) for index, node in enumerate(glb.nodes))
        interpolation = tuple(sorted(set(track.interpolation for track in tracks.values())))
        current = (tuple(times.tolist()), topology, root_name, root, interpolation)
        if binding is not None and current != binding:
            raise ContractError('handoff serialized mode topology or timeline differs')
        binding = current
        tangent = endpoint_tangent(glb, animations[0]['name'], endpoint=endpoint, terminal=terminal)
        if tangent.names[root] != root_name or tangent.time_s != float(times[endpoint]):
            raise ContractError('handoff serialized root endpoint binding differs')
        values.append(_numeric(tangent.world_velocity[root, :3, 3]))
    motor = values[0] - values[1]
    if motor.shape != (3,) or not np.isfinite(motor).all():
        raise ContractError('handoff serialized motor velocity is invalid')
    return motor


def _boundary(package: Path, *, terminal: bool, mode: str, profile: dict, phase_s: float = 0., motor_velocity=None):
    glb = Glb.from_bytes((package/f'{mode}.glb').read_bytes())
    runtime,plan,recipe = _json(package/'runtime.json'),_json(package/'plan.json'),_json(package/'recipe.json')
    require_runtime_axes(runtime,recipe)
    if runtime.get('ground_plane')!=profile['geometry']['ground']:
        raise ContractError('handoff runtime ground differs from the locked floor')
    animations = glb.document.get('animations',[])
    if len(animations)!=1:
        raise ContractError('handoff requires exactly one exported clip')
    tracks,times = _clip_state(glb,animations[0]['name'])
    times = _numeric(times)
    pt = _numeric([row['time_s'] for row in plan['samples']])
    if len(times)<3 or pt.shape!=times.shape or np.any(np.diff(times)<=0) or np.max(np.abs(pt-times))>2e-6:
        raise ContractError('handoff serialized and planned timelines differ')
    parsed, parsed_times = read_animation_tracks(
        glb, animations[0]['name'], require_common_timeline=True
    )
    if not np.array_equal(parsed_times, times):
        raise ContractError('invalid handoff serialized channel timeline')
    for (_, path), track in parsed.items():
        if path not in ('rotation','translation','scale') or track.values.shape != (len(times), 4 if path == 'rotation' else 3):
            raise ContractError('invalid handoff serialized channel')
        norms = np.linalg.norm(track.values, axis=1) if path == 'rotation' else None
        if path == 'rotation' and np.any(norms <= 1e-15):
            raise ContractError('invalid handoff serialized quaternion')
        if path == 'rotation' and track.interpolation == 'LINEAR' and np.max(np.abs(norms - 1)) > 1e-4:
            raise ContractError('invalid handoff serialized quaternion')
    endpoint = _endpoint_index(times, terminal=terminal, phase_s=phase_s)
    ids = list(range(endpoint - 2, endpoint + 1)) if terminal else list(range(endpoint, endpoint + 3))
    if min(ids) < 0 or max(ids) >= len(times):
        raise ContractError('declared handoff phase has insufficient native context')
    root = glb.name_to_node[runtime['rig_roles']['root']]
    descendants = descendant_indices(glb, root)
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
    frames = _skin_boundary(glb,profile,animations[0]['name'],times,ids)
    skin = [np.concatenate([points(frame,side) for side in ('left','right')])+
            (forward*distance if mode=='in_place' else np.zeros(3)) for frame,distance in zip(frames,travel)]
    tangent = endpoint_tangent(glb, animations[0]['name'], endpoint=endpoint, terminal=terminal)
    if mode == 'in_place':
        motor_velocity = _numeric(motor_velocity)
        if motor_velocity.shape != (3,):
            raise ContractError('handoff requires exact serialized motor velocity')
    elif motor_velocity is not None:
        raise ContractError('root-motion handoff cannot apply a separate motor velocity')
    else:
        motor_velocity = np.zeros(3)
    labels, skin_tangent = skinned_velocity(glb, profile, tangent)
    world_tangent = tangent.world_velocity[descendants, :3, 3] + motor_velocity
    skin_tangent = skin_tangent + motor_velocity
    exact = {'node_names':[tangent.names[index] for index in descendants],
             'world_velocity':world_tangent.tolist(), 'skin_labels':labels,
             'skin_velocity':skin_tangent.tolist(),
             'angular_velocity':tangent.angular_velocity[descendants].tolist(),
             'interpolation':sorted(set(track.interpolation for track in parsed.values()))}
    data = {'times':times[ids],'positions':world,'rotations':rotations,'skin':skin,
        'contacts':{side:plan['samples'][endpoint]['feet'][side]['contact'] for side in ('left','right')}, 'exact':exact}
    topology = [(tangent.names[index], None if glb.parents[index] is None else tangent.names[int(glb.parents[index])])
                for index in descendants]
    return data,float(travel[-1 if terminal else 0]),topology


def verify_handoff(transition: Path, steady: Path, *, root: Path) -> dict:
    paths = [Path(transition),Path(steady)]
    hashes = [_digest(p/'manifest.json') for p in paths]
    verifications = [verify_package(p) for p in paths]
    tr,sr = [_json(p/'recipe.json') for p in paths]
    require_shared_motion_baseline(paths)
    kind = require_pair(tr,sr,_json(paths[0]/'runtime.json'))
    root = root.resolve()
    def locked(reference):
        path=(root/reference['path']).resolve()
        if root not in path.parents or _digest(path)!=reference['sha256']:
            raise ContractError('handoff profile is not the locked source')
        return _json(path)
    profile,rig = locked(tr['contact_profile']),locked(tr['rig'])
    from ..planning.gait_transition import load_gait_transition, declared_handoff_phase
    from ..planning.grounded_gait import load_grounded_gait
    from ..planning.airborne_gait import load_airborne_gait
    transition_profile = load_gait_transition(locked(tr['program_profile']))
    gait_document = locked(tr['gait_profile'])
    gait = (load_grounded_gait(gait_document) if sr['program'] == 'grounded_gait' else load_airborne_gait(gait_document))
    phase = declared_handoff_phase(transition_profile, gait)
    contract = _json(paths[0]/'runtime.json')['transition_contract']
    if contract['steady_phase_s'] != phase or transition_profile.kind != kind:
        raise ContractError('handoff phase or kind differs from the locked program')
    for path in paths:
        if _json(path/'runtime.json')['rig_roles']!=rig['roles']:
            raise ContractError('handoff runtime roles differ from the locked rig')
    before,after = paths if kind=='start' else paths[::-1]
    modes = {}
    for mode in ('root_motion','in_place'):
        before_phase = phase if kind=='stop' else 0.
        after_phase = phase if kind=='start' else 0.
        motor_a = _serialized_motor_velocity(before, terminal=True, phase_s=before_phase) if mode == 'in_place' else None
        motor_b = _serialized_motor_velocity(after, terminal=False, phase_s=after_phase) if mode == 'in_place' else None
        a,da,topology_a = _boundary(before,terminal=True,mode=mode,profile=profile,phase_s=before_phase,motor_velocity=motor_a)
        b,db,topology_b = _boundary(after,terminal=False,mode=mode,profile=profile,phase_s=after_phase,motor_velocity=motor_b)
        if topology_a!=topology_b:
            raise ContractError('handoff motion-owned topology differs')
        modes[mode] = compare_boundaries(a,b,_numeric(tr['forward_axis'])*(da-db))
        modes[mode]['motion_owned_nodes'] = [name for name,_ in topology_a]
        modes[mode]['serialized_motor_velocity_mps'] = {
            'before': (np.zeros(3) if motor_a is None else motor_a).tolist(),
            'after': (np.zeros(3) if motor_b is None else motor_b).tolist(),
        }
    for p,expected in zip(paths,hashes):
        verify_package(p)
        if _digest(p/'manifest.json')!=expected:
            raise ContractError('handoff input mutated during inspection')
    technical = all(v['technical_status']=='PASS' for v in verifications)
    return {'schema':'eonwild.motion.handoff-validation.v1','kind':kind, 'steady_phase_s': phase,
        'status':'PASS' if technical and all(v['status']=='PASS' for v in modes.values()) else 'BLOCKED',
        'individual_technical_status':[v['technical_status'] for v in verifications],
        'packages':[{'id':r['id'],'manifest_sha256':s,'root_motion_sha256':_digest(p/'root_motion.glb'),
                     'in_place_sha256':_digest(p/'in_place.glb')} for p,r,s in zip(paths,[tr,sr],hashes)],
        'modes':modes,'visual_review':'PENDING','unity_validation':'NOT_RUN','production_approved':False,
        'classification':'independent native-time emitted pose, velocity, contact and material join; no crossfade or runtime claim'}
