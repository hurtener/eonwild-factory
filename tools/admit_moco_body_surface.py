#!/usr/bin/env python3
"""Admit body contact witnesses from source skin, without changing mass or ROM.

Rigid segment ownership is a collision approximation; blended skin is audited
again after export. Never infer a collision radius from a mass/inertia radius.
"""
import argparse,hashlib,json,itertools
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from eonwild_motion.factory.compiler import compile_motion_set
from eonwild_motion.solve.constant_skin_targets import CanonicalConstantSkinTargetLaw
from eonwild_motion.solve.skin_rig import SkinRig

ap=argparse.ArgumentParser()
for n in ('motion-set','profile','metadata','output'):ap.add_argument('--'+n,type=Path,required=True)
a=ap.parse_args();captured={}
class Captured(Exception):pass
original=CanonicalConstantSkinTargetLaw.__dict__['build']
def intercept(cls,query,provider,**kw):
    captured.update(context=query.context,source=kw['source'],contact=kw['contact_profile']);raise Captured()
CanonicalConstantSkinTargetLaw.build=classmethod(intercept)
try:
    try:compile_motion_set(a.motion_set.resolve(),'walk',root=Path.cwd(),output=a.output.with_suffix('.never-published'))
    except Captured:pass
finally:CanonicalConstantSkinTargetLaw.build=original
c,source=captured['context'],captured['source'];meta=json.loads(a.metadata.read_text());profile=json.loads(a.profile.read_text())
assert hashlib.sha256(source.raw).hexdigest()==meta['admission']['source_geometry_sha256']
roles={b['role']:source.name_to_node[b['bone']] for b in profile['bindings']}
base=np.array(c.base_w);basis=np.column_stack((c.forward,c.up,c.lateral));origin=(base[roles['leftLeg.0'],:3,3]+base[roles['rightLeg.0'],:3,3])/2
skin=SkinRig(source,c.roles,c.forward,c.up,captured['contact']);vertices=(skin.skin(base,np.arange(len(skin.weights)))-origin)@basis
mapping={roles['root']:'trunk'};origins={'trunk':np.zeros(3)};rotations={'trunk':np.eye(3)}
for b in meta['axial_bindings']:
    mapping[roles[b['role']]]=b['body'];origins[b['body']]=np.array(meta['admission']['points'][b['role']]);rotations[b['body']]=np.eye(3)
for side,s in [('left','l'),('right','r')]:
    for j,body in enumerate(['thigh','shin','metatarsus','toe']):
        body+='_'+s;role=side+'Leg.'+str(j);mapping[roles[role]]=body;origins[body]=np.array(meta['admission']['points'][role]);R=np.eye(3)
        if j<3:
            end=np.array(meta['admission']['points'][side+'Leg.'+str(j+1)]);direction=end-origins[body];direction/=np.linalg.norm(direction)
            R=Rotation.align_vectors([direction],[[0.,-1.,0.]])[0].as_matrix()
        rotations[body]=R
# Unmodelled forelimbs must not inflate the chest envelope; they are tucked by
# the semantic carriage layer and remain an emitted-skin review responsibility.
for role in ('leftShoulder','rightShoulder','jaw_lower'):
    if role in roles:mapping[roles[role]]=None
owner={}
for node in np.unique(skin.node_ids):
    current=int(node)
    while current is not None and current not in mapping:current=source.parents[current]
    owner[int(node)]=mapping.get(current)
names=sorted(origins);weight=np.array([np.where(np.vectorize(owner.get)(skin.node_ids)==body,skin.weights,0).sum(axis=1) for body in names]).T
assign=weight.argmax(axis=1);confidence=weight.max(axis=1);sites={};L=sum(meta['segment_lengths_m']);radius=.004*L
# Fourteen support directions, including oblique surfaces during a roll.
directions=np.array([v for v in itertools.product((-1,0,1),repeat=3) if any(v) and (sum(x!=0 for x in v) in (1,3))],float)
directions/=np.linalg.norm(directions,axis=1)[:,None]
for j,body in enumerate(names):
    if body.startswith(('toe','metatarsus','shin')):continue
    points=(vertices[(assign==j)&(confidence>.45)]-origins[body])@rotations[body]
    if len(points)<8:continue
    selected=[]
    for d in directions:
        projection=points@d;near=points[projection>=np.quantile(projection,.99)]
        point=near.mean(axis=0)
        selected.append(dict(center_local_m=(point-radius*d).tolist(),radius_m=radius,normal_local=d.tolist()))
    sites[body]=selected
result=dict(schema='eonwild.motion.admitted-body-surface.v1',source_geometry_sha256=meta['admission']['source_geometry_sha256'],classification='Source-skin support witnesses with rigid segment ownership; not tissue mechanics',sites=sites)
a.output.write_text(json.dumps(result,indent=2)+'\n');print('Admitted',len(sites),'body surfaces')
