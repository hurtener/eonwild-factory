"""Evaluate connected choreography on the admitted rig and final skinned soles.

Material acquisitions are frozen before applying body response. This diagnostic
sequence shares leg IK, toe articulation and body controls with the walk.
"""
from copy import deepcopy
import numpy as np
from .airborne_gait import solve_airborne_plan_sample
from ..layers.leg_contact_resolve_v3 import _world_matrices


class SequenceEvaluator:
    def __init__(self, query, sequence, skin, provider, control):
        self.query, self.sequence, self.skin = query, sequence, skin
        self.context, self.control = query.context, control
        self.ids = {s: np.asarray(provider.anchor_for(s).material_vertex_indices) for s in ('left','right')}
        self.up_i = int(np.argmax(abs(self.context.up)))

    def evaluate(self, time, offsets=None, controlled=True):
        row = self.sequence.sample(float(time))
        for side, foot in row['feet'].items():
            foot['distal_endpoint_role'] = 'shape_preference'
            if offsets is not None: foot['target_offset_m'] = list(offsets[side])
        body = self.query._continuous_body_response(row) if self.query._body_response is not None else {'sagittal_node_degrees':{}}
        body = deepcopy(body)
        if controlled:
            delta = self.control.delta(row['locomotion_time_s'])
            gain = row.get('performance_gain', 1.)
            body['body_support_control'] = {
                'policy_id': self.control.policy_id, 'binding_sha256': self.control.binding_sha256,
                'translation_forward_up_lateral_m': (np.asarray(delta.translation_m)*gain).tolist(),
                'rotation_pitch_roll_yaw_radians': (np.asarray(delta.rotation_radians)*gain).tolist()}
        pose = solve_airborne_plan_sample(self.context, row, body_response_sample=body)
        worlds = np.asarray(_world_matrices(self.query._source, pose.translations, pose.rotations, self.context.base_s))
        patches = {s:self.skin.skin(worlds, ids) for s,ids in self.ids.items()}
        return row, pose, patches

    def emit_samples(self, times):
        # Freeze source-owned rolling acquisitions over each actual stance.
        raw = [self.evaluate(t, controlled=False) for t in times]
        floor = self.skin.ground + .000101
        targets = {s:[None]*len(times) for s in self.ids}
        indices = {s:[] for s in self.ids}
        corrections = {s:[] for s in self.ids}
        for side in self.ids:
            previous_loaded = False
            anchor = None
            old_index = None
            for i, (row, _, patches) in enumerate(raw):
                patch = patches[side]
                index = int(np.argmin(patch[:,self.up_i]))
                loaded = row['feet'][side]['contact']
                if loaded:
                    if not previous_loaded:
                        anchor = patch[index].copy(); anchor[self.up_i] = floor
                    elif index != old_index:
                        anchor = patch[index] + anchor - patch[old_index]
                        anchor[self.up_i] = floor
                    targets[side][i] = anchor.copy()
                    correction = anchor - patch[index]
                else:
                    correction = np.zeros(3)
                indices[side].append(index); corrections[side].append(correction)
                previous_loaded, old_index = loaded, index
            # Transport the endpoint offsets through swing with a C2 envelope.
            for i, (row, _, _) in enumerate(raw):
                if targets[side][i] is not None: continue
                a=i-1
                while a >= 0 and targets[side][a] is None: a-=1
                b=i+1
                while b < len(times) and targets[side][b] is None: b+=1
                if a >= 0 and b < len(times):
                    from ..planning.grounded_gait import smooth
                    u=smooth(row['feet'][side]['swing_phase'])
                    corrections[side][i]=(1-u)*corrections[side][a]+u*corrections[side][b]
        del raw
        for i,time in enumerate(times):
            offsets={s:corrections[s][i].copy() for s in self.ids}
            for iteration in range(20):
                row, pose, patches = self.evaluate(time, offsets)
                errors={}
                for s,patch in patches.items():
                    target=targets[s][i]
                    error=np.zeros(3) if target is None else target-patch[indices[s][i]]
                    error += self.context.up*max(0.,floor-patch[:,self.up_i].min()-error@self.context.up)
                    errors[s]=error
                if max(np.linalg.norm(e) for e in errors.values()) < 1e-7: break
                for s in self.ids: offsets[s]+=errors[s]
            yield row,pose,{s:{'loaded':targets[s][i] is not None,
                'gap_m':float(patches[s][:,self.up_i].min()-self.skin.ground),
                'residual_m':0. if targets[s][i] is None else float(np.linalg.norm(targets[s][i]-patches[s][indices[s][i]])),
                'vertex_index':int(self.ids[s][indices[s][i]]),
                'anchor_m':None if targets[s][i] is None else targets[s][i].tolist()} for s in self.ids}
