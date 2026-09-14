"""Authored open-and-follow balance steps, using the shared support interface.

This is planned kinematic balance recovery, not a response to simulated impact.
"""
import math
import numpy as np
from .directional_steps import DirectionalSteps
from .grounded_gait import smooth
from .foot_articulation import recovery_pitch


class LateralRecoverySteps(DirectionalSteps):
    """Open with the foot on the travel side; follow without crossing feet."""

    def __init__(self, origin, forward, lateral, up, height, lanes, foot_heights,
                 capabilities, recipe):
        if len(lanes) != 2 or set(lanes) != {'left', 'right'}:
            raise ValueError('Lateral recovery requires semantic left/right support')
        self.origin=np.asarray(origin)
        self.forward,self.lateral,self.up=map(np.asarray,(forward,lateral,up))
        self.height,self.lanes,self.foot_heights=height,lanes,foot_heights
        self.turn_stance=recipe['turn_stance']
        self.walking=dict(recipe['walking'])
        self.policy=recipe['lateral']
        normal_step=capabilities['stepLengthM']/capabilities['preferredSpeedMps']
        self.walking['recovery_seconds']=normal_step*self.policy['recovery_fraction_of_normal_step']
        self.walking['heel_prepare_seconds']=normal_step*self.policy['heel_prepare_fraction_of_normal_step']
        self.anchors={s:self.origin+self.lateral*lanes[s]
                      +self.up*(foot_heights[s]-self.origin@self.up) for s in lanes}
        self.events,self.steps,self.blocks=[],[],[]
        anchors={s:p.copy() for s,p in self.anchors.items()}
        headings={s:0. for s in lanes}
        time,center=.45,np.zeros(3)
        for spec in recipe['blocks']:
            side=spec['side']
            distance=spec['distance_body_heights']*height
            if side not in lanes or not math.isfinite(distance) or not 0<distance<=.3*height:
                raise ValueError('Invalid bounded lateral recovery intent')
            direction=math.copysign(1.,lanes[side])
            # Quintic path acceleration has maximum 10/sqrt(3) * d/T^2.
            period=max(normal_step*self.policy['step_fraction_of_normal_step'],
                       1/capabilities['maximumStepFrequencyHz'],
                       math.sqrt(10/math.sqrt(3)*distance/capabilities['lateralAccelerationMps2'])/1.8)
            block=dict(start=time,end=time+2*period,center=center.copy(),
                       delta=self.lateral*direction*distance,heading=0.,angle=0.,
                       stationary=False,count=2,length=distance,side=side,
                       direction=direction,label=spec['label'],period=period,
                       walk_articulation_scale=1.,walk_clearance_scale=1.)
            self.blocks.append(block)
            for index,moving in enumerate((side,next(s for s in lanes if s!=side))):
                target=anchors[moving]+block['delta']
                target_heading=math.copysign(math.radians(self.policy['opening_yaw_degrees']),lanes[moving])
                e=dict(start=time+index*period,end=time+(index+1)*period,
                       duration=period,period=period,side=moving,block=block,index=index,
                       inner=index==1,old=anchors[moving].copy(),target=target,
                       oldHeading=headings[moving],targetHeading=target_heading,
                       label=spec['label']+(' / open and catch' if index==0 else ' / recover stance'))
                self.events.append(e);self.steps.append(e)
                anchors[moving],headings[moving]=target.copy(),target_heading
            center=center+block['delta']
            time=block['end']+self.policy['settle_seconds']
        self.duration=time
        self.period=self.events[0]['period']

    def body(self,time):
        block=next((b for b in self.blocks if time<=b['end']),self.blocks[-1])
        u=smooth((time-(block['start']+.1*block['period']))/(1.8*block['period']))
        return block['center']+block['delta']*u,0.


def lateral_articulation(phase,contact,roll,policy):
    crown=-recovery_pitch(phase,1.,.44,.94) if not contact else 0.
    return {'toe_flex_degrees':policy['toe_curl_degrees']*crown,
            'foot_pitch_degrees':roll+policy['metatarsal_pitch_degrees']*crown,
            'articulation_scale':.30,
            'walking_knee_preference_degrees':policy['knee_extension_preference_degrees']}


def lateral_attention(sequence,time,policy,attention):
    gain=0.
    for b in sequence.blocks:
        gain+=b['direction']*smooth((time-b['start']+.3)/.65)*(1-smooth((time-b['end']+.1)/.55))
    return math.radians(attention['envelope']['normalDegrees']*policy['attention_gain'])*gain
