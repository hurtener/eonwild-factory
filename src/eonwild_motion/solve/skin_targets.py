"""Skin-space contact refinement and cyclic final-artifact authority.

Contact offsets are inputs to a new constrained V9 solve, never post-export
bone edits. The declared floor and material witness identities do not move.
The engineering ground/penetration/skate thresholds are unchanged.
"""
from __future__ import annotations

from copy import deepcopy
import math
import numpy as np

from ..contact_gauge import _source_frames
from ..dynamics.contact_authority import PatchFrame, AuthorityThresholds, evaluate_contact_authority
from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _clip_state
from ..planning.grounded_gait import smooth

# These are the existing refinement target and stopping tolerance, not looser
# substitutes for the independent final contact-authority thresholds.
_TARGET_GAP_M = .0001
_REFINEMENT_TOLERANCE_M = .0002


def _numeric_array(value, *, label):
    try:
        array = np.asarray(value)
        if array.dtype.kind not in 'iuf':
            raise ValueError('expected real numbers, not coercible strings or booleans')
        array = array.astype(float, copy=False)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ContractError(f'{label} must contain finite real numbers') from exc
    if not np.isfinite(array).all():
        raise ContractError(f'{label} must contain finite real numbers')
    return array


def _points(value, *, label):
    array = _numeric_array(value, label=label)
    if array.ndim != 2 or array.shape[1] != 3 or len(array) == 0:
        raise ContractError(f'{label} requires a nonempty N by 3 material point array')
    return array


def _times(value, *, label):
    array = _numeric_array(value, label=label)
    if array.ndim != 1 or len(array) < 2 or np.any(np.diff(array) <= 0):
        raise ContractError(f'{label} must be a strictly increasing timeline')
    return array


def _contacts(value, count):
    array = np.asarray(value)
    if array.shape != (count,) or array.dtype.kind != 'b':
        raise ContractError('contact state must contain one boolean per sample')
    return array


def _ground(profile):
    ground = profile['geometry']['ground']
    if ground.get('up_axis') not in ('X', 'Y', 'Z'):
        raise ContractError('skin contact needs an explicit positive cardinal floor axis')
    level = _numeric_array(ground.get('level_m'), label='ground level')
    if level.ndim != 0:
        raise ContractError('ground level must be a finite scalar')
    return {'X': 0, 'Y': 1, 'Z': 2}[ground['up_axis']], float(level)


def skin_frames(glb, contact_profile):
    name = glb.document['animations'][0]['name']
    _, times = _clip_state(glb, name)
    return _source_frames(glb, contact_profile, animation_name=name, sample_times=list(map(float, times)))


def points(frame, side):
    return _points([p['point_m'] for region in ('sole_points', 'toe_points')
                    for p in frame['feet'][side][region]], label=f'{side} material patch')


def _validate_skin_samples(frames, plan):
    """Check correspondence before corrections or cyclic endpoint de-duplication.

    Each sole/toe region must keep its material-point ordering and count. This
    catches count changes; stable IDs/order themselves are supplied by the
    locked skin extractor, not inferred by matching nearby points here.
    """
    if len(frames) != len(plan['samples']):
        raise ContractError('skin and plan timelines differ')
    times = _times([f['time_s'] for f in frames], label='skin times')
    expected = _times([r['time_s'] for r in plan['samples']], label='plan times')
    # Same serialized float32-time allowance as evaluate_emitted. Equal counts
    # alone do not establish that a contact mask belongs to these poses.
    if not np.allclose(times, expected, rtol=0, atol=2e-6):
        raise ContractError('skin and plan timelines differ')
    masks = {side: _contacts([r['feet'][side]['contact'] for r in plan['samples']], len(frames))
             for side in ('left', 'right')}
    shapes = {}
    for frame in frames:
        root = _numeric_array(frame['root_m'], label='skin root')
        if root.shape != (3,):
            raise ContractError('skin root requires three coordinates')
        for side in masks:
            for region in ('sole_points', 'toe_points'):
                patch = _points([p['point_m'] for p in frame['feet'][side][region]], label=f'{side} {region}')
                key = side, region
                if key in shapes and shapes[key] != patch.shape:
                    raise ContractError('skin material point count changed across samples')
                shapes[key] = patch.shape
    return times, masks


