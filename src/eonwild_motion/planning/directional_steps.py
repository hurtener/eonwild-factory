"""Continuous whole-body turns with support-constrained foot accommodation.

Body heading, weight transfer and foot recovery overlap throughout the turn.
There is no per-step body wait or marching push-off in the turn-in-place law.
"""
import math
import numpy as np
from .grounded_gait import smooth
from .airborne_gait import rounded_swing_height
from .walking_response import recovery_window


class DirectionalSteps:
    def __init__(self, origin, forward, lateral, up, height, lanes, foot_heights,
                 blocks, step_seconds=1.15, turn_stance=None, walking=None):
        self.origin = np.asarray(origin)
        self.forward, self.lateral, self.up = map(np.asarray, (forward, lateral, up))
        self.height, self.lanes, self.foot_heights = height, lanes, foot_heights
        self.period = step_seconds
        self.turn_stance = turn_stance or {}
        self.walking = walking or {}
        if 'heel_peak_swing_fraction' in self.walking:
            peak=self.walking['heel_peak_swing_fraction']
            release=self.walking.get('heel_release_swing_fraction')
            if (not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
                        for v in (peak,release)) or not 0 < peak < release < .9):
                raise ValueError('Walking heel overlap requires 0 < peak < release < .9')
        self.blocks, self.steps = [], []
        time, center, heading = .45, np.zeros(3), 0.
        for spec in blocks:
            count, angle = spec['steps'], math.radians(spec['turn_degrees'])
            period = spec.get('step_seconds', self.period)
            stationary = abs(spec['step_length_body_heights']) < 1e-12
            block = dict(start=time, end=time+count*period, center=center.copy(),
                         heading=heading, angle=angle, count=count, stationary=stationary,
                         length=count*spec['step_length_body_heights']*height,
                         walk_articulation_scale=spec.get('walk_articulation_scale',1.),
                         walk_clearance_scale=spec.get('walk_clearance_scale',1.),
                         label=spec['label'])
            block['turn_steps'] = []
            self.blocks.append(block)
            inner_side = max(lanes, key=lanes.get) if angle > 0 else min(lanes, key=lanes.get)
            leading = next(s for s in lanes if s != inner_side) if stationary else inner_side
            trailing = next(s for s in lanes if s != leading)
            for index in range(count):
                side = (leading if index % 2 == 0 else trailing)
                inner = side == inner_side
                duration = period * ((.84 if inner else 1.16) if stationary else 1.)
                entry = dict(start=time, end=time+duration, side=side, block=block, index=index,
                             inner=inner, duration=duration, period=period)
                self.steps.append(entry)
                block['turn_steps'].append(entry)
                time += duration
            block['end'] = time
            center, heading = self.body(block['end'])
            time = block['end']+.45
        self.duration = time
        self.anchors = {s:self.origin+self.lateral*lanes[s]
            +self.up*(foot_heights[s]-self.origin@self.up) for s in lanes}
        anchors = {s:p.copy() for s,p in self.anchors.items()}
        headings = {s:0. for s in lanes}
        self.events = []
        for step in self.steps:
            side, block = step['side'], step['block']
            target_center, target_heading = self.body(min(block['end'],step['end']+.35*step['period']))
            lane = self.lateral*math.cos(target_heading)-self.forward*math.sin(target_heading)
            target = self.origin+target_center+lane*lanes[side]
            if block['stationary'] and step['index'] < block['count']-2:
                forward = self.forward*math.cos(target_heading)+self.lateral*math.sin(target_heading)
                target += forward*self.height*(-.018 if step['inner'] else .032)
                if not step['inner']:
                    target += lane*math.copysign(self.turn_stance.get('outside_opening_body_heights',.045)*height,lanes[side])
            target += self.up*(foot_heights[side]-target@self.up)
            self.events.append(dict(step, old=anchors[side].copy(), target=target,
                oldHeading=headings[side], targetHeading=target_heading, label=block['label']))
            anchors[side], headings[side] = target, target_heading

    def body(self, time):
        b = next((b for b in self.blocks if time <= b['end']), self.blocks[-1])
        u = smooth((time-b['start'])/(b['end']-b['start']))
        if b['stationary'] and b['turn_steps']:
            # The outside step opens space; the inner step contributes more
            # rotation as support passes onto the opened foot. Intervals overlap.
            weights = [1.20 if e['inner'] else .80 for e in b['turn_steps']]
            u = sum(w*smooth((time-max(b['start'],e['start']-.65*e['duration'])) /
                            (min(b['end'],e['end']+.65*e['duration'])-max(b['start'],e['start']-.65*e['duration'])))
                    for w,e in zip(weights,b['turn_steps'])) / sum(weights)
        if not b['stationary'] and self.walking:
            # Integrate a smooth speed ramp around steady travel; keep heading
            # on the same arc. No per-step start/stop pulse.
            x=max(0.,min(1.,(time-b['start'])/(b['end']-b['start'])))
            r=self.walking['travel_ramp_fraction']
            integral=lambda z:z**6-3*z**5+2.5*z**4
            if x<r:u=r*integral(x/r)/(1-r)
            elif x>1-r:u=1-r*integral((1-x)/r)/(1-r)
            else:u=(x-r/2)/(1-r)
        theta, h = b['angle']*u, b['heading']
        if b['stationary'] and b['turn_steps']:
            # Translate around changing support locations instead of a fixed
            # pelvis pivot. The same overlapping turn progress drives yaw and
            # travel; planted foot targets remain world anchored.
            center = b['center'].copy()
            previous_heading = h
            gain = self.turn_stance.get('support_pivot_fraction_of_lane',1.)
            for weight,e in zip(weights,b['turn_steps']):
                start=max(b['start'],e['start']-.65*e['duration'])
                end=min(b['end'],e['end']+.65*e['duration'])
                progress=smooth((time-start)/(end-start))
                increment=b['angle']*weight/sum(weights)
                support=next(side for side in self.lanes if side!=e['side'])
                pivot=self.lanes[support]*gain
                a=previous_heading; z=a+increment*progress
                center += pivot*(self.lateral*(math.cos(a)-math.cos(z))
                                 -self.forward*(math.sin(a)-math.sin(z)))
                previous_heading += increment
            return center,h+theta
        if abs(b['angle']) > 1e-8:
            radius = b['length']/b['angle']
            x,z = radius*(math.cos(h)-math.cos(h+theta)), radius*(math.sin(h+theta)-math.sin(h))
        else:
            x,z = math.sin(h)*b['length']*u, math.cos(h)*b['length']*u
        return b['center']+self.lateral*x+self.forward*z, h+theta

    def weight(self, time):
        # Unload before departure and accept weight after arrival. Overlap
        # adjacent exchanges instead of returning the pelvis to center per step.
        weight = 0.
        for e in self.events:
            d = e['duration']
            lift,touch=recovery_window(e,self.walking)
            unload = smooth((time-(e['start']+(lift-.30)*d))/(.30*d))
            reload = smooth((time-(e['start']+touch*d))/(.30*d))
            weight -= math.copysign(1.,self.lanes[e['side']]) * unload*(1-reload)
        return weight

    def sample(self, time):
        center, heading = self.body(time)
        feet = {}
        for side in self.anchors:
            position, yaw = self.anchors[side].copy(), 0.
            contact, swing, roll = True, 0., 0.
            articulation_scale = 1.
            for e in self.events:
                if e['side'] != side: continue
                if time >= e['end']:
                    position, yaw = e['target'].copy(), e['targetHeading']
                    continue
                walking=not e['block']['stationary'] and bool(self.walking)
                articulation_scale=e['block']['walk_articulation_scale'] if walking else 1.
                prepare=self.walking.get('heel_prepare_step_fraction',0.) if walking else 0.
                peak_roll=articulation_scale*self.walking.get('heel_roll_degrees',18.) if walking else (5. if e['block']['stationary'] else 18.)
                phase = (time-e['start'])/e['duration']
                lift,touch=recovery_window(e,self.walking)
                span=touch-lift
                if walking and self.walking.get('heel_prepare_seconds'):
                    prepare=self.walking['heel_prepare_seconds']/e['duration']-lift
                overlap=walking and 'heel_peak_swing_fraction' in self.walking
                if overlap:
                    # Continue heel rise THROUGH toe release. Recovery travel
                    # is already moving before the heel reaches its maximum.
                    peak=lift+span*self.walking['heel_peak_swing_fraction']
                    end=lift+span*self.walking['heel_release_swing_fraction']
                    carried_roll=peak_roll*(smooth((phase+prepare)/(peak+prepare))
                        if phase<=peak else 1-smooth((phase-peak)/(end-peak)))
                if time < e['start']:
                    if walking:
                        roll=carried_roll if overlap else peak_roll*smooth((time-e['start']+prepare*e['duration'])/((prepare+.1)*e['duration']))
                    break
                if phase <= lift:
                    roll = carried_roll if overlap else peak_roll*smooth((phase+prepare)/(.10+prepare))
                elif phase < touch:
                    swing = (phase-lift)/span
                    blend = smooth(swing)
                    # The foot opens early in recovery; it is already aimed
                    # toward the intended support before weight arrives.
                    yaw_blend = smooth(swing/.90)
                    position = (1-blend)*e['old']+blend*e['target']
                    clearance = (.028 if e['inner'] else .036) if e['block']['stationary'] else .035
                    if e['block']['stationary']:
                        carried = (1-blend)*e['oldHeading']+blend*e['targetHeading']
                        axis = self.lateral*math.cos(carried)-self.forward*math.sin(carried)
                        # A free leg opens away from the other leg, not through
                        # a fixed-radius circle which can crowd the support.
                        position += axis*math.copysign(.022*self.height,self.lanes[side])*math.sin(math.pi*swing)**2
                    if walking:
                        clearance=self.walking['clearance_body_heights']*e['block']['walk_clearance_scale']
                        carried=(1-blend)*e['oldHeading']+blend*e['targetHeading']
                        axis=self.lateral*math.cos(carried)-self.forward*math.sin(carried)
                        position+=axis*math.copysign(self.walking['recovery_outward_body_heights']*self.height,self.lanes[side])*math.sin(math.pi*swing)**2
                    lift = (rounded_swing_height(swing,self.walking['rounded_swing_peak_fraction'])
                            if walking and self.walking.get('rounded_swing_peak_fraction') else
                            64*swing**3*(1-swing)**3)
                    position += self.up*(clearance*self.height*lift)
                    yaw = (1-yaw_blend)*e['oldHeading']+yaw_blend*e['targetHeading']
                    roll = carried_roll if overlap else peak_roll*(1-smooth(swing/.32))
                    contact = False
                else:
                    position, yaw = e['target'].copy(), e['targetHeading']
                break
            feet[side] = dict(contact=contact, position=position, heading=yaw,
                             swing_phase=swing, roll_degrees=roll, walk_articulation_scale=articulation_scale)
        axis = self.lateral*math.cos(heading)-self.forward*math.sin(heading)
        half_width = (max(self.lanes.values())-min(self.lanes.values()))/2
        shift = axis*(self.turn_stance.get('support_shift_fraction_of_half_width',.42)*half_width*self.weight(time))
        label = next((e['label'] for e in self.events if e['start']<=time<=e['end']), 'settle')
        return dict(weight=self.weight(time), time=time, center=center+shift, heading=heading, feet=feet, label=label, turn_in_place=next((b['stationary'] for b in self.blocks if time<=b['end']),self.blocks[-1]['stationary']))
