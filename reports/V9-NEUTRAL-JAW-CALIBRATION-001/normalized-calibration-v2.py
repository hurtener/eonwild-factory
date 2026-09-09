from dataclasses import replace
import hashlib,json
from pathlib import Path
from eonwild_motion.factory.animal import apply_uniform_geometry_scale,load_animal_instance
from eonwild_motion.glb.container import Glb
from eonwild_motion.solve.jaw_response import _posed_gap,_semantic_body_height
from eonwild_motion.solve.performance import load_performance
ROOT=Path('/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521/worktrees/eonwild-neutral-jaw-calibration')
SHA='2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f'; source=Glb.from_bytes((ROOT/'assets/sha256'/f'{SHA}.glb').read_bytes()); roles=json.loads((ROOT/'catalog/rigs/heavy-biped.v9.json').read_text())['roles']; old=load_performance(json.loads((ROOT/'catalog/performance/heavy-biped.tarbosaurus-adult-walk.v7.json').read_text())).neutral_jaw_calibration
height=_semantic_body_height(source,roles,(0,1,0)); target=.0015*height
low,high=49.,52.
for _ in range(80):
 mid=(low+high)/2; gap=_posed_gap(source,roles,replace(old,close_degrees=mid),(0,0,1),(0,1,0))[2]
 if gap>target: low=mid
 else: high=mid
angle=(low+high)/2; calibrated=replace(old,close_degrees=angle,measured_body_height_m=height,measured_minimum_gap_m=target); raw_gap=_posed_gap(source,roles,calibrated,(0,0,1),(0,1,0))[2]
animal=load_animal_instance(json.loads((ROOT/'catalog/animals/tarbosaurus-bataar-pin-552-1.adult.v2.json').read_text()),source_sha256=SHA);apply_uniform_geometry_scale(source,animal['uniform_scale']);scaled_height=_semantic_body_height(source,roles,(0,1,0));scaled_gap=_posed_gap(source,roles,calibrated,(0,0,1),(0,1,0))[2]
out={'schema':'eonwild.motion.neutral-jaw-normalized-calibration.v2','classification':'Authored engineering positive sampled surface clearance; not tooth contact, biological measurement, or visual approval.','source_geometry_sha256':hashlib.sha256(source.raw).hexdigest(),'method':calibrated.method,'axis_frame':calibrated.axis_frame,'clearance_body_heights':.0015,'close_degrees':angle,'raw_source':{'body_height_m':height,'minimum_gap_m':raw_gap,'gap_body_heights':raw_gap/height},'uniform_animal_scale':animal['uniform_scale'],'scaled_admitted':{'body_height_m':scaled_height,'minimum_gap_m':scaled_gap,'gap_body_heights':scaled_gap/scaled_height},'prior_diagnostic':{'report_sha256':'9d9abfcd7c0b9b10c663b9d952e0e7cbe7e39e011f11cbdec2d1007551171eec','result_sha256':'abd44cbff9a77ffb556764fdb100d58516907fc8314620a515f4e2ba7dee115c','use':'surface witness and initial bracket only; v2 re-solves the angle in one raw-source space'}}
path=Path(__file__).with_suffix('.json');path.write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2))