def cyclic_authority(frames, loaded, displacement, thresholds):
    """Evaluate loaded phases crossing the seam with unwrapped root travel.

    Validate EVERY original sample, including the actual duplicate endpoint,
    before using unique samples. Otherwise NaN comparisons or broadcasting can
    conceal a bad final skin sample that is then absent from the three copies.
    """
    if len(frames) != len(loaded) or len(frames) < 3:
        raise ContractError('cyclic contact requires at least three aligned frames')
    times = _times([f.time_s for f in frames], label='cyclic contact times')
    mask = _contacts(loaded, len(frames))
    shift = _numeric_array(displacement, label='cyclic displacement')
    if shift.shape != (3,):
        raise ContractError('invalid cyclic contact displacement')
    patches = {}
    for key in ('sole_m', 'toe_m'):
        arrays = [_points(getattr(frame, key), label=f'cyclic {key}') for frame in frames]
        if any(array.shape != arrays[0].shape for array in arrays[1:]):
            raise ContractError('cyclic material point count changed across samples')
        patches[key] = arrays
    duration = float(times[-1] - times[0])
    seam = max(float(np.linalg.norm(arrays[-1] - arrays[0] - shift, axis=1).max())
               for arrays in patches.values())
    if mask[-1] != mask[0] or seam > .0005:
        return {'verdict': 'FAIL', 'maximum_skin_seam_error_m': seam,
                'reasons': ['cyclic contact state or serialized skin does not close'], 'phases': []}
    count = len(frames) - 1
    expanded, flags = [], []
    for cycle in (-1, 0, 1):
        for frame, load in zip(frames[:-1], mask[:-1]):
            expanded.append(PatchFrame(frame.time_s + cycle * duration,
                tuple(map(tuple, np.asarray(frame.sole_m) + cycle * shift)),
                tuple(map(tuple, np.asarray(frame.toe_m) + cycle * shift))))
            flags.append(bool(load))
    intervals = []
    start = None
    for i, load in enumerate(flags + [False]):
        if load and start is None:
            start = i
        elif not load and start is not None:
            if start < 2 * count and i > count:
                intervals.append((start, i))
            start = None
    results = [evaluate_contact_authority(expanded[a:b], [True] * (b - a), thresholds=thresholds)
               for a, b in intervals]
    if not results:
        return {'verdict': 'FAIL', 'maximum_skin_seam_error_m': seam,
                'reasons': ['no loaded contact phase'], 'phases': []}
    return {'verdict': 'PASS' if all(r['verdict'] == 'PASS' for r in results) else 'FAIL',
        'maximum_skin_seam_error_m': seam,
        'cyclic_context': 'loaded phases intersecting middle of three root-unwrapped cycles',
        'phases': [p for r in results for p in r['phases']],
        'reasons': [reason for r in results for reason in r.get('reasons', [])]}


def evaluate_skin(glb, profile, plan, *, world_offsets=None):
    frames, _ = skin_frames(glb, profile)
    _, masks = _validate_skin_samples(frames, plan)
    if world_offsets is not None:
        # Reconstruct the motor's world frame, never modify the GLB or floor.
        offsets = _numeric_array(world_offsets, label='in-place world offsets')
        if offsets.shape != (len(frames), 3):
            raise ContractError('in-place world reconstruction requires one finite offset per sample')
        frames = deepcopy(frames)
        for frame, offset in zip(frames, offsets):
            frame['root_m'] = (np.asarray(frame['root_m']) + offset).tolist()
            for foot in frame['feet'].values():
                for region in ('sole_points', 'toe_points'):
                    for point in foot[region]:
                        point['point_m'] = (np.asarray(point['point_m']) + offset).tolist()
    axis, ground = _ground(profile)
    thresholds = AuthorityThresholds(up_axis=axis, ground_m=ground)
    displacement = np.asarray(frames[-1]['root_m']) - frames[0]['root_m']
    per_foot = {}
    global_minimum = math.inf
    maximum_stance_gap = -math.inf
    for side in ('left', 'right'):
        patches = [PatchFrame(f['time_s'], tuple(tuple(p['point_m']) for p in f['feet'][side]['sole_points']),
                    tuple(tuple(p['point_m']) for p in f['feet'][side]['toe_points'])) for f in frames]
        loaded = masks[side].tolist()
        per_foot[side] = (cyclic_authority(patches, loaded, displacement, thresholds) if plan.get('loop', True)
                          else evaluate_contact_authority(patches, loaded, thresholds=thresholds))
        for f, load in zip(frames, loaded):
            gap = float(points(f, side)[:, axis].min() - ground)
            global_minimum = min(global_minimum, gap)
            if load:
                maximum_stance_gap = max(maximum_stance_gap, gap)
    penetration = max(0., -global_minimum)
    valid = all(r['verdict'] == 'PASS' for r in per_foot.values()) and penetration <= thresholds.penetration_tolerance_m
    return {'verdict': 'PASS' if valid else 'FAIL', 'authority': {'per_foot': per_foot},
        'maximum_penetration_m': penetration,
        'maximum_stance_gap_m': maximum_stance_gap if math.isfinite(maximum_stance_gap) else None,
        'ground_level_m': ground, 'sample_count': len(frames),
        'classification': 'final serialized skin, fixed floor, full multi-influence weights, unchanged engineering thresholds'}


