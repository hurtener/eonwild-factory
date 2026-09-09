"""Reusable V9 persistent-support performances and explicit oral contact.

Feet keep world-space support while the trunk, neck and jaw perform a typed
recipe. The five-mode oral projection is extracted from Feeding003, with
per-build state instead of monkey-patching historical scripts. Animation cues
never decide that prey was damaged, food yielded, or a gameplay grip succeeded.
"""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import math
import numpy as np

from ..errors import ContractError
from ..layers.leg_contact_resolve_v3 import _clip_state, _pose, _rotation_from_matrix, _qmul, _qinv
from ..planning.airborne_gait import AirborneGait
from ..planning.grounded_gait import smooth
from ..planning.supported_action import SupportedAction, curve, resample_chain
from ..planning.support_balance import support_balance
from .airborne_gait import _unit, _qrotate, _qrotvec, _between, _interior, stable_knee_geometry, _orientation_from_bend
from .performance import Performance, decorate_plan
from .skin_rig import SkinRig
from .skin_targets import solve_with_skin_targets
from .whole_body_gait_transition import _build_glb


def bounded_fit(residual, low, high, initial=None, iterations=65):
    """Small bounded Levenberg-Marquardt solve; radians, no random seed."""
    low, high = np.asarray(low), np.asarray(high)
    if (low > high).any():
        raise ContractError('empty oral articulation envelope')
    x = np.clip(np.zeros(len(low)) if initial is None else initial, low, high)
    damping = 1e-4
    for _ in range(iterations):
        r = residual(x)
        if not np.isfinite(r).all(): raise ContractError('non-finite oral residual')
        jac = np.empty((len(r), len(x)))
        eps = 1e-5
        for j in range(len(x)):
            xx = x.copy(); xx[j] += eps
            jac[:, j] = (residual(xx) - r) / eps
        step = np.linalg.solve(jac.T @ jac + np.eye(len(x)) * damping, -jac.T @ r)
        trial = np.clip(x + np.clip(step, -.18, .18), low, high)
        new = residual(trial)
        if float(new @ new) < float(r @ r):
            if np.linalg.norm(trial - x) < 1e-9:
                x = trial; break
            x = trial; damping = max(1e-8, damping * .5)
        else:
            damping = min(1e6, damping * 4)
    return x


def calibrate_support(source, roles, contact_profile, up, forward, height, width, support_reach=None):
    rig = SkinRig(source, roles, forward, up, contact_profile)
    pelvis = rig.neutral_world[rig.roles_i['pelvis'][0], :3, 3]
    feet = {}
    for side, chain in rig.legs.items():
        reach = (float((rig.neutral_world[chain[-1], :3, 3] - pelvis) @ forward) if support_reach is None
                 else float(support_reach[0 if side == 'left' else 1]) * height)
        feet[side] = {'contact': True, 'forward_m': reach, 'height_m': 0., 'toe_flex_degrees': 0.,
                      'foot_pitch_degrees': 0., 'swing_phase': 0., 'touchdown_time_s': 0.}
    samples = [{'time_s': t, 'root_forward_m': 0., 'pelvis_height_offset_m': -.025 * height,
                'stage': 'PLANTED_CALIBRATION', 'support_count': 2, 'flight': False,
                'feet': {side: dict(foot) for side, foot in feet.items()}} for t in (0., .5, 1.)]
    plan = {'schema': 'eonwild.motion.v9.contact-plan.v1', 'program': 'supported_action', 'loop': True,
            'body_height_m': height, 'same_foot_cycle_s': 1., 'duration_s': 1., 'samples': samples}
    plan = decorate_plan(plan, Performance(lane_width_body_heights=width, pelvis_sway_body_heights=0.,
        pelvis_yaw_degrees=0., pelvis_roll_degrees=0., tail_yaw_degrees=0., gaze_elevation_degrees=0.))
    raw, _, _, receipt = solve_with_skin_targets(source, semantic_roles=roles, gait=AirborneGait(cycles=1, sample_hz=24),
        up_axis=up, forward_axis=forward, plan=plan, contact_profile=contact_profile)
    from ..glb.container import Glb
    compiled = Glb.from_bytes(raw)
    tracks, _ = _clip_state(compiled, compiled.document['animations'][0]['name'])
    return tuple(np.asarray(a, dtype=float) for a in _pose(compiled, tracks, 0)), receipt


