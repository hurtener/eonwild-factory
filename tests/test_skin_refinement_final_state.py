"""Small deterministic witnesses for refinement and final-skin correspondence.

The mocked limb emitter isolates the refinement controller. It is not a real
skinned-species or visual-quality proof; those remain separate acceptance jobs.
"""
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from eonwild_motion.dynamics.contact_authority import AuthorityThresholds, PatchFrame
from eonwild_motion.errors import ContractError
from eonwild_motion.solve import skin_targets as subject


def plan():
    rows = []
    for i, time in enumerate(np.linspace(0., 1., 5)):
        left_loaded = i in (0, 3, 4)
        rows.append({'time_s': float(time), 'root_forward_m': 0., 'pelvis_height_offset_m': 0.,
            'support_count': 1 + int(left_loaded), 'flight': False,
            'feet': {side: {'contact': left_loaded if side == 'left' else True,
                'forward_m': 0., 'height_m': 0., 'toe_flex_degrees': 0.,
                'foot_pitch_degrees': 0., 'swing_phase': 0.}
                for side in ('left', 'right')}})
    return {'loop': True, 'body_height_m': 1., 'duration_s': 1.,
            'same_foot_cycle_s': 1., 'program': 'grounded_gait', 'samples': rows}


def profile():
    return {'geometry': {'ground': {'up_axis': 'Y', 'level_m': 0.}}}


def material_frames(program, *, stance_gap=.0001, swing_gap=-.006, responsive=True):
    frames = []
    for row in program['samples']:
        feet = {}
        for side, lane in (('left', -.15), ('right', .15)):
            foot = row['feet'][side]
            gap = stance_gap if foot['contact'] else swing_gap
            offset = np.asarray(foot.get('target_offset_m', [0., 0., 0.])) if responsive else np.zeros(3)
            patch = [{'point_m': (np.array([lane + dx, gap, dz]) + offset).tolist()}
                     for dx, dz in ((0., 0.), (.03, 0.), (0., .04))]
            feet[side] = {'sole_points': deepcopy(patch), 'toe_points': deepcopy(patch)}
        frames.append({'time_s': row['time_s'], 'root_m': [0., 0., 0.], 'feet': feet})
    return frames


def fake_emitter(monkeypatch, **frame_options):
    calls = []

    def emit(source, **kwargs):
        calls.append(deepcopy(kwargs['plan_override']))
        n = len(calls) - 1
        return f'root:{n}'.encode(), f'inplace:{n}'.encode(), calls[-1], {}

    monkeypatch.setattr('eonwild_motion.solve.airborne_gait.solve_airborne_gait', emit)
    # Keep this mock local to the controller module, not Glb's class globally.
    monkeypatch.setattr(subject, 'Glb', SimpleNamespace(from_bytes=lambda raw: raw))
    monkeypatch.setattr(subject, 'skin_frames', lambda *args: (material_frames(calls[-1], **frame_options), {}))
    return calls


def refine(program, contact=None, **kwargs):
    return subject.solve_with_skin_targets(object(), semantic_roles={}, gait=None,
        up_axis=[0., 1., 0.], forward_axis=[0., 0., 1.], plan=program,
        contact_profile=profile() if contact is None else contact, **kwargs)


def test_good_stance_cannot_skip_a_needed_swing_correction(monkeypatch):
    calls = fake_emitter(monkeypatch)
    program, contact = plan(), profile()
    before_program, before_contact = deepcopy(program), deepcopy(contact)
    root, inplace, solved, receipt = refine(program, contact)
    evidence = receipt['skin_target_refinement']
    assert len(calls) > 1
    assert evidence['trace'][0]['maximum_loaded_target_error_m'] == pytest.approx(0.)
    assert evidence['trace'][0]['maximum_swing_clearance_error_m'] == pytest.approx(.0061)
    assert evidence['converged'] is True
    assert evidence['convergence_components'] == {'loaded_targets': True, 'swing_clearance': True}
    assert evidence['trace'][-1]['maximum_swing_clearance_error_m'] <= .0002
    assert root == f'root:{len(calls) - 1}'.encode()
    assert inplace == f'inplace:{len(calls) - 1}'.encode()
    assert solved == calls[-1]  # Return the offsets actually passed to the last solve.
    assert program == before_program and contact == before_contact
    frames = material_frames(solved)
    assert min(subject.points(f, 'left')[:, 1].min() for f in frames) >= -.0005
    assert calls[0]['samples'][1]['feet']['left']['target_offset_m'] == [0., 0., 0.]
    assert solved['samples'][1]['feet']['left']['target_offset_m'][1] > 0.


def test_iteration_limit_does_not_claim_an_unapplied_clearance_fix(monkeypatch):
    calls = fake_emitter(monkeypatch)
    root, _, solved, receipt = refine(plan(), iterations=0)
    assert len(calls) == 1 and root == b'root:0'
    assert solved == calls[0]
    assert receipt['skin_target_refinement']['converged'] is False
    assert receipt['skin_target_refinement']['convergence_components']['swing_clearance'] is False
    assert receipt['skin_target_refinement']['maximum_offset_m'] == 0.


def test_exhausted_nonresponsive_solver_returns_last_measured_state(monkeypatch):
    calls = fake_emitter(monkeypatch, responsive=False)
    root, _, solved, receipt = refine(plan(), iterations=1)
    assert len(calls) == 2 and root == b'root:1'
    assert solved == calls[-1]
    assert receipt['skin_target_refinement']['converged'] is False
    assert receipt['skin_target_refinement']['trace'][-1]['maximum_swing_clearance_error_m'] == pytest.approx(.0061)


