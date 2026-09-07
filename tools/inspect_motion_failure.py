"""Read-only native-pose diagnosis of a rejected compilation.

An interrupted solve is retained as diagnostic evidence, never as an accepted
factory package. This observer does not change constraints, plans or assets.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import traceback
import numpy as np
from eonwild_motion.factory.compiler import compile_recipe, verify_package
from eonwild_motion.glb.container import Glb
from eonwild_motion.layers.leg_contact_resolve_v3 import _clip_state, _pose, _world_matrices, _world_position
from eonwild_motion.solve.airborne_gait import _interior


def inspect(raw, plan, receipt, roles, forward, up):
    glb = Glb.from_bytes(raw)
    tracks, times = _clip_state(glb, glb.document['animations'][0]['name'])
    forward, up = np.asarray(forward), np.asarray(up)
    states = []
    rotations = []
    for i, time in enumerate(times):
        pose = _pose(glb, tracks, i)
        worlds = _world_matrices(glb, *pose)
        rotations.append(pose[1])
        row = {'time_s': time, 'plan': plan['samples'][i], 'legs': {}}
        for side in ('left', 'right'):
            chain = [glb.name_to_node[n] for n in roles['legs'][side]['contactChain']]
            hp, kp, ap, fp = [np.asarray(_world_position(worlds[n])) for n in chain]
            thigh = kp - hp
            row['legs'][side] = {'hip_degrees': float(np.degrees(np.arctan2(thigh @ forward, -thigh @ up))),
                'knee_degrees': _interior(hp-kp, ap-kp), 'ankle_degrees': _interior(kp-ap, fp-ap),
                'hip_to_foot_m': [float((fp-hp) @ forward), float((fp-hp) @ up)],
                'proxy': receipt.get('emitted_proxy_samples', [{}]*len(times))[i].get('feet', {}).get(side)}
        states.append(row)
    r = np.asarray(rotations)
    r /= np.linalg.norm(r, axis=2, keepdims=True)
    rates = np.degrees(2*np.arccos(np.clip(np.abs(np.sum(r[:-1]*r[1:], axis=2)), 0, 1))) / np.diff(times)[:, None]
    order = np.argsort(rates.max(axis=1))[-5:][::-1]
    peaks = [{'rate_degrees_per_s': float(rates[i].max()), 'node': int(rates[i].argmax()),
              'name': glb.nodes[int(rates[i].argmax())].get('name'), 'before': states[i], 'after': states[i+1]} for i in order]
    envelopes = sorted([(float((s['legs'][side]['proxy'] or {}).get('articulation_envelope_violation_degrees', 0)), i, side)
                        for i, s in enumerate(states) for side in ('left', 'right')], reverse=True)[:4]
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'native_samples': len(times),
        'peak_rates': peaks, 'worst_envelope_states': [{'error_degrees': e, 'side': side, 'state': states[i]} for e, i, side in envelopes],
        'first': states[0], 'last': states[-1]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--recipe', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True, exist_ok=False)
    recipe = json.loads(args.recipe.read_text())
    roles = json.loads((root/recipe['rig']['path']).read_text())['roles']
    report = {'classification': 'native diagnostic; not visual or Unity approval'}
    raw = plan = receipt = None
    try:
        compile_recipe(args.recipe, root=root, output=args.output/'candidate')
        report['verification'] = verify_package(args.output/'candidate')
        report['validation'] = json.loads((args.output/'candidate/validation.json').read_text())
        raw = (args.output/'candidate/root_motion.glb').read_bytes()
        plan = json.loads((args.output/'candidate/plan.json').read_text())
        receipt = json.loads((args.output/'candidate/solver-receipt.json').read_text())
    except Exception as exc:
        report['error'] = str(exc)
        report['traceback'] = traceback.format_exc()
        tb = exc.__traceback__
        while tb:
            scope = tb.tb_frame.f_locals
            if tb.tb_frame.f_code.co_name == 'solve_with_skin_targets':
                raw, plan, receipt = scope.get('root_raw'), scope.get('current'), scope.get('receipt')
                report['refinement_trace'] = scope.get('trace')
                report['iteration'] = scope.get('iteration')
            tb = tb.tb_next
    if raw is not None and plan is not None and receipt is not None:
        report['solver_summary'] = {k:v for k,v in receipt.items() if isinstance(v,(str,int,float,bool))}
        report['motion'] = inspect(raw, plan, receipt, roles, recipe['forward_axis'], recipe['up_axis'])
        (args.output/'diagnostic-root.glb').write_bytes(raw)
        (args.output/'diagnostic-plan.json').write_text(json.dumps(plan, indent=2, allow_nan=False)+'\n')
    (args.output/'diagnostic.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    # Keep logs bounded; the full final material validation remains in artifacts.
    log = {k:v for k,v in report.items() if k not in ('validation','traceback')}
    if 'validation' in report:
        v = report['validation']
        log['gates'] = {k:v[k] for k in ('technical_status','rotation_rates','cyclic_continuity','solver_feasibility')}
    print('MOTION_DIAGNOSTIC '+json.dumps(log, allow_nan=False), flush=True)
    return 0 if report.get('verification',{}).get('technical_status') == 'PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
