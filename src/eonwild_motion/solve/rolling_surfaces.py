"""Behavior-owned rolling material contacts on the admitted skinned surface.

A material point is anchored during its support interval, not throughout the
whole stance. Acquisitions are frozen from the source sole's lower envelope.
No corrected trial can move an anchor or choose a more convenient witness.
"""
from dataclasses import dataclass
from bisect import bisect_right
import hashlib
import json
import math
import numpy as np
from scipy.optimize import brentq
from ..errors import ContractError


@dataclass(frozen=True)
class RollingContactEvent:
    phase_s: float
    patch_index: int
    anchor_m: tuple[float, float, float]


@dataclass(frozen=True)
class RollingContactPlan:
    cycle_s: float
    stance_s: float
    events: tuple[tuple[RollingContactEvent, ...], ...]
    end_offsets_m: tuple[tuple[float, float, float], ...]
    start_offsets_m: tuple[tuple[float, float, float], ...]
    binding_sha256: str

    def current_binding_sha256(self):
        payload = {'cycle_s': self.cycle_s, 'stance_s': self.stance_s,
            'events': [[{'phase_s':e.phase_s,'patch_index':e.patch_index,'anchor_m':e.anchor_m}
                        for e in group] for group in self.events],
            'start_offsets_m': self.start_offsets_m, 'end_offsets_m': self.end_offsets_m}
        return hashlib.sha256(json.dumps(payload, sort_keys=True,
            separators=(',', ':'), allow_nan=False).encode()).hexdigest()

    def event(self, side, phase):
        events = self.events[0 if side == 'left' else 1]
        index = max(0, bisect_right([e.phase_s for e in events], phase) - 1)
        return events[index]


def build_rolling_contact_plan(query, provider, skin):
    from .source_motion_query import SourceMotionUnavailable
    from .constant_skin_targets import _TARGET_GAP_M
    cycle = 2 * query._locomotion_gait.step_period_s
    stance = cycle * query._locomotion_gait.duty_factor
    up_i = int(np.argmax(abs(query.context.up)))
    groups, starts, ends = [], [], []
    for side, offset in (('left', 0.), ('right', cycle/2)):
        cache = {}
        def surface(phase):
            phase = float(phase)
            if phase not in cache:
                time = (offset + phase) % cycle
                if time < 1e-12 and offset + phase > 0: time = cycle
                result = query._evaluate_owned(time, side='left_limit' if phase == stance else 'value',
                    target_offsets={'left': [0.,0.,0.], 'right': [0.,0.,0.]})
                if isinstance(result, SourceMotionUnavailable): raise ContractError(result.reason)
                ids = np.asarray(provider.anchor_for(side).material_vertex_indices)
                cache[phase] = skin.skin(np.asarray(result.worlds), ids) - query.context.forward * result.row['feet'][side]['forward_m']
            return cache[phase]
        initial = surface(0.)
        index = int(np.argmin(initial[:, up_i]))
        anchor = initial[index].copy()
        anchor[up_i] = skin.ground + _TARGET_GAP_M + 1e-6
        events = [RollingContactEvent(0., index, tuple(anchor))]
        starts.append(tuple(anchor - initial[index]))
        previous = 0.
        for phase in np.linspace(0., stance, math.ceil(stance*120)+1)[1:]:
            current = surface(phase)
            incoming = int(np.argmin(current[:, up_i]))
            if incoming != index and current[incoming, up_i] < current[index, up_i] - 1e-10:
                def crossing(t):
                    points = surface(t)
                    return float(points[index, up_i] - points[incoming, up_i])
                a, b = crossing(previous), crossing(phase)
                event_phase = brentq(crossing, previous, phase, xtol=1e-10) if a*b < 0 else previous
                at_event = surface(event_phase)
                # The incoming point acquires the position it has when the
                # outgoing anchored point reaches the same support plane.
                correction = anchor - at_event[index]
                anchor = at_event[incoming] + correction
                anchor[up_i] = skin.ground + _TARGET_GAP_M + 1e-6
                index = incoming
                events.append(RollingContactEvent(float(event_phase), index, tuple(anchor)))
            previous = float(phase)
        ends.append(tuple(anchor - surface(stance)[index]))
        groups.append(tuple(events))
    payload = {'cycle_s': cycle, 'stance_s': stance,
        'events': [[{'phase_s':e.phase_s,'patch_index':e.patch_index,'anchor_m':e.anchor_m} for e in g] for g in groups],
        'start_offsets_m': starts, 'end_offsets_m': ends}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',',':')).encode()).hexdigest()
    return RollingContactPlan(cycle, stance, tuple(groups), tuple(ends), tuple(starts), digest)


