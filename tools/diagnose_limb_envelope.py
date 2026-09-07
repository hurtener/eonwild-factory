"""Preserve actionable geometric facts when candidate compilation rejects.

Read-only observer of the failed solve. Does not catch an error and call it a
pass, publish incomplete motion, alter parameters, or move the floor/anchors.
"""
from __future__ import annotations
import argparse,json,traceback
from pathlib import Path
import numpy as np
from eonwild_motion.factory.compiler import compile_recipe,verify_package


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True,exist_ok=False)
    try:
        compile_recipe(args.recipe,root=root,output=args.output/'candidate')
        result=verify_package(args.output/'candidate')
        print('ENVELOPE_ACCEPTANCE '+json.dumps(result),flush=True)
        return 0 if result['technical_status']=='PASS' else 2
    except Exception as exc:
        report={'error':str(exc),'traceback':traceback.format_exc(),'frames':[]}
        tb=exc.__traceback__
        while tb:
            scope=tb.tb_frame.f_locals
            row={'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno}
            if row['function']=='solve_with_skin_targets':
                row['iteration']=scope.get('iteration');row['trace']=scope.get('trace')
                receipt=scope.get('receipt',{})
                row['solver_summary']={k:v for k,v in receipt.items() if isinstance(v,(str,int,float,bool))}
                plan=scope.get('current',{});samples=plan.get('samples',[])
                for key in ('offsets','corrections','next_offsets'):
                    values=scope.get(key)
                    if not isinstance(values,dict):continue
                    row[key]={}
                    for side,array in values.items():
                        array=np.asarray(array);index=int(np.linalg.norm(array,axis=1).argmax())
                        row[key][side]={'maximum_norm_m':float(np.linalg.norm(array[index])),
                            'index':index,'value':array[index].tolist(),'plan_sample':samples[index] if index<len(samples) else None}
                        emitted=receipt.get('emitted_proxy_samples',[])
                        if index<len(emitted):row[key][side]['emitted_proxy']=emitted[index]['feet'][side]
                proposed=scope.get('proposed')
                if isinstance(proposed,np.ndarray):
                    index=int(np.linalg.norm(proposed,axis=1).argmax())
                    row['proposed']={'index':index,'value':proposed[index].tolist(),'norm':float(np.linalg.norm(proposed[index]))}
            report['frames'].append(row);tb=tb.tb_next
        (args.output/'failure.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print('LIMB_ENVELOPE_FAILURE '+json.dumps(report,allow_nan=False),flush=True)
        return 2


if __name__=='__main__':raise SystemExit(main())
