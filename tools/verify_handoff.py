"""Verify an emitted start/stop against its exact bound steady package."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from eonwild_motion.errors import ContractError
from eonwild_motion.factory.handoff import verify_handoff


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--transition',type=Path,required=True)
    p.add_argument('--steady',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():p.error('handoff receipt exists; select a new output')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=verify_handoff(args.transition,args.steady,root=Path(__file__).resolve().parents[1])
    except (ContractError,ValueError,KeyError,OSError,TypeError) as exc:
        result={'status':'ERROR','error':str(exc),'visual_review':'PENDING','unity_validation':'NOT_RUN','production_approved':False}
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,allow_nan=False),flush=True)
    return 0 if result['status']=='PASS' else 2


if __name__=='__main__':raise SystemExit(main())
