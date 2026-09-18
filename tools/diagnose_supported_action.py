"""Read-only failure localization for supported programs on admitted geometry.

Does not suppress or repair constraints, move anchors, or publish candidates.
Records the first failing pose and actual solver-local geometric witnesses.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import traceback
import numpy as np

from eonwild_motion.factory.compiler import load_recipe
from eonwild_motion.factory.source import geometry_height
from eonwild_motion.glb.container import Glb
from eonwild_motion.planning.supported_action import load_supported_action
from eonwild_motion.solve.supported_action import SupportedSolver


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    recipe,paths=load_recipe(args.recipe,root)
    source=Glb.from_bytes(paths['source'].read_bytes())
    roles=json.loads(paths['rig'].read_text())['roles']
    profile=json.loads(paths['contact_profile'].read_text())
    action=load_supported_action(json.loads(paths['program_profile'].read_text()))
    up=np.asarray(recipe['up_axis']);forward=np.asarray(recipe['forward_axis'])
    height=geometry_height(source,roles,up)
    args.output.mkdir(parents=True,exist_ok=False)
    solver=SupportedSolver(source,roles,action,profile,up,forward,height)
    rig=solver.rig
    report={'body_height_m':height,'support_calibration':solver.calibration,
        'initial_legs':{side:rig.neutral_world[chain,:3,3].tolist() for side,chain in rig.legs.items()},
        'calibrated_legs':{side:solver.w0[chain,:3,3].tolist() for side,chain in rig.legs.items()},'samples':[]}
    for phase in np.linspace(0,action.reference_duration_seconds,121):
        try:
            t,r,s,state,facts=solver.pose(float(phase))
            report['samples'].append({'phase':float(phase),'facts':facts,'body':state.get('body'),'jaw':state.get('actual_jaw_degrees')})
        except Exception as exc:
            failure={'phase':float(phase),'error':str(exc),'traceback':traceback.format_exc(),'frames':[]}
            tb=exc.__traceback__
            while tb:
                scope=tb.tb_frame.f_locals
                row={'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno}
                for key in ('side','target','hp','kp','ap','pk','pa','extension','error','witness','desired_surface','opening','gap'):
                    value=scope.get(key)
                    if isinstance(value,np.ndarray):row[key]=value.tolist()
                    elif isinstance(value,(str,int,float,np.floating)):row[key]=float(value) if isinstance(value,np.floating) else value
                failure['frames'].append(row);tb=tb.tb_next
            report['failure']=failure
            print('SUPPORTED_FAILURE '+json.dumps(failure,allow_nan=False),flush=True)
            break
    (args.output/'diagnostic.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print('CALIBRATED_LEGS '+json.dumps(report['calibrated_legs']))
    return 2 if 'failure' in report else 0


if __name__=='__main__':
    raise SystemExit(main())
