"""Feeding002: channel-overlapped performance atop preserved planted geometry.

The interpolation is reusable and dimensionless; profile data owns timing and
anatomical calibration. Feeding001 files are loaded read-only and never edited.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
from channels import curve

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('feeding_checkpoint_001',ROOT/'build/V9-FEEDING-REVIEW-001/feeding.py')
BASE=importlib.util.module_from_spec(spec)
spec.loader.exec_module(BASE)


def signal(time,profile):
    authored=time*6/profile['duration_seconds']
    return {name:curve(authored,keys) for name,keys in profile['channels'].items()}


# The checkpoint functions resolve signal from their module globals. This is
# process-local composition, not a source mutation or second pose writer.
BASE.signal=signal
BASE.CLIP='feeding_overlapped_grip_review'
setup=BASE.setup
pose=BASE.pose


def build(profile_path=HERE/'profile.json',output=HERE/'feeding.glb',receipt_path=HERE/'receipt.json'):
    result=BASE.build(profile_path,output,receipt_path)
    result['iteration']='Feeding002'
    result['interpolation']='C1 shape-preserving channel-specific cubic Hermite'
    result['preserved_checkpoint_sha256']='51ef2bc8f7d8990f54948a410c89eb777f57e71b97ba48eb2236524949be3682'
    result['composition_source_sha256']=BASE.B.sha(Path(__file__).read_bytes())
    result['interpolation_source_sha256']=BASE.B.sha((HERE/'channels.py').read_bytes())
    receipt_path.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',type=Path,default=HERE/'profile.json')
    parser.add_argument('--output',type=Path,default=HERE/'feeding.glb')
    parser.add_argument('--receipt',type=Path,default=HERE/'receipt.json')
    args=parser.parse_args()
    receipt=build(args.profile,args.output,args.receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='samples'},indent=2))
