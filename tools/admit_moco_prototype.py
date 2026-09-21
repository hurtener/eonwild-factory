#!/usr/bin/env python3
"""Capture fresh admitted semantic anatomy before the walking solver runs.

Uses the existing diagnostic admission seam used by running previews. This is a
single-process CLI; it never reads an animated take or emits a walking asset.
"""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from eonwild_motion.factory.compiler import compile_motion_set
from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw

p=argparse.ArgumentParser();p.add_argument('--motion-set',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
class Captured(Exception):pass
captured={};original=CanonicalConstantSkinTargetLaw.__dict__['build']
def intercept(cls,query,provider,**kw):captured.update(context=query.context,source=kw['source']);raise Captured()
CanonicalConstantSkinTargetLaw.build=classmethod(intercept)
try:
    try:compile_motion_set(a.motion_set.resolve(),'walk',root=Path.cwd(),output=a.output.parent/(a.output.stem+'.never-published'))
    except Captured:pass
finally:CanonicalConstantSkinTargetLaw.build=original
c=captured['context'];source=captured['source'];profile=json.loads(a.profile.read_text());animal=profile['authoring']['animalInstance']
if animal['measurements']['body_mass'].get('unit')!='kg':raise ValueError('Body mass must use kg')
for key,unit in [('preferredSpeed','m/s'),('stepLength','m')]:
    if profile['locomotion']['run'][key].get('unit')!=unit:raise ValueError('Run task units mismatch: '+key)
source_hash=hashlib.sha256(source.raw).hexdigest()
if source_hash!=animal['geometry_calibration']['source_geometry_sha256']:raise ValueError('Admission/profile source hash mismatch')
if not math.isclose(profile['authoring']['bodyHeightM'],c.body_height,rel_tol=1e-6):raise ValueError('Admission/profile height mismatch')
positions={b['role']:np.asarray(c.base_w[source.name_to_node[b['bone']]])[:3,3] for b in profile['bindings']}
origin=(positions['leftLeg.0']+positions['rightLeg.0'])/2
points={role:[float((v-origin)@axis) for axis in (c.forward,c.up,c.lateral)] for role,v in positions.items()}
result={'schema':'eonwild.motion.moco-admission.v1','source_geometry_sha256':source_hash,
        'motion_set':str(a.motion_set),'profile_sha256':hashlib.sha256(a.profile.read_bytes()).hexdigest(),
        'animal':animal,'body_height_m':c.body_height,
        'preferred_speed_mps':profile['locomotion']['run']['preferredSpeed']['value'],
        'step_length_m':profile['locomotion']['run']['stepLength']['value'],
        'task_provenance':profile['locomotion']['run'],
        'coordinate_frame':'forward, up, lateral; meters relative to bilateral hip midpoint',
        'points':points}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output)
