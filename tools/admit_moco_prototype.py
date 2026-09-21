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
from eonwild_motion.solve.skin_rig import SkinRig

p=argparse.ArgumentParser();p.add_argument('--motion-set',type=Path,required=True);p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
class Captured(Exception):pass
captured={};original=CanonicalConstantSkinTargetLaw.__dict__['build']
def intercept(cls,query,provider,**kw):captured.update(context=query.context,source=kw['source'],contact=kw['contact_profile']);raise Captured()
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
skin=SkinRig(source,c.roles,c.forward,c.up,captured['contact'])
# Measure a skull-fixed rostral witness separately from the moving lower jaw.
# This is artist geometry, not a reconstructed eye or anatomical sight axis.
head=source.name_to_node[c.roles['head']]
def below(node,ancestor):
    while node is not None:
        if node==ancestor:return True
        node=source.parents[node]
    return False
skull_nodes=[n for n in range(len(source.nodes)) if below(n,head) and
             not (c.jaw is not None and below(n,c.jaw))]
head_weights=np.where(np.isin(skin.node_ids,skull_nodes),skin.weights,0).sum(axis=1)
head_indices=np.flatnonzero(head_weights>.6)
if not len(head_indices):raise ValueError('No skull-dominant skin for nose admission')
head_vertices=skin.skin(np.asarray(c.base_w),head_indices)
head_forward=head_vertices@c.forward
nose=head_vertices[head_forward>=np.quantile(head_forward,.98)].mean(axis=0)
points['nose']=[float((nose-origin)@axis) for axis in (c.forward,c.up,c.lateral)]
surface={}
for side in ('left','right'):
    vertices=skin.skin(np.asarray(c.base_w),skin.foot_masks[side])
    local=np.array([[float((v-positions[side+'Leg.3'])@axis) for axis in (c.forward,c.up,c.lateral)] for v in vertices])
    # Retain the measured material envelope. Fitting contact primitives belongs
    # to the versioned model recipe; these are geometry samples, not tissue data.
    surface[side]={'vertices_m':local.tolist(),'minimum_up_m':float(local[:,1].min()),
                   'frame':'forward/up/lateral relative to admitted MTP; original rest orientation',
                   'toe_midpoint_m':np.mean([np.array(points[k])-points[side+'Leg.3'] for k in points if k.startswith('legs.'+side+'.toeChains.') and k.endswith('.1')],axis=0).tolist()}
result={'schema':'eonwild.motion.moco-admission.v1','source_geometry_sha256':source_hash,
        'motion_set':str(a.motion_set),'profile_sha256':hashlib.sha256(a.profile.read_bytes()).hexdigest(),
        'animal':animal,'body_height_m':c.body_height,
        'preferred_speed_mps':profile['locomotion']['run']['preferredSpeed']['value'],
        'step_length_m':profile['locomotion']['run']['stepLength']['value'],
        'task_provenance':profile['locomotion']['run'],
        'coordinate_frame':'forward, up, lateral; meters relative to bilateral hip midpoint',
        'points':points,'foot_surface':surface}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.output)
