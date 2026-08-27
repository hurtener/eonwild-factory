#!/usr/bin/env python3
"""Generate the preserved v1 phase-shaped FK walk for comparison."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(SCRIPT_DIR))
from eonproc_v1.gltf_io import GlbAsset, sha256_file
from eonproc_v1.rig import SemanticMap
from eonproc_v1.generator import LegacyBipedGenerator

def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--bone-map',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args()
 out=Path(a.output_dir).resolve();out.mkdir(parents=True,exist_ok=True);asset=GlbAsset(a.input);sem=SemanticMap.load(a.bone_map);gen=LegacyBipedGenerator(asset,sem);m=gen.generate();root_rest=asset.rest_translation[asset.name_to_node[gen.root]]
 spec={"name":"PROC_WALK_LARGE_V1","times":m['times'].astype('float32'),"rotations":{k:v.astype('float32') for k,v in m['rotations'].items()},"translations":{gen.root:__import__('numpy').repeat(root_rest[None,:],len(m['times']),axis=0).astype('float32')},"extras":{"generator":"Eonwild procedural animation skill v1 compatibility snapshot","contactAware":False,"sampleHz":gen.profile.sample_hz}}
 dest=out/(Path(a.input).stem+'.procedural-v1.glb');asset.write_animations(dest,[spec],replace_existing=True)
 report={"version":"1.0.0","asset_sha256":sha256_file(a.input),"output_sha256":sha256_file(dest),"clip":spec['name'],"driven_bones":len(gen.driven_bones),"sample_count":len(m['times']),"limitations":["Phase-shaped FK only","No world-space contact lock","No neutral jaw layer","Preset tail wave rather than inertial response"]}
 (out/'procedural-v1-report.json').write_text(json.dumps(report,indent=2));print(dest);return 0
if __name__=='__main__':raise SystemExit(main())