def test_clear_swing_does_not_force_unnecessary_solves(monkeypatch):
    calls = fake_emitter(monkeypatch, swing_gap=.02)
    _, _, _, receipt = refine(plan())
    assert len(calls) == 1
    assert receipt['skin_target_refinement']['converged'] is True
    assert receipt['skin_target_refinement']['trace'][0]['maximum_swing_clearance_error_m'] == 0.


def test_hover_is_corrected_at_limb_targets_not_by_moving_floor(monkeypatch):
    fake_emitter(monkeypatch, stance_gap=.008, swing_gap=.02)
    contact = profile()
    _, _, solved, receipt = refine(plan(), contact)
    assert contact == profile()
    assert receipt['skin_target_refinement']['converged'] is True
    assert solved['samples'][0]['feet']['left']['target_offset_m'][1] < 0.
    frames = material_frames(solved, stance_gap=.008, swing_gap=.02)
    gap = subject.points(frames[0], 'left')[:, 1].min()
    assert abs(gap - .0001) <= .0002


@pytest.mark.parametrize('iterations', [-1, True, 1.5])
def test_invalid_iteration_limits_fail_before_emission(monkeypatch, iterations):
    calls = fake_emitter(monkeypatch)
    with pytest.raises(ContractError):
        refine(plan(), iterations=iterations)
    assert calls == []


def test_refinement_rejects_disagreement_with_declared_floor_axis(monkeypatch):
    calls = fake_emitter(monkeypatch)
    contact = profile()
    contact['geometry']['ground']['up_axis'] = 'Z'
    with pytest.raises(ContractError, match='axes disagree'):
        refine(plan(), contact)
    assert calls == []


def test_refinement_rejects_a_foot_without_any_loaded_sample(monkeypatch):
    calls = fake_emitter(monkeypatch)
    program = plan()
    for row in program['samples']:
        row['feet']['left']['contact'] = False
    with pytest.raises(ContractError, match='loaded samples'):
        refine(program)
    assert calls == []


def test_same_sample_count_does_not_establish_timeline_correspondence(monkeypatch):
    program = plan()
    frames = material_frames(program, swing_gap=.02)
    frames[1]['time_s'] += .01
    monkeypatch.setattr(subject, 'skin_frames', lambda *args: (frames, {}))
    with pytest.raises(ContractError, match='timelines differ'):
        subject.evaluate_skin(None, profile(), program)


def test_integer_contact_masks_are_not_boolean_contact_evidence(monkeypatch):
    program = plan()
    frames = material_frames(program, swing_gap=.02)
    program['samples'][0]['feet']['left']['contact'] = 1
    monkeypatch.setattr(subject, 'skin_frames', lambda *args: (frames, {}))
    with pytest.raises(ContractError, match='boolean'):
        subject.evaluate_skin(None, profile(), program)


def wrapped_patches():
    # A stance across the seam stays at x=1 in cycle zero and x=0 in the
    # preceding cycle. The duplicate endpoint includes the full root travel.
    result = []
    for time, x in zip(np.linspace(0., 1., 5), (0., 0., .5, 1., 1.)):
        patch = ((x, 0., 0.), (x + .03, 0., 0.), (x, 0., .04))
        result.append(PatchFrame(float(time), patch, patch))
    return result


def test_valid_wrap_retains_complete_grounded_phases_and_original_frames():
    frames = wrapped_patches()
    before = deepcopy(frames)
    result = subject.cyclic_authority(frames, [True, True, False, True, True], [1., 0., 0.], AuthorityThresholds())
    assert result['verdict'] == 'PASS'
    assert len(result['phases']) == 2
    assert result['maximum_skin_seam_error_m'] < 1e-12
    assert frames == before


@pytest.mark.parametrize('bad', [float('nan'), float('inf'), -float('inf')])
def test_invalid_actual_duplicate_endpoint_cannot_be_omitted(bad):
    frames = wrapped_patches()
    patch = list(frames[-1].sole_m)
    patch[0] = (bad, 0., 0.)
    frames[-1] = replace(frames[-1], sole_m=tuple(patch))
    with pytest.raises(ContractError, match='finite real'):
        subject.cyclic_authority(frames, [True, True, False, True, True], [1., 0., 0.], AuthorityThresholds())


def test_duplicate_endpoint_cannot_broadcast_one_vertex_over_a_patch():
    frames = wrapped_patches()
    frames[-1] = replace(frames[-1], sole_m=frames[-1].sole_m[:1])
    with pytest.raises(ContractError, match='point count changed'):
        subject.cyclic_authority(frames, [True, True, False, True, True], [1., 0., 0.], AuthorityThresholds())


def test_seam_pose_or_contact_error_remains_a_failure():
    frames = wrapped_patches()
    for loaded, displacement in (([True, True, False, True, False], [1., 0., 0.]),
                                 ([True, True, False, True, True], [0., 0., 0.])):
        result = subject.cyclic_authority(frames, loaded, displacement, AuthorityThresholds())
        assert result['verdict'] == 'FAIL'


@pytest.mark.parametrize('bad_time', [float('nan'), .75, -.1])
def test_nonfinite_or_unordered_terminal_time_is_rejected(bad_time):
    frames = wrapped_patches()
    frames[-1] = replace(frames[-1], time_s=bad_time)
    with pytest.raises(ContractError):
        subject.cyclic_authority(frames, [True, True, False, True, True], [1., 0., 0.], AuthorityThresholds())


def test_invalid_final_skin_sample_is_rejected_even_for_nonloop(monkeypatch):
    program = plan()
    program['loop'] = False
    frames = material_frames(program, swing_gap=.02)
    frames[-1]['feet']['right']['toe_points'][0]['point_m'][1] = float('nan')
    monkeypatch.setattr(subject, 'skin_frames', lambda *args: (frames, {}))
    with pytest.raises(ContractError, match='finite real'):
        subject.evaluate_skin(None, profile(), program)
