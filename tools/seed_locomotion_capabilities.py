"""Seed a new admitted biped profile from a labeled geometric-similarity prior.

Never admits a rig or infers biological performance from its mesh. The output
requires numerical calibration and native-time review on the target animal.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from eonwild_motion.embodiment import validate
from eonwild_motion.planning.locomotion_capabilities import resolve_capabilities


def seed(target, reference, reference_hash):
    validate(target);validate(reference);resolve_capabilities(reference)
    a=target['authoring'];b=reference['authoring']
    for authored in (a,b):
        limb=authored['animalInstance']['measurements']['hindlimb_length']
        if limb['unit']!='m' or not math.isfinite(limb['value']) or limb['value']<=0:
            raise ValueError('Similarity seeding requires positive hindlimb length in metres')
    mass=a['animalInstance']['measurements']['body_mass']['value']/b['animalInstance']['measurements']['body_mass']['value']
    length=a['animalInstance']['measurements']['hindlimb_length']['value']/b['animalInstance']['measurements']['hindlimb_length']['value']
    if not all(math.isfinite(v) and v>0 for v in (mass,length)):
        raise ValueError('An admitted target needs positive mass and limb length')
    d=deepcopy(reference['locomotion'])
    factors={'yawInertia':mass*length**2,'iliumArea':length**2,
        'forwardForce':length**2,'brakingForce':length**2,'lateralForce':length**2,
        'yawTorque':length**3,'yawBrakingTorque':length**3,
        'maximumYawRate':1/math.sqrt(length),'preferredSpeed':math.sqrt(length),
        'maximumGroundedSpeed':math.sqrt(length),'maximumStepFrequency':1/math.sqrt(length),
        'attentionLead':math.sqrt(length)}
    for group in ('body','control','walk','style'):
        for key,item in d[group].items():
            factor=factors.get(key,1.)
            item['value']*=factor;item['classification']='derived_estimate'
            item['source']={'citation':'Eonwild geometric-similarity onboarding prior',
                'referenceProfileSha256':reference_hash,'referenceField':group+'.'+key,
                'massRatio':mass,'hindlimbLengthRatio':length,'multiplier':factor,
                'rationale':'Scaled or inherited authored prior. Not fossil measurement, measured force, or evidence of species-specific performance.'}
    d['limitations'].append('SEEDED PRIOR: mass/length similarity cannot capture muscle physiology or differing body proportions. Calibrate every capability and review the actual rig before accepting it.')
    result=deepcopy(target);result['locomotion']=d;resolve_capabilities(result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--target',type=Path,required=True,help='Existing admitted heavy-biped embodiment profile')
    p.add_argument('--reference',type=Path,required=True,help='Existing capability profile; source of a labeled prior')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise ValueError('Refusing to overwrite a profile')
    raw=a.reference.read_bytes()
    result=seed(json.loads(a.target.read_text()),json.loads(raw),hashlib.sha256(raw).hexdigest())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('Wrote unreviewed capability prior:',a.output)
