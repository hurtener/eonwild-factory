"""Compile an explicit steady/start/stop recipe set and verify both actual joins.

A passing clip never grants a passing handoff. Each requested package and both
joins must pass; errors remain visible and cause a nonzero exit. No cached
historical takes, diagnostic scripts, reference assets or retiming are inputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import traceback

from eonwild_motion.factory.compiler import compile_recipe, verify_package
from eonwild_motion.factory.handoff import verify_handoff


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('steady','start','stop'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    if args.output.exists():
        parser.error('choose a new output directory; existing evidence is immutable')
    args.output.mkdir(parents=True)
    result = {'schema':'eonwild.motion.transition-pair-verification.v1',
        'source_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        'packages':{},'handoffs':{},'visual_review':'PENDING','unity_validation':'NOT_RUN',
        'production_approved':False,'status':'BLOCKED'}
    def write():
        (args.output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    for name in ('steady','start','stop'):
        package = args.output/name
        try:
            compile_recipe(getattr(args,name),root=root,output=package)
            result['packages'][name] = verify_package(package)
        except Exception as exc:
            result['packages'][name] = {'technical_status':'ERROR','error':str(exc)}
            (args.output/f'{name}.error.log').write_text(traceback.format_exc())
        write()
        print('TRANSITION_PACKAGE',name,json.dumps(result['packages'][name]),flush=True)
    for kind in ('start','stop'):
        try:
            receipt = verify_handoff(args.output/kind,args.output/'steady',root=root)
        except Exception as exc:
            receipt = {'status':'ERROR','error':str(exc),'visual_review':'PENDING','unity_validation':'NOT_RUN'}
            (args.output/f'{kind}.handoff.error.log').write_text(traceback.format_exc())
        (args.output/f'{kind}.handoff.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
        summary = {k:v for k,v in receipt.items() if k!='modes'}
        summary['modes'] = {k:{x:y for x,y in v.items() if x!='motion_owned_nodes'} for k,v in receipt.get('modes',{}).items()}
        result['handoffs'][kind] = summary
        write()
        print('EMITTED_HANDOFF',kind,json.dumps(summary,allow_nan=False),flush=True)
    if (all(v['technical_status']=='PASS' for v in result['packages'].values())
        and all(v['status']=='PASS' for v in result['handoffs'].values())):
        result['status']='PASS'
    write()
    return 0 if result['status']=='PASS' else 2


if __name__=='__main__':
    raise SystemExit(main())
