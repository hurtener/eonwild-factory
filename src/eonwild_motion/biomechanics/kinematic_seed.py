"""Art-directed, contact-aware initial guess for testing a biomechanics bridge.

This is NOT a predicted dinosaur gait or a replacement for the admitted factory
compiler. It supplies a named, reproducible kinematic fixture when no licensed,
validated source-species trajectory is available. All anatomy names and numerical
intent come from profile data. Existing skin/FK and GLB emission are reused.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import hashlib
import math
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.interpolate import CubicSpline
from ..errors import ContractError
from ..glb.container import Glb
from ..solve.skin_rig import SkinRig
from ..solve.whole_body_gait_transition import _append_accessor, _encode


def unit(v):
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v)
    if not np.isfinite(v).all() or n < 1e-10:
        raise ContractError('degenerate kinematic vector')
    return v/n


def rotation(v):
    return Rotation.from_rotvec(np.asarray(v)).as_matrix()


def align(a, b):
    a, b = unit(a), unit(b)
    axis = np.cross(a, b); s = np.linalg.norm(axis); c = np.clip(a@b, -1., 1.)
    if s < 1e-10:
        if c < 0:
            raise ContractError('antipodal segment needs an explicit twist reference')
        return np.eye(3)
    return rotation(axis/s * math.atan2(s, c))


def smooth(x):
    x = np.clip(x, 0., 1.)
    return x*x*x*(10 + x*(-15 + 6*x))


def periodic_curve(knots, values, phase):
    return float(CubicSpline(knots, values, bc_type='periodic')(phase % 1.))


def load_rig(source: Glb, profile: dict):
    if profile.get('schema') != 'eonwild.biomechanics.kinematic-seed.v1':
        raise ContractError('unsupported kinematic seed profile')
    if hashlib.sha256(source.raw).hexdigest() != profile['source']['sha256']:
        raise ContractError('source hash does not match the calibrated asset')
    if source.document.get('animations'):
        raise ContractError('seed requires immutable animation-free source geometry')
    if profile['coordinate'] != {'units':'metres','handedness':'right','up':[0,1,0],'forward':[0,0,1]}:
        raise ContractError('normalize source into declared +Y up/+Z forward before admission')
    if len(source.name_to_node) != len(source.nodes):
        raise ContractError('duplicate source node names make semantic mapping ambiguous')
    roles = profile['roles']
    if set(roles['legs']) != {'left','right'}:
        raise ContractError('requires explicit bilateral semantic legs')
    limb_nodes=[n for leg in roles['legs'].values() for n in leg['contactChain']]
    if len(limb_nodes)!=len(set(limb_nodes)):
        raise ContractError('left and right legs may not share joints')
    def names(value):
        if isinstance(value, str): return [value]
        if isinstance(value, dict): return [n for v in value.values() for n in names(v)]
        return [n for v in value for n in names(v)]
    for name in names(roles):
        if name not in source.name_to_node:
            raise ContractError(f'missing semantic joint: {name}')
    # Anatomical aliases may repeat; each actual limb must be a direct chain.
    for limb in roles['legs'].values():
        chain = limb['contactChain']
        if len(chain) != 4 or len(set(chain)) != 4:
            raise ContractError('requires four distinct hip/knee/ankle/MTP joints')
        for p, c in zip(chain, chain[1:]):
            if source.parents[source.name_to_node[c]] != source.name_to_node[p]:
                raise ContractError('incompatible leg topology')
        for chain in limb['toeChains']:
            for p,c in zip(chain,chain[1:]):
                if source.parents[source.name_to_node[c]] != source.name_to_node[p]:
                    raise ContractError('incompatible digit topology')
    if len(source.document['skins']) != 1:
        raise ContractError('kinematic seed supports one complete skin')
    mesh_nodes = [n for n in source.nodes if n.get('skin') == 0]
    if len(mesh_nodes) != 1:
        raise ContractError('kinematic seed requires one skinned mesh node')
    mesh = mesh_nodes[0]
    primitives = source.document['meshes'][mesh['mesh']]['primitives']
    if len(primitives) != 1:
        raise ContractError('kinematic seed requires one mesh primitive')
    a = primitives[0]['attributes']
    suffixes = sorted([k[7:] for k in a if k.startswith('JOINTS_')], key=int)
    feet = {}
    for side, limb in roles['legs'].items():
        feet[side]={'sole_joints':[limb['contactChain'][-1],limb['pad']],
                    'toe_joints':[n for c in limb['toeChains'] for n in c],
                    'weight_threshold':0.45,
                    'membership_policy':'sum_declared_region_weights.v1'}
    geometry={'skin_index':0,'mesh_node':mesh['name'],'position_accessor':a['POSITION'],
              'joint_accessors':[a['JOINTS_'+s] for s in suffixes],
              'weight_accessors':[a['WEIGHTS_'+s] for s in suffixes],
              'feet':feet,'ground':{'level_m':0.}}
    sk=SkinRig(source,roles,[0,0,1],[0,1,0],{'geometry':geometry})
    # The kinematic OpenSim bridge preserves these tiny source scales; large or
    # non-uniform scales need an explicit separate bind normalization operation.
    if np.max(np.abs(np.asarray(source.rest_scale)-1)) > 2e-5:
        raise ContractError('source scale requires explicit rig preparation')
    settings=profile['authored_seed']
    for key,value in settings.items():
        if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value):
            raise ContractError(f'non-finite or nonnumeric authored setting: {key}')
    if not .5 < settings['duty_factor'] < .8 or settings['cycle_s'] <= 0 or settings['stride_m'] <= 0:
        raise ContractError('invalid grounded seed timing')
    return sk


class Seed:
    def __init__(self, source, profile):
        self.source,self.profile=source,profile
        self.skin=load_rig(source,profile)
        self.roles=profile['roles']; self.cfg=profile['authored_seed']
        self.rest=self.skin.neutral_world
        self.rest_R=np.array([Rotation.from_matrix(w[:3,:3]).as_matrix() for w in self.rest])
        self.names=source.name_to_node
        self.legs={s:[self.names[n] for n in v['contactChain']] for s,v in self.roles['legs'].items()}
        self.root=self.names[self.roles['root']]
        self.mtp_center=float(np.mean([self.rest[c[-1],0,3] for c in self.legs.values()]))
        self.toe_pivot={}
        for side,limb in self.roles['legs'].items():
            mids=[self.names[c[1]] for c in limb['toeChains']]
            self.toe_pivot[side]=float(np.mean(self.rest[mids,2,3]))

    def set_world_rotation(self,t,q,s,node,world_R):
        worlds=self.skin.world(t,q,s)
        p=self.source.parents[node]
        parent_R=np.eye(3) if p is None else Rotation.from_matrix(worlds[p,:3,:3]).as_matrix()
        q[node]=Rotation.from_matrix(parent_R.T@world_R).as_quat()

    def delta(self,t,q,s,name,axis,degrees):
        node=self.names[name]
        w=self.skin.world(t,q,s)
        self.set_world_rotation(t,q,s,node,rotation(np.asarray(axis)*math.radians(degrees))@Rotation.from_matrix(w[node,:3,:3]).as_matrix())

    def foot_plan(self,time,side,standing=False):
        cfg=self.cfg; T=cfg['cycle_s']; d=cfg['duty_factor']; stride=cfg['stride_m'];speed=stride/T
        phase=(time/T+(0 if side=='left' else .5))%1.
        chain=self.legs[side]; mtp0=self.rest[chain[-1],:3,3]
        lane=self.mtp_center+(-.5 if side=='left' else .5)*cfg['track_width_m']
        if standing:
            return np.array([lane,mtp0[1],mtp0[2]]), 0.,0.,True,phase
        if phase <= d:
            z=speed*time+mtp0[2]+stride*(d/2-phase)
            lift=0.
            pitch=cfg['toeoff_pitch_deg']*smooth((phase-(d-.13))/.13)
            meta=periodic_curve([0,.30,d,d+.12,.91,1.],[-18,3,40,45,-28,-18],phase)
        else:
            u=(phase-d)/(1-d)
            # Quintic Hermite transport: both endpoint velocities match the
            # moving body's -speed trajectory; world stance anchors don't slide.
            duration=T*(1-d); travel=stride*d; deriv=-speed*duration
            c3=10*travel-10*deriv; c4=-15*travel+15*deriv; c5=6*travel-6*deriv
            rel=-stride*d/2+deriv*u+c3*u**3+c4*u**4+c5*u**5
            z=speed*time+mtp0[2]+rel
            lift=cfg['swing_clearance_m']*(math.sin(math.pi*u)**2)
            peak=d+.11
            pitch=(cfg['toeoff_pitch_deg']+(cfg['recovery_pitch_deg']-cfg['toeoff_pitch_deg'])*smooth((phase-d)/.11)) if phase<=peak else cfg['recovery_pitch_deg']*(1-smooth((phase-peak)/(1-peak)))
            meta=periodic_curve([0,.30,d,d+.12,.91,1.],[-18,3,40,45,-28,-18],phase)
        base=np.array([lane,mtp0[1]+lift,z])
        # Roll the MTP around an explicitly authored forefoot ground point.
        roll=rotation([math.radians(pitch),0,0])
        offset=np.array([0,mtp0[1],mtp0[2]-self.toe_pivot[side]])
        base+=(roll@offset-offset)
        return base,math.radians(pitch),math.radians(meta),phase<=d,phase

    def solve_leg(self,t,q,s,side,mtp,pitch,meta):
        hip,knee,ankle,foot=self.legs[side]
        rest=self.rest
        ankle_target=mtp+rotation([meta,0,0])@(rest[ankle,:3,3]-rest[foot,:3,3])
        hip_pos=self.skin.world(t,q,s)[hip,:3,3]
        a=np.linalg.norm(rest[knee,:3,3]-rest[hip,:3,3]); b=np.linalg.norm(rest[ankle,:3,3]-rest[knee,:3,3])
        direction=ankle_target-hip_pos;distance=np.linalg.norm(direction)
        if distance >= a+b-1e-5 or distance <= abs(a-b)+1e-5:
            raise ContractError(f'{side} requested seed pose exceeds fixed-length reach: {distance}/{a+b}')
        along=direction/distance
        pole=unit(np.array([0,0,1.])-along*along[2])
        axial=(a*a-b*b+distance*distance)/(2*distance)
        bend=math.sqrt(max(0.,a*a-axial*axial))
        knee_target=hip_pos+axial*along+bend*pole
        self.set_world_rotation(t,q,s,hip,align(rest[knee,:3,3]-rest[hip,:3,3],knee_target-hip_pos)@self.rest_R[hip])
        self.set_world_rotation(t,q,s,knee,align(rest[ankle,:3,3]-rest[knee,:3,3],ankle_target-knee_target)@self.rest_R[knee])
        self.set_world_rotation(t,q,s,ankle,rotation([meta,0,0])@self.rest_R[ankle])
        self.set_world_rotation(t,q,s,foot,rotation([pitch,0,0])@self.rest_R[foot])
        # Retain all digit chains. Progressive toe release is authored rather
        # than treating the entire foot as a rigid paddle.
        phase=self._phase[side]; d=self.cfg['duty_factor']
        toe_gain=smooth((phase-(d-.14))/.14) if phase<=d else 1-smooth((phase-d)/(1-d))
        for chain in self.roles['legs'][side]['toeChains']:
            proximal=self.names[chain[0]]; distal=self.names[chain[1]]
            counter=-pitch*.65*toe_gain
            self.delta(t,q,s,chain[0],[1,0,0],math.degrees(counter))
            # Small separate phalanx recovery; no new bones or reassigned weights.
            curl=self.cfg['toe_curl_deg']*math.sin(math.pi*(phase-d)/(1-d))**2 if phase>d else 0.
            self.delta(t,q,s,chain[1],[1,0,0],curl)
        world=self.skin.world(t,q,s)
        return float(np.linalg.norm(world[foot,:3,3]-mtp))

    def pose(self,time,*,standing=False):
        t,q,s=[np.array(v,dtype=float).copy() for v in self.skin.neutral]
        cfg=self.cfg; phase=time/cfg['cycle_s'];a=2*math.pi*phase;speed=cfg['stride_m']/cfg['cycle_s']
        t[self.root,1]-=cfg['neutral_drop_m']
        if not standing:
            t[self.root,2]+=speed*time
            t[self.root,0]+=cfg['pelvis_sway_m']*math.sin(a-.35)
            t[self.root,1]+=cfg['pelvis_bob_m']*math.cos(2*a-1.1)
            self.delta(t,q,s,self.roles['pelvis'],[0,0,1],cfg['pelvis_roll_deg']*math.sin(a-.35))
            self.delta(t,q,s,self.roles['pelvis'],[0,1,0],cfg['pelvis_yaw_deg']*math.cos(a))
            self.delta(t,q,s,self.roles['chest'],[1,0,0],cfg['chest_pitch_deg']*math.sin(2*a-.4))
            # A damped traveling curvature envelope, not identical rotations on
            # every tail joint and not a claim of simulated angular momentum.
            tail=self.roles['tail']
            for j,name in enumerate(tail):
                w=(.45+.55*j/max(1,len(tail)-1))
                self.delta(t,q,s,name,[0,1,0],cfg['tail_yaw_deg']*w*math.sin(a-j*.22+.8))
                self.delta(t,q,s,name,[1,0,0],cfg['tail_pitch_deg']*w*math.sin(2*a-j*.16))
            neck=self.roles['neck']+[self.roles['head']]
            for name in neck:
                self.delta(t,q,s,name,[1,0,0],-cfg['chest_pitch_deg']*math.sin(2*a-.4)/len(neck))
                self.delta(t,q,s,name,[0,1,0],-cfg['pelvis_yaw_deg']*math.cos(a)/len(neck))
            for side,names in self.roles['arms'].items():
                sign=1 if side=='left' else -1
                self.delta(t,q,s,names[0],[1,0,0],cfg['arm_swing_deg']*math.sin(a)*sign)
        self.delta(t,q,s,self.roles['jaw_lower'],[1,0,0],-cfg['jaw_close_deg'])
        plans={side:self.foot_plan(time,side,standing) for side in self.legs}
        self._phase={side:plan[-1] for side,plan in plans.items()}
        base_q=q.copy(); residual={}
        for side,(mtp,pitch,meta,contact,p) in plans.items():
            target=mtp.copy()
            # Final material-floor solve follows posture, metatarsal and toe
            # changes. Never reuse a skeleton-only receipt as skin evidence.
            for iteration in range(5):
                # Reset only this limb before applying its absolute constraints.
                descendants=self.skin.descendants(self.legs[side][0]); idx=list(descendants)
                q[idx]=base_q[idx]
                residual[side]=self.solve_leg(t,q,s,side,target,pitch,meta)
                world=self.skin.world(t,q,s)
                xyz=self.skin.skin(world,self.skin.foot_masks[side])
                minimum=float(xyz[:,1].min())
                if contact or standing:
                    correction=.0008-minimum
                else:
                    u=(p-cfg['duty_factor'])/(1-cfg['duty_factor'])
                    safe=.0008+.018*math.sin(math.pi*u)**2
                    correction=max(0.,safe-minimum)
                if abs(correction)<1e-6: break
                target[1]+=correction
        world=self.skin.world(t,q,s)
        return t,q,s,{'time_s':float(time),'phase':float(phase%1.),
                     'contacts':{side:bool(p[3] or standing) for side,p in plans.items()},
                     'foot_fk_error_m':residual,
                     'minimum_skin_y_m':float(self.skin.skin(world)[:,1].min())}

    def sample(self,hz=60):
        if type(hz) is not int or hz<10 or hz>240:
            raise ContractError('sample rate must be an integer in [10,240]')
        times=np.linspace(0,self.cfg['cycle_s'],round(self.cfg['cycle_s']*hz)+1)
        poses=[];rows=[]
        for time in times:
            t,q,s,row=self.pose(float(time));poses.append((t,q,s));rows.append(row)
        t=np.array([p[0] for p in poses]);q=np.array([p[1] for p in poses]);s=np.array([p[2] for p in poses])
        q/=np.linalg.norm(q,axis=2,keepdims=True)
        for i in range(1,len(q)):
            mask=np.sum(q[i]*q[i-1],axis=1)<0;q[i,mask]*=-1
        return times,t,q,s,rows


def emit_glb(source, clips):
    """Append animation only: every original mesh/skin/texture accessor survives."""
    doc=deepcopy(source.document); binary=bytearray(source.binary);animations=[]
    for name,times,translations,rotations in clips:
        times=np.asarray(times,float);translations=np.asarray(translations,float);rotations=np.asarray(rotations,float)
        if len(times)<2 or not np.isfinite(times).all() or np.any(np.diff(times)<=0):
            raise ContractError('strictly increasing finite timeline required')
        if translations.shape!=(len(times),len(source.nodes),3) or rotations.shape!=(len(times),len(source.nodes),4):
            raise ContractError('trajectory shape mismatch')
        if not np.isfinite(translations).all() or not np.isfinite(rotations).all():
            raise ContractError('non-finite trajectory')
        if not np.allclose(np.linalg.norm(rotations,axis=2),1,atol=1e-6,rtol=0):
            raise ContractError('rotation quaternion is not unit length')
        time_index=_append_accessor(doc,binary,times[:,None],'SCALAR')
        samplers=[];channels=[]
        for node in range(len(source.nodes)):
            for path,values,kind in [('translation',translations[:,node],'VEC3'),('rotation',rotations[:,node],'VEC4')]:
                # Keep source parent/container nodes untouched unless animated.
                rest=np.asarray(source.rest_translation if path=='translation' else source.rest_rotation)[node]
                if np.max(np.abs(values-rest))<1e-10: continue
                out=_append_accessor(doc,binary,values,kind)
                channels.append({'sampler':len(samplers),'target':{'node':node,'path':path}})
                samplers.append({'input':time_index,'output':out,'interpolation':'LINEAR'})
        animations.append({'name':name,'samplers':samplers,'channels':channels})
    doc['animations']=animations
    raw=_encode(doc,binary)
    reopen=Glb(raw=raw)
    for key in ('meshes','skins','materials','textures','images','nodes'):
        if reopen.document.get(key)!=source.document.get(key):
            raise ContractError(f'animation-only emitter altered {key}')
    for i in range(len(source.document['accessors'])):
        if source.accessor_bytes(i)!=reopen.accessor_bytes(i):
            raise ContractError(f'animation-only emitter altered original accessor {i}')
    return raw
