"""Review an existing immutable package; never regenerate or repair its motion.

Native-time reference comparisons retain the original V9 bytes, floor and
clock. Camera locks are shared per view. Mechanical, rendering, visual and
Unity results are distinct and all media are tied to exact source hashes.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import traceback

from eonwild_motion.factory.compiler import verify_package
from build_showcase import render_view, VIEWS
from prepare_motion_reference import prepare

V9_FOLDER = 'build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12'
V9_SHA = 'b54e3740ea451927b3b812c1be3f4ca6146cc369ad1313be7f08edd5ca741cd3'
V9_FORWARD = [0.038931620556417676, 0.0, 0.9992418770852487]


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--views',choices=VIEWS,nargs='+',default=list(VIEWS))
    parser.add_argument('--fps',type=int,default=30)
    parser.add_argument('--blender',default='blender')
    parser.add_argument('--compare-v9-walk',action='store_true')
    args=parser.parse_args(argv)
    if not 12<=args.fps<=120 or len(set(args.views))!=len(args.views):
        parser.error('review needs unique views and a supported frame rate')
    root=Path(__file__).resolve().parents[1]
    package=args.package.resolve();output=args.output.resolve()
    before=verify_package(package)
    identity=hashlib.sha256((package/'manifest.json').read_bytes()).hexdigest()
    output.mkdir(parents=True,exist_ok=False)
    result={'schema':'eonwild.motion.compiled-review.v1','candidate_manifest_sha256':identity,
        'source_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        'candidate_status':before,'views':{},'visual_review':'PENDING','unity_parity':'NOT_RUN','production_approved':False}
    reference=None
    try:
        if args.compare_v9_walk:
            recipe=json.loads((package/'recipe.json').read_text())
            if not recipe['id'].startswith('heavy-biped.walk.'):
                raise ValueError('this explicit V9 comparison is for the normal walking family')
            reference=output/'reference-package'
            folder=root/V9_FOLDER
            result['reference']=prepare(folder/'narrow-gauge-walk-root_motion.glb',V9_SHA,
                'PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION',root/recipe['rig']['path'],
                folder/'candidate-contact-profile-root_motion.json',V9_FORWARD,reference,loop=True)
        for index,view in enumerate(args.views):
            camera=output/'cameras'/f'{view}.json' if reference else None
            row={}
            if reference:
                row['reference']=render_view(reference,output/'reference'/view,root=root,blender=args.blender,
                    view=view,mode='root_motion',fps=args.fps,fbx=False,camera_lock=camera)
                if row['reference']['status']!='PASS':
                    result['views'][view]=row
                    continue
            row['candidate']=render_view(package,output/'candidate'/view,root=root,blender=args.blender,
                view=view,mode='root_motion',fps=args.fps,fbx=index==0,camera_lock=camera)
            result['views'][view]=row
        result['candidate_status']=verify_package(package)
        if hashlib.sha256((package/'manifest.json').read_bytes()).hexdigest()!=identity:
            raise ValueError('candidate manifest changed during review')
    except Exception as exc:
        result['error']=str(exc)
        (output/'error.log').write_text(traceback.format_exc())
        print(traceback.format_exc(),flush=True)
    render_ok=('error' not in result and all(result['views'].get(view,{}).get('candidate',{}).get('status')=='PASS'
        and (not reference or result['views'][view].get('reference',{}).get('status')=='PASS') for view in args.views))
    result['render_status']='PASS' if render_ok else 'FAIL'
    result['exit_code']=1 if not render_ok else (0 if result['candidate_status']['technical_status']=='PASS' else 2)
    (output/'review-summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print('COMPILED_REVIEW '+json.dumps({k:v for k,v in result.items() if k!='views'},allow_nan=False),flush=True)
    return result['exit_code']


if __name__=='__main__':raise SystemExit(main())
