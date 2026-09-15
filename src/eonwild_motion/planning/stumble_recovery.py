"""Causal side-hit choreography, using received impulse and victim capabilities.

Impulse / mass estimates the incoming velocity change. Catch placements, trunk
compliance and stopping distance are authored kinematics, not collision dynamics.
The approved deliberate lateral-recovery planner is independent of this behavior.
"""
import math
import numpy as np
from .directional_steps import DirectionalSteps
from .grounded_gait import smooth


class StumbleRecoverySteps(DirectionalSteps):
    def __init__(self, origin, forward, lateral, up, height, lanes, foot_heights,
                 capabilities, recipe):
        if set(lanes) != {'left', 'right'}:
            raise ValueError('Stumble recovery requires two semantic support sides')
        self.origin = np.asarray(origin, dtype=float)
        self.forward, self.lateral, self.up = map(np.asarray, (forward, lateral, up))
        self.height, self.lanes, self.foot_heights = height, lanes, foot_heights
        self.policy = recipe['impact']
        self.walking, self.turn_stance = dict(recipe['walking']), recipe['turn_stance']
        self.anchors = {s:self.origin+self.lateral*lanes[s]+self.up*
                        (foot_heights[s]-self.origin@self.up) for s in lanes}
        self.events, self.steps, self.blocks = [], [], []
        anchors = {s:p.copy() for s,p in self.anchors.items()}
        headings = {s:0. for s in lanes}
        normal_step = capabilities['stepLengthM']/capabilities['preferredSpeedMps']
        period = max(normal_step*self.policy['step_fraction_of_normal_step'],
                     1/capabilities['maximumStepFrequencyHz'])
        self.period = period
        time, center = self.policy['initial_hold_seconds'], np.zeros(3)
        for spec in recipe['blocks']:
            side, impulse = spec['side'], spec['received_impulse_ns']
            if (side not in lanes or isinstance(impulse, bool) or
                    not isinstance(impulse, (float, int)) or not math.isfinite(impulse) or impulse <= 0):
                raise ValueError('Impact requires a semantic side and positive finite received impulse in N s')
            direction = math.copysign(1., lanes[side])
            velocity = impulse/capabilities['massKg']
            distance = velocity*self.policy['reaction_seconds'] + velocity**2/(2*capabilities['lateralAccelerationMps2'])
            if distance > self.policy['maximum_recoverable_distance_body_heights']*height:
                raise ValueError('Impact exceeds this grounded recovery study; a fall behavior is required')
            pairs = max(1, math.ceil(distance/(self.policy['catch_reach_body_heights']*height)))
            count = pairs*2
            end = time+self.policy['reaction_seconds']+count*period
            b = dict(start=time,end=end,center=center.copy(),delta=self.lateral*direction*distance,
                     heading=0.,angle=0.,stationary=False,count=count,length=distance,
                     side=side,direction=direction,label=spec['label'],period=period,
                     walk_articulation_scale=1.,walk_clearance_scale=1.,
                     received_impulse_ns=impulse,velocity_change_mps=velocity,
                     severity=velocity/self.policy['reference_velocity_mps'])
            self.blocks.append(b)
            follower = next(s for s in lanes if s != side)
            for index in range(count):
                moving = side if index%2 == 0 else follower
                # Early opening catches most momentum. Later pairs make smaller
                # corrections; the follower restores the same broad base.
                fraction = 1-(1-(index//2+1)/pairs)**1.25
                target = self.anchors[moving]+center+b['delta']*fraction
                target_heading = math.copysign(math.radians(self.policy['opening_yaw_degrees']), lanes[moving])
                start = time+self.policy['reaction_seconds']+index*period
                e = dict(start=start,end=start+period,duration=period,period=period,
                         side=moving,block=b,index=index,inner=index%2==1,
                         old=anchors[moving].copy(),target=target,
                         oldHeading=headings[moving],targetHeading=target_heading,
                         label=spec['label']+('/catch' if index == 0 else '/absorb and recover'))
                self.events.append(e); self.steps.append(e)
                anchors[moving], headings[moving] = target, target_heading
            center += b['delta']
            time = end+self.policy['settle_seconds']
        self.duration = time

    def body(self, time):
        b = next((b for b in self.blocks if time <= b['end']), self.blocks[-1])
        u = np.clip((time-b['start'])/(b['end']-b['start']), 0., 1.)
        # Early displacement followed by continuous deceleration across catches.
        # Zero endpoint velocity/acceleration; no independent per-step pulse.
        progress = 20*u**3-45*u**4+36*u**5-10*u**6
        return b['center']+b['delta']*progress, 0.

    def response(self, time):
        roll = drop = look = torso_roll = tail_yaw = 0.
        for b in self.blocks:
            age = time-b['start']
            if age <= 0: continue
            span = b['end']-b['start']
            rise = smooth(age/self.policy['recoil_rise_seconds'])
            decay = math.exp(-age/(span*.55))
            finish = 1-smooth((age-span)/(self.policy['settle_seconds']))
            envelope = rise*decay*finish
            severity = min(b['severity'], 1.8)
            roll -= b['direction']*math.radians(self.policy['pelvis_roll_degrees'])*severity*envelope
            drop += self.policy['compression_body_heights']*self.height*severity*envelope
            # Chest gives first; head and tail lag and then recover, rather than
            # looking toward an unannounced collision before it has happened.
            torso_roll -= b['direction']*math.radians(self.policy['torso_roll_degrees'])*severity*envelope
            delayed = smooth((age-.10)/.30)*math.exp(-max(0.,age-.10)/(span*.7))*finish
            look -= b['direction']*self.policy['attention_fraction_of_normal']*min(severity,1.)*delayed
            tail_yaw += b['direction']*math.radians(self.policy['tail_yaw_degrees'])*severity*delayed
        return dict(roll_radians=roll,drop_m=drop,look_normal_fraction=look,
                    torso_roll_radians=torso_roll,tail_yaw_radians=tail_yaw)
