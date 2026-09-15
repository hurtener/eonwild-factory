"""Resolve evidenced animal data and authored control budgets for shared planning.

These are effective locomotion-path budgets, not reconstructed muscles or solved forces.
The published agility proxy stays separate from dimensional control quantities.
"""
from copy import deepcopy
import math
import numpy as np
from .directional_steps import DirectionalSteps


UNITS = {
    'body': {'yawInertia': 'kg*m^2', 'iliumArea': 'cm^2'},
    'control': {'forwardForce': 'N', 'brakingForce': 'N', 'lateralForce': 'N',
                'yawTorque': 'N*m', 'yawBrakingTorque': 'N*m',
                'maximumYawRate': 'deg/s', 'tractionCoefficient': '1'},
    'walk': {'preferredSpeed': 'm/s', 'maximumGroundedSpeed': 'm/s',
             'maximumStepFrequency': 'steps/s'},
    'style': {'effort': '1', 'turnCadenceMultiplier': '1',
              'maximumHeadingPerStep': 'deg', 'attentionLead': 's',
              'responseTimeScale': '1'},
}


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def resolve_capabilities(profile):
    """Pure, naming-independent resolver; values and units remain in the profile."""
    d = profile['locomotion']; a = profile['authoring']
    if d.get('contract') != 'eonwild.locomotion-capabilities.v1' or d.get('family') != 'heavy-predatory-biped':
        raise ValueError('Unsupported locomotion capability contract or family')
    values = {}
    for group, fields in UNITS.items():
        values[group] = {}
        for key, unit in fields.items():
            item = d[group][key]
            if (item.get('unit') != unit or not positive(item.get('value'))
                    or item.get('classification') not in ('published_estimate', 'authored_estimate', 'derived_estimate', 'measured')
                    or not item.get('source', {}).get('citation')):
                raise ValueError('Invalid capability value, units or provenance: '+group+'.'+key)
            values[group][key] = float(item['value'])
    mass = a['animalInstance']['measurements']['body_mass']
    if mass['unit'] != 'kg' or not positive(mass['value']) or not mass.get('source'):
        raise ValueError('Capabilities require evidenced mass in kg')
    step = a['stepLengthM']; stride = a['sameFootStrideM']
    if not positive(step) or not positive(stride) or not math.isclose(stride, 2*step, rel_tol=1e-6):
        raise ValueError('Expected one step and same-foot stride intent')
    c, w, s, b = (values[k] for k in ('control', 'walk', 'style', 'body'))
    if not 0 < s['effort'] <= 1 or w['preferredSpeed'] > w['maximumGroundedSpeed']:
        raise ValueError('Invalid effort or walking speed range')
    if not d.get('limitations'):
        raise ValueError('Capability limitations must be explicit')
    m = mass['value']; effort = s['effort']; inertia = b['yawInertia']
    traction = c['tractionCoefficient'] * 9.81
    result = dict(contract=d['contract'], family=d['family'], massKg=m,
        yawInertiaKgM2=inertia, stepLengthM=step, sameFootStrideM=stride,
        preferredSpeedMps=w['preferredSpeed'],
        maximumGroundedSpeedMps=min(w['maximumGroundedSpeed'],step*w['maximumStepFrequency']),
        maximumStepFrequencyHz=w['maximumStepFrequency'],
        forwardAccelerationMps2=min(c['forwardForce']/m*effort,traction),
        brakingAccelerationMps2=min(c['brakingForce']/m*effort,traction),
        lateralAccelerationMps2=min(c['lateralForce']/m*effort,traction),
        yawAccelerationRadps2=c['yawTorque']/inertia*effort,
        yawBrakingRadps2=c['yawBrakingTorque']/inertia*effort,
        maximumYawRateRadps=math.radians(c['maximumYawRate'])*effort,
        turnCadenceMultiplier=s['turnCadenceMultiplier'],
        maximumHeadingPerStepDegrees=s['maximumHeadingPerStep'],
        attentionLeadSeconds=s['attentionLead'],
        responseSeconds=s['responseTimeScale']*math.sqrt(inertia/(c['yawTorque']*effort)),
        publishedTurningProxy=b['iliumArea']/inertia)
    # Separate normalized scores, not one blended number controlling every motion.
    result['agilityComponents'] = dict(
        forward=result['forwardAccelerationMps2']/9.81,
        braking=result['brakingAccelerationMps2']/9.81,
        lateral=result['lateralAccelerationMps2']/9.81,
        turning=result['yawAccelerationRadps2']/9.81)
    result['agilityNormalization'] = 'Linear components divided by g; turning divided by g/(1 metre). Authored effort included; not the published index.'
    if "impactResponse" in profile:
        result["impactResponse"] = deepcopy(profile["impactResponse"])
    return result