class SupportedSolver:
    """One private request context; no shared/cache mutation of source rigs."""
    def __init__(self, source, roles, action, contact_profile, up, forward, height):
        self.source, self.roles, self.action = source, roles, action
        self.up, self.forward = _unit(up), _unit(forward)
        self.lateral = _unit(np.cross(self.up, self.forward))
        self.height = float(height)
        self.rig = SkinRig(source, roles, self.forward, self.up, contact_profile, oral=True)
        (self.t0, self.r0, self.s0), self.calibration = calibrate_support(source, roles, contact_profile, self.up, self.forward, height, action.lane_width_body_heights, action.support_reach_body_heights)
        self.w0 = self.rig.world(self.t0, self.r0, self.s0)
        surface = self.rig.skin(self.w0)
        # Explicit family calibration, independent of which contact vertices
        # happen to be in the current skin masks.
        self.length = height * action.translation_scale_body_heights[0]
        self.width = height * action.translation_scale_body_heights[2]
        self.pitch_axes = {n: _unit(np.linalg.solve(self.w0[n,:3,:3], self.lateral)) for nodes in self.rig.roles_i.values() for n in nodes}
        self.yaw_axes = {n: _unit(np.linalg.solve(self.w0[n,:3,:3], self.up)) for nodes in self.rig.roles_i.values() for n in nodes}
        self.angles = {role: resample_chain(action.base_pitch_degrees[role], len(nodes)) for role, nodes in self.rig.roles_i.items() if role in action.base_pitch_degrees}
        self.body_bounds = {}
        for role, rows in action.joint_pitch_limits_degrees.items():
            count = len(self.rig.roles_i[role]); array = np.asarray(rows)
            lower, upper = resample_chain(array[:,0], count), resample_chain(array[:,1], count)
            self.body_bounds.update({n: (low, high) for n, low, high in zip(self.rig.roles_i[role], lower, upper)})
        neck = self.rig.roles_i['neck']; split = max(1, int(math.ceil(len(neck) * .6)))
        self.groups = [self.rig.roles_i['spine'], self.rig.roles_i['chest'] + neck[:split], neck[split:] + self.rig.roles_i['head']]
        if any(not group for group in self.groups): raise ContractError('oral solver needs nonempty trunk and cervical modes')
        self.contact_nodes = {side: np.asarray(chain) for side, chain in self.rig.legs.items()}
        self.anchor_target = None
        self.release_values = None
        if action.anchor:
            t, r, s, state = self.free_pose(action.anchor.capture)
            offset = np.asarray(action.anchor.offset_body_heights)
            self.anchor_target = self.rig.centroid(self.rig.world(t,r,s), 'upper') + height * (offset[0]*self.forward + offset[1]*self.up + offset[2]*self.lateral)

    def free_pose(self, phase):
        a = self.action
        state = {key: curve(phase, keys) for key, keys in a.channels.items()}
        t, r, s = self.t0.copy(), self.r0.copy(), self.s0.copy()
        pelvis = self.rig.roles_i['pelvis'][0]
        shift = self.forward * state['forward'] * self.length + self.lateral * state['lateral'] * self.width - self.up * state['drop'] * self.height * a.translation_scale_body_heights[1]
        parent = self.rig.parents[pelvis]
        basis = np.eye(3) if parent is None else self.w0[parent,:3,:3]
        t[pelvis] += np.linalg.solve(basis, shift)
        for role, values in self.angles.items():
            amount = state['tail'] if role == 'tail' else state['body']
            for n, degrees in zip(self.rig.roles_i[role], values):
                r[n] = _qmul(r[n], _qrotvec(self.pitch_axes[n] * math.radians(degrees * amount)))
                yaw = state['yaw'] * a.yaw_weights.get(role,0.) / len(values)
                r[n] = _qmul(r[n], _qrotvec(self.yaw_axes[n] * math.radians(yaw)))
        # Coordinate body height BEFORE fixing the oral target and solving the
        # planted limbs. A braced pull must bend/support the body, not stretch
        # its rear leg or repeatedly drag a skin target beyond reach.
        world = self.rig.world(t,r,s)
        chains = list(self.rig.legs.values())
        hips = np.asarray([world[chain[0],:3,3] for chain in chains])
        anchors = np.asarray([self.w0[chain[2],:3,3] for chain in chains])
        lengths = np.asarray([[np.linalg.norm(self.w0[chain[1],:3,3]-self.w0[chain[0],:3,3]),
                               np.linalg.norm(self.w0[chain[2],:3,3]-self.w0[chain[1],:3,3])] for chain in chains])
        accommodation, balance = support_balance(hips, anchors, lengths, up_axis=self.up,
            knee_max_degrees=a.support_limits['knee_interior_degrees'][1],
            maximum_drop_m=.10*self.height, activation_band_m=.008*self.height)
        t[pelvis] += np.linalg.solve(basis, accommodation)
        state['support_balance'] = balance
        jaw = self.rig.roles_i['jaw_lower'][0]
        opening = state['jaw'] * a.gape_degrees
        def jaw_pose(degrees):
            rr = r.copy(); rr[jaw] = _qmul(self.r0[jaw], _qrotvec(self.pitch_axes[jaw] * math.radians(degrees)))
            w = self.rig.world(t,rr,s)
            minimum = float((self.rig.skin(w,self.rig.lower_jaw_indices) @ self.up).min() - self.rig.ground)
            return rr, minimum
        r, gap = jaw_pose(opening)
        if gap < .002 * self.height:
            closed, closed_gap = jaw_pose(0.)
            if closed_gap < 0:
                raise ContractError('supported body pose drives the closed jaw through the fixed ground')
            lo, hi = 0., opening
            for _ in range(14):
                mid = (lo+hi)/2; trial, trial_gap = jaw_pose(mid)
                if trial_gap >= .002*self.height: lo = mid
                else: hi = mid
            opening = lo; r, gap = jaw_pose(opening)
        state['actual_jaw_degrees'] = opening
        state['jaw_ground_gap_m'] = gap
        return t,r,s,state

    def corrected_rotations(self, rotations, degrees):
        r = rotations.copy()
        for group, value in zip(self.groups, degrees[:3]):
            for n in group:
                r[n] = _qmul(r[n], _qrotvec(self.pitch_axes[n] * math.radians(value)))
        for role, value in zip(('neck','head'), degrees[3:]):
            for n in self.rig.roles_i[role]:
                r[n] = _qmul(r[n], _qrotvec(self.yaw_axes[n] * math.radians(value / len(self.rig.roles_i[role]))))
        return r

    def project_mouth(self,t,r,s,target,state):
        preferred = {n: value*state['body'] for role, values in self.angles.items() if role!='tail' for n,value in zip(self.rig.roles_i[role],values)}
        low = [max(self.body_bounds[n][0]-preferred[n]+.001 for n in g) for g in self.groups] + [-12.,-12.]
        high = [min(self.body_bounds[n][1]-preferred[n]-.001 for n in g) for g in self.groups] + [12.,12.]
        cervical = self.rig.roles_i['chest'] + self.rig.roles_i['neck'] + self.rig.roles_i['head']
        def residual(x):
            degrees = np.degrees(x)
            rr = self.corrected_rotations(r,degrees)
            mouth = self.rig.centroid(self.rig.world(t,rr,s),'upper')
            curve_angles = [preferred[n]+degrees[1 if n in self.groups[1] else 2] for n in cervical]
            kink = np.maximum(np.abs(np.diff(curve_angles))-9.5,0.)
            return np.r_[(mouth-target)/self.action.anchor.tolerance_m, .003*degrees, 10*kink]
        fit = bounded_fit(residual,np.radians(low),np.radians(high))
        return np.degrees(fit)

    def support_pose(self,t,r,s):
        maximum_extension = maximum_error = violation = 0.
        facts = {}
        for side, (hip,knee,ankle,foot) in self.rig.legs.items():
            target = self.w0[ankle,:3,3].copy()
            ids = self.rig.foot_masks[side]
            original = self.rig.skin(self.w0,ids)
            witness = int(np.argmin(original @ self.up))
            desired_surface = original[witness]
            for _ in range(5):
                w = self.rig.world(t,r,s)
                hp,kp,ap = (w[n,:3,3] for n in (hip,knee,ankle))
                normal = _unit(np.cross(self.w0[knee,:3,3]-self.w0[hip,:3,3], self.w0[ankle,:3,3]-self.w0[knee,:3,3]))
                pk,pa,extension = stable_knee_geometry(hp,target,np.linalg.norm(kp-hp),np.linalg.norm(ap-kp),normal)
                current_normal = _unit(np.cross(kp-hp,ap-kp)); next_normal = _unit(np.cross(pk-hp,pa-pk))
                q = _qmul(_orientation_from_bend(kp-hp,current_normal,pk-hp,next_normal),_rotation_from_matrix(w[hip]))
                parent = self.rig.parents[hip]
                r[hip] = _qmul(_qinv(_rotation_from_matrix(w[parent])),q)
                w = self.rig.world(t,r,s);kp,ap=w[knee,:3,3],w[ankle,:3,3]
                q = _qmul(_between(ap-kp,pa-kp),_rotation_from_matrix(w[knee]))
                r[knee] = _qmul(_qinv(_rotation_from_matrix(w[hip])),q)
                w = self.rig.world(t,r,s)
                r[ankle] = _qmul(_qinv(_rotation_from_matrix(w[knee])),_rotation_from_matrix(self.w0[ankle]))
                w = self.rig.world(t,r,s)
                actual = self.rig.skin(w,ids)
                error = desired_surface - actual[witness]
                error -= self.up * float(error@self.up)
                error += self.up * (.0001 - float((actual@self.up).min()-self.rig.ground))
                if np.linalg.norm(error)<.00005: break
                target += error
                if np.linalg.norm(target-self.w0[ankle,:3,3])>.06*self.height:
                    raise ContractError('supported material correction exceeds the family envelope')
            hp,kp,ap,fp = (w[n,:3,3] for n in (hip,knee,ankle,foot))
            angles = {'hip_sagittal_degrees': math.degrees(math.atan2(float((kp-hp)@self.forward),-float((kp-hp)@self.up))),
                'knee_interior_degrees':_interior(hp-kp,ap-kp),'ankle_interior_degrees':_interior(kp-ap,fp-ap)}
            for key,value in angles.items():
                low,high=self.action.support_limits[key];violation=max(violation,low-value,value-high)
            maximum_extension=max(maximum_extension,float(extension))
            maximum_error=max(maximum_error,float(np.linalg.norm(ap-target)))
            facts[side]={**angles,'surface_error_m':float(np.linalg.norm(error))}
        return r, {'max_foot_target_residual_m':maximum_error,'max_unreachable_extension_m':maximum_extension,
                   'maximum_articulation_envelope_violation_degrees':max(0.,violation),'legs':facts}

    def pose(self, phase):
        t,r,s,state = self.free_pose(phase)
        correction = np.zeros(5)
        anchor = self.action.anchor
        if anchor and anchor.enter < phase < anchor.release:
            if phase <= anchor.resisted_end:
                gain=smooth((phase-anchor.enter)/(anchor.capture-anchor.enter))
                free=self.rig.centroid(self.rig.world(t,r,s),'upper')
                target=(1-gain)*free+gain*self.anchor_target
                correction=self.project_mouth(t,r,s,target,state)
            else:
                if self.release_values is None:
                    results=[];h=.001
                    for at in (anchor.resisted_end-h,anchor.resisted_end):
                        tt,rr,ss,st=self.free_pose(at)
                        results.append(self.project_mouth(tt,rr,ss,self.anchor_target,st))
                    self.release_values=(results[1],(results[1]-results[0])/h)
                value,velocity=self.release_values
                duration=anchor.release-anchor.resisted_end;u=(phase-anchor.resisted_end)/duration
                correction=(1-smooth(u))*value+duration*(u-6*u**3+8*u**4-3*u**5)*velocity
            r=self.corrected_rotations(r,correction)
        r,facts=self.support_pose(t,r,s)
        state['correction_degrees']=correction.tolist()
        state['oral_constraint_active']=bool(anchor and anchor.capture<=phase<=anchor.resisted_end)
        return t,r,s,state,facts