def _cyclic_fill(times, values, loaded, *, loop=True):
    """Quintic interpolation of corrections through unloaded intervals.

    It does not assert C2 continuity of the entire emitted motion: derivatives
    at neighboring loaded samples and final serialized seams are audited apart.
    """
    times = _times(times, label='correction times')
    values = _points(values, label='correction vectors')
    if len(values) != len(times) or type(loop) is not bool:
        raise ContractError('correction vectors, times and loop declaration must align')
    mask = _contacts(loaded, len(times))
    result = values.copy()
    indices = np.flatnonzero(mask)
    if not len(indices):
        raise ContractError('refinement requires loaded samples')
    duration = times[-1] - times[0]
    for i in np.flatnonzero(~mask):
        before = indices[indices < i]
        after = indices[indices > i]
        if not loop and (not len(before) or not len(after)):
            result[i] = values[after[0] if len(after) else before[-1]]
            continue
        a, b = (before[-1] if len(before) else indices[-1]), (after[0] if len(after) else indices[0])
        ta = times[a] - (duration if not len(before) else 0)
        tb = times[b] + (duration if not len(after) else 0)
        gain = smooth((times[i] - ta) / max(1e-9, tb - ta))
        result[i] = (1 - gain) * values[a] + gain * values[b]
    return result