def solve_rolling_surfaces(law, query, time_s, evaluation_side='value'):
    from .source_motion_query import SourceMotionUnavailable, _thaw
    from .constant_skin_targets import _TARGET_GAP_M
    from ..planning.grounded_gait import smooth
    plan, skin, ctx = law._rolling_contact_plan, law._skin, query.context
    sides = ('left', 'right'); up_i = int(np.argmax(abs(ctx.up)))
    zero = {side: [0.,0.,0.] for side in sides}
    raw = query._evaluate_owned(time_s, side=evaluation_side, target_offsets=zero, rolling_material_authority=True)
    if isinstance(raw, SourceMotionUnavailable): raise ContractError(raw.reason)
    row = _thaw(raw.row)
    targets, indices, offsets = {}, {}, {}
    for ordinal, side in enumerate(sides):
        foot = row['feet'][side]
        if foot['contact']:
            phase = float(row['time_s'] - foot['touchdown_time_s'])
            phase = min(plan.stance_s, max(0., phase))
            event = plan.event(side, phase)
            indices[side] = event.patch_index
            targets[side] = np.asarray(event.anchor_m) + ctx.forward * foot['forward_m']
            ids = np.asarray(law._provider.anchor_for(side).material_vertex_indices)
            point = skin.skin(np.asarray(raw.worlds), ids[[event.patch_index]])[0]
            offsets[side] = targets[side] - point
        else:
            blend = smooth(float(foot['swing_phase']))
            offsets[side] = (1-blend)*np.asarray(plan.end_offsets_m[ordinal]) + blend*np.asarray(plan.start_offsets_m[ordinal])
            indices[side] = plan.events[ordinal][-1].patch_index
            targets[side] = None
    for iteration in range(30):
        if max(np.linalg.norm(value) for value in offsets.values()) > .059 * ctx.body_height:
            raise ContractError('rolling material correction exceeds body-height envelope')
        result = query._evaluate_owned(time_s, side=evaluation_side, target_offsets={s:v.tolist() for s,v in offsets.items()}, rolling_material_authority=True)
        if isinstance(result, SourceMotionUnavailable): raise ContractError(result.reason)
        worlds = np.asarray(result.worlds); errors, gaps, points = {}, {}, {}
        for side in sides:
            ids = np.asarray(law._provider.anchor_for(side).material_vertex_indices)
            patch = skin.skin(worlds, ids)
            points[side] = patch[indices[side]]
            gaps[side] = float(patch[:,up_i].min() - skin.ground)
            error = np.zeros(3) if targets[side] is None else targets[side] - points[side]
            error += ctx.up * max(0., _TARGET_GAP_M+1e-6-gaps[side]-float(error@ctx.up))
            errors[side] = error
        if max(np.linalg.norm(e) for e in errors.values()) < 1e-9: break
        for side in sides: offsets[side] += errors[side]
    data = {}
    for side in sides:
        material_error = np.zeros(3) if targets[side] is None else targets[side] - points[side]
        data[side] = {'loaded':bool(row['feet'][side]['contact']),
            'required_correction_m': material_error if targets[side] is not None else errors[side],
            'loaded_material_max_residual_m':float(np.linalg.norm(material_error)),
            'gap_m':gaps[side], 'pose':result.pose, 'row':_thaw(result.row), 'correction_m':offsets[side],
            'material_witness_m':points[side].tolist(),
            'semantic_target_m':(points[side] if targets[side] is None else targets[side]).tolist()}
    return data