def solve_supported_action(source, *, semantic_roles, action, contact_profile, up_axis, forward_axis, body_height_m):
    solver=SupportedSolver(source,semantic_roles,action,contact_profile,up_axis,forward_axis,body_height_m)
    count=int(math.ceil(action.duration_seconds*action.sample_hz))
    times=np.linspace(0,action.duration_seconds,count+1)
    translations=[];rotations=[];states=[];maximums={key:0. for key in ('max_foot_target_residual_m','max_unreachable_extension_m','maximum_articulation_envelope_violation_degrees')}
    rows=[]
    for time in times:
        phase=time*action.reference_duration_seconds/action.duration_seconds
        t,r,s,state,facts=solver.pose(phase)
        if rotations:
            flip=np.sum(rotations[-1]*r,axis=1)<0;r[flip]*=-1
        translations.append(t);rotations.append(r);states.append(state)
        for key in maximums: maximums[key]=max(maximums[key],facts[key])
        stage=('ORAL_ANCHOR' if state['oral_constraint_active'] else 'SUPPORTED_PERFORMANCE')
        rows.append({'time_s':float(time),'root_forward_m':0.,'pelvis_height_offset_m':0.,'stage':stage,'flight':False,'support_count':2,
            'feet':{side:{'contact':True,'forward_m':0.,'height_m':0.,'toe_flex_degrees':0.,'foot_pitch_degrees':0.,'swing_phase':0.,'touchdown_time_s':0.} for side in ('left','right')},
            'performance_state':state})
    plan={'schema':'eonwild.motion.v9.contact-plan.v1','program':'supported_action','loop':action.loop,'body_height_m':body_height_m,
        'duration_s':action.duration_seconds,'same_foot_cycle_s':action.duration_seconds,'samples':rows,
        'events':[{'time_s':event['reference_time_seconds']*action.duration_seconds/action.reference_duration_seconds,
                   'name':event['name'],'kind':'animation_cue','authoritative_world_fact':False} for event in action.events],
        'oral_anchor_m':solver.anchor_target.tolist() if solver.anchor_target is not None else None,
        'oral_calibration':solver.rig.mouth_calibration(),'classification':'authored V9 supported performance with geometric constraints; no force simulation'}
    ft,fr=np.asarray(translations),np.asarray(rotations)
    channels={(n,'rotation'):fr[:,n] for n in range(len(source.nodes))}
    for n in [source.name_to_node[semantic_roles['root']],source.name_to_node[semantic_roles['pelvis']]]:channels[(n,'translation')]=ft[:,n]
    raw=_build_glb(source,'supported_action',times,channels,hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest(),{'program':'supported_action'})
    from ..glb.container import Glb
    final=Glb.from_bytes(raw);tracks,_=_clip_state(final,'supported_action')
    errors=[];jaw_gap=math.inf
    for i,row in enumerate(rows):
        w=solver.rig.world(*_pose(final,tracks,i))
        if row['performance_state']['oral_constraint_active']:
            errors.append(float(np.linalg.norm(solver.rig.centroid(w,'upper')-solver.anchor_target)))
        jaw_gap=min(jaw_gap,float((solver.rig.skin(w,solver.rig.lower_jaw_indices)@solver.up).min()-solver.rig.ground))
    oral={'status':'PASS' if (not action.anchor or (errors and max(errors)<=action.anchor.tolerance_m)) and jaw_gap>=-.0005 else 'FAIL',
          'maximum_anchor_error_m':max(errors) if errors else None,'anchor_samples':len(errors),'minimum_jaw_ground_gap_m':jaw_gap,
          'classification':'reopened skinned rostral-surface centroid; not a bone origin or simulated force'}
    receipt={**maximums,'oral_contact':oral,'support_calibration':solver.calibration,'classification':'V9 supported-action constraints, no independent visual approval'}
    return raw,raw,plan,receipt