def solve_with_skin_targets(source, *, semantic_roles, gait, up_axis, forward_axis, plan, contact_profile, iterations=7, articulation_profile=None, canonical_support_anchor_provider=None, canonical_locomotion_gait=None, canonical_transition=None):
    from .airborne_gait import solve_airborne_gait
    if type(iterations) is not int or iterations < 0:
        raise ContractError('skin refinement iterations must be a non-negative integer')
    current = deepcopy(plan)
    up = _numeric_array(up_axis, label='refinement up axis')
    forward = _numeric_array(forward_axis, label='refinement forward axis')
    if up.shape != (3,) or forward.shape != (3,) or not np.isclose(np.linalg.norm(forward), 1., rtol=0, atol=1e-6):
        raise ContractError('skin refinement requires finite unit coordinate axes')
    index_up, ground = _ground(contact_profile)
    if not np.allclose(up, np.eye(3)[index_up], rtol=0, atol=1e-8) or abs(float(up @ forward)) > 1e-6:
        raise ContractError('skin refinement axes disagree with the fixed floor')
    height = _numeric_array(current['body_height_m'], label='body height')
    if height.ndim != 0 or height <= 0:
        raise ContractError('skin refinement requires a positive body height')
    samples = current['samples']
    _times([r['time_s'] for r in samples], label='refinement plan times')
    count = len(samples)
    masks = {side: _contacts([r['feet'][side]['contact'] for r in samples], count) for side in ('left', 'right')}
    if any(not mask.any() for mask in masks.values()):
        raise ContractError('skin refinement requires loaded samples for each foot')
    performance = current.get('performance', {})
    canonical_requested = isinstance(performance, dict) and performance.get('canonical_support_anchors') is True
    if canonical_requested and canonical_support_anchor_provider is None:
        raise ContractError('skin refinement canonical support anchors require a bound provider')
    if canonical_support_anchor_provider is not None:
        from .support_anchors import CanonicalSupportAnchorProvider
        if not canonical_requested or not isinstance(canonical_support_anchor_provider, CanonicalSupportAnchorProvider):
            raise ContractError('skin refinement canonical support anchors must be a bound provider')
        canonical_support_anchor_provider.validate_for_consumption(
            source, semantic_roles=semantic_roles, solver_gait=gait,
            locomotion_gait=canonical_locomotion_gait, transition=canonical_transition,
            plan=current, contact_profile=contact_profile, up_axis=tuple(up),
            forward_axis=tuple(forward), articulation_profile=articulation_profile)
    anchors = {}
    offsets = {side: np.zeros((count, 3)) for side in masks}
    trace = []
    for iteration in range(iterations + 1):
        for i, row in enumerate(samples):
            for side in offsets:
                row['feet'][side]['target_offset_m'] = offsets[side][i].tolist()
        root_raw, inplace_raw, _, receipt = solve_airborne_gait(source, source_clip=None,
            semantic_roles=semantic_roles, gait=gait, up_axis=tuple(up), forward_axis=tuple(forward),
            plan_override=current, legacy_overlay=False, articulation_profile=articulation_profile)
        frames, _ = skin_frames(Glb.from_bytes(root_raw), contact_profile)
        times, _ = _validate_skin_samples(frames, current)
        maximum_loaded_error = maximum_swing_error = 0.0
        corrections = {}
        for side in offsets:
            loaded = masks[side]
            if side not in anchors:
                if canonical_support_anchor_provider is None:
                    first = int(np.flatnonzero(loaded)[0])
                    patch = points(frames[first], side)
                    witness = int(patch[:, index_up].argmin())
                    origin = patch - forward * samples[first]['feet'][side]['forward_m']
                else:
                    anchor = canonical_support_anchor_provider.anchor_for(side)
                    witness = anchor.lowest_patch_index
                    origin = anchor.material_origin_m.copy()
                anchors[side] = (witness, origin)
            _, origin = anchors[side]
            correction = np.zeros_like(offsets[side])
            for i, (frame, row, load) in enumerate(zip(frames, samples, loaded)):
                patch = points(frame, side)
                gap = float(patch[:, index_up].min() - ground)
                if load:
                    target = origin + forward * row['feet'][side]['forward_m']
                    active = patch[:, index_up] <= patch[:, index_up].min() + .001
                    errors = target[active] - patch[active]
                    error = .5 * (errors.max(axis=0) + errors.min(axis=0))
                    error -= up * float(error @ up)
                    error += up * (_TARGET_GAP_M - gap)
                    correction[i] = error
                    maximum_loaded_error = max(maximum_loaded_error, float(np.linalg.norm(error)))
                else:
                    # Measure the CURRENT emitted swing, not an unapplied
                    # correction. Planted feet alone cannot end refinement.
                    maximum_swing_error = max(maximum_swing_error, max(0., _TARGET_GAP_M - gap))
            correction = _cyclic_fill(times, correction, loaded, loop=current.get('loop', True))
            for i, (frame, load) in enumerate(zip(frames, loaded)):
                if not load:
                    gap = float(points(frame, side)[:, index_up].min() - ground)
                    correction[i] += up * max(0., _TARGET_GAP_M - gap - float(correction[i] @ up))
            corrections[side] = correction
        converged = max(maximum_loaded_error, maximum_swing_error) <= _REFINEMENT_TOLERANCE_M
        trace.append({'iteration': iteration, 'maximum_loaded_target_error_m': maximum_loaded_error,
                      'maximum_swing_clearance_error_m': maximum_swing_error})
        if converged or iteration == iterations:
            # Return exactly the solve just measured, never offsets scheduled
            # for a nonexistent next iteration or a post-export projection.
            break
        for side in offsets:
            offsets[side] += .85 * corrections[side]
            if np.max(np.linalg.norm(offsets[side], axis=1)) > .06 * float(height):
                raise ContractError('skin-target refinement exceeded its body-normalized correction envelope')
            if current.get('loop', True):
                offsets[side][-1] = offsets[side][0]
    receipt['skin_target_refinement'] = {
        'classification': 'material-witness correction before repeated constrained IK, not post-export projection',
        'converged': converged, 'trace': trace, 'target_gap_m': _TARGET_GAP_M,
        'tolerance_m': _REFINEMENT_TOLERANCE_M,
        'convergence_components': {'loaded_targets': maximum_loaded_error <= _REFINEMENT_TOLERANCE_M,
                                   'swing_clearance': maximum_swing_error <= _REFINEMENT_TOLERANCE_M},
        'maximum_offset_m': max(float(np.max(np.linalg.norm(v, axis=1))) for v in offsets.values()),
        'witnesses': {side: {'initial_lowest_patch_index': int(value[0]), 'material_anchor_origins_m': value[1].tolist()}
                      for side, value in anchors.items()},
        'ground_level_m': ground}
    if canonical_support_anchor_provider is not None:
        receipt['skin_target_refinement']['anchor_selection'] = (
            canonical_support_anchor_provider.receipt())
    return root_raw, inplace_raw, current, receipt