def resolve_walk(c, requested_speed=None):
    speed = c['preferredSpeedMps'] if requested_speed is None else requested_speed
    if not isinstance(speed,(int,float)) or not math.isfinite(speed) or speed < 0:
        raise ValueError('Walking request must be finite and nonnegative')
    resolved = min(speed,c['maximumGroundedSpeedMps'])
    return dict(requestedSpeedMps=speed, speedMps=resolved,
        stepLengthM=c['stepLengthM'], sameFootStrideM=c['sameFootStrideM'],
        stepSeconds=c['stepLengthM']/resolved if resolved else None,
        limited=resolved < speed)


def advance_walk_speed(c, current, requested, dt):
    if not all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in (current,requested,dt)):
        raise ValueError('Invalid walking state or timestep')
    target=resolve_walk(c,requested)['speedMps']
    limit=c['forwardAccelerationMps2'] if target>=current else c['brakingAccelerationMps2']
    return current+max(-limit*dt,min(limit*dt,target-current))


def yaw_rate_at_speed(c, speed):
    if not math.isfinite(speed) or speed<0: raise ValueError('Invalid speed')
    return min(c['maximumYawRateRadps'],c['lateralAccelerationMps2']/speed) if speed else c['maximumYawRateRadps']


def plan_directional(c, origin, forward, lateral, up, height, lanes, foot_heights, recipe):
    """Regenerate coordinated steps; never retime or filter an emitted clip.

Fit the shared planner's body trajectory to the capability budgets. All joint
and skin constraints run afterwards. This does not certify forces in the final rig.
"""
    recipe=deepcopy(recipe)
    blocks=deepcopy(recipe['blocks']); walk=resolve_walk(c)
    direction=recipe.get('travel_direction','forward')
    if direction=='impact_lateral':
        if recipe.get('walking',{}).get('articulation_source')!='stumble_grounded':
            raise ValueError('Impact recovery requires its own grounded articulation policy')
        from .stumble_recovery import StumbleRecoverySteps
        if recipe["impact"].get("response_model")=="support_coupled":
            from .impact_response import ReactiveImpactSteps
            sequence=ReactiveImpactSteps(origin,forward,lateral,up,height,lanes,foot_heights,c,recipe)
        else:
            sequence=StumbleRecoverySteps(origin,forward,lateral,up,height,lanes,foot_heights,c,recipe)
        return sequence,dict(walk=walk,blocks=[dict(label=b['label'],side=b['side'],
            receivedImpulseNs=b['received_impulse_ns'],velocityChangeMps=b['velocity_change_mps'],
            distanceM=b['length'],stepSeconds=b['period'],catchSteps=b['count'],impactTimeS=b['start'])
            for b in sequence.blocks],method='Received impulse / victim mass with authored catching and compliance; no collision detection or final whole-body force balance.')
    if direction=='lateral':
        if recipe.get('walking',{}).get('articulation_source')!='lateral_grounded':
            raise ValueError('Lateral travel requires its own grounded articulation policy')
        from .lateral_recovery import LateralRecoverySteps
        sequence=LateralRecoverySteps(origin,forward,lateral,up,height,lanes,foot_heights,c,recipe)
        return sequence,dict(walk=walk,blocks=[dict(label=b['label'],side=b['side'],
            distanceM=b['length'],stepSeconds=b['period']) for b in sequence.blocks],
            method='Open-and-follow lateral recovery; quintic path duration bounded by effective lateral force/mass and cadence. Local support accommodation is not a solved whole-body COM response.')
    if direction not in ('forward','backward'):
        raise ValueError('Unsupported travel direction')
    if direction=='backward' and recipe.get('walking',{}).get('articulation_source')!='backward_grounded':
        raise ValueError('Backward travel requires its own grounded articulation policy')
    if recipe.get('walking',{}).get('recovery_fraction_of_normal_step'):
        recipe['walking']['recovery_seconds']=walk['stepSeconds']*recipe['walking']['recovery_fraction_of_normal_step']
        recipe['walking']['heel_prepare_seconds']=walk['stepSeconds']*recipe['walking']['heel_prepare_fraction_of_normal_step']
    for b in blocks:
        if direction=='backward' and ('step_scale_of_normal' not in b or b.get('turn_degrees')!=0):
            raise ValueError('Backward review requires profile-relative straight steps')
        if 'step_scale_of_normal' in b:
            factor=b['step_scale_of_normal']
            if not positive(factor) or 'step_length_body_heights' in b:
                raise ValueError('Declare one positive walking step scale, without a competing absolute length')
            b['step_length_body_heights']=factor*c['stepLengthM']/height
            b['resolved_step_length_m']=factor*c['stepLengthM']
            if direction=='backward':
                b['step_length_body_heights']*=-1
                b['resolved_step_length_m']*=-1
        speed_scale=b.get('speed_scale',1.)
        if not positive(speed_scale) or speed_scale>1:
            raise ValueError('Walking speed scale must be in (0,1]')
        if abs(b['step_length_body_heights'])<1e-12:
            count=max(b['steps'],math.ceil(abs(b['turn_degrees'])/c['maximumHeadingPerStepDegrees']))
            b['steps']=count+(count%2)  # recover both feet to broad support
            b['step_seconds']=max(1/c['maximumStepFrequencyHz'],walk['stepSeconds']/c['turnCadenceMultiplier'])
        else:
            b['step_seconds']=max(1/c['maximumStepFrequencyHz'],
                abs(b['step_length_body_heights'])*height/(walk['speedMps']*speed_scale))
    def make():
        return DirectionalSteps(origin,forward,lateral,up,height,lanes,foot_heights,
            blocks,recipe['step_seconds'],turn_stance=recipe['turn_stance'],walking=recipe.get('walking'))
    diagnostics=[]
    # The path shape is unchanged under block time scaling; two rounds account
    # for support envelopes reaching across the fixed inter-block settling gap.
    for iteration in range(2):
        p=make(); diagnostics=[]
        for spec,b in zip(blocks,p.blocks):
            ts=np.linspace(b['start'],b['end'],257);dt=ts[1]-ts[0]
            headings=np.array([p.body(t)[1] for t in ts])
            # Constrain the locomotion path. Local pelvis support accommodation
            # is a separate response, not yet a solved whole-body COM trajectory.
            centers=np.array([p.body(t)[0] for t in ts])
            velocity=np.gradient(centers,dt,axis=0);acceleration=np.gradient(velocity,dt,axis=0)
            speed=np.linalg.norm(velocity,axis=1)
            tangential=np.sum(velocity*acceleration,axis=1)/np.maximum(speed,1e-8)
            lateral_acc=np.sqrt(np.maximum(0,np.sum(acceleration**2,axis=1)-tangential**2))
            rate=np.gradient(headings,dt);angular_acc=np.gradient(rate,dt)*math.copysign(1,b['angle'] or 1)
            scale=max(1.,float(speed.max())/c['maximumGroundedSpeedMps'],
                float(np.max(np.abs(rate)))/c['maximumYawRateRadps'],
                math.sqrt(max(0,float(angular_acc.max()))/c['yawAccelerationRadps2']),
                math.sqrt(max(0,float(-angular_acc.min()))/c['yawBrakingRadps2']),
                math.sqrt(max(0,float(tangential.max()))/c['forwardAccelerationMps2']),
                math.sqrt(max(0,float(-tangential.min()))/c['brakingAccelerationMps2']),
                math.sqrt(float(lateral_acc.max())/c['lateralAccelerationMps2']))
            diagnostics.append(dict(label=b['label'],fitScale=scale,stepSeconds=spec['step_seconds']*scale))
            spec['step_seconds']*=scale
    return make(),dict(walk=walk,blocks=blocks,fit=diagnostics,
        method='Locomotion path constrained by effective linear/angular budgets; excludes local pelvis accommodation and does not certify whole-body forces')
