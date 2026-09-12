"""Continuous whole-body turns with support-constrained foot accommodation.

Body heading, weight transfer and foot recovery overlap throughout the turn.
There is no per-step body wait or marching push-off in the turn-in-place law.
"""
import math
import numpy as np
from .grounded_gait import smooth


class DirectionalSteps:
    def __init__(self, origin, forward, lateral, up, height, lanes, foot_heights,
                 blocks, step_seconds=1.15):
        self.origin = np.asarray(origin)
        self.forward, self.lateral, self.up = map(np.asarray, (forward, lateral, up))
        self.height, self.lanes, self.foot_heights = height, lanes, foot_heights
        self.period = step_seconds
        self.blocks, self.steps = [], []
        time, center, heading = .45, np.zeros(3), 0.
        for spec in blocks:
            count, angle = spec['steps'], math.radians(spec['turn_degrees'])
            stationary = abs(spec['step_length_body_heights']) < 1e-12
            block = dict(start=time, end=time+count*self.period, center=center.copy(),
                         heading=heading, angle=angle, count=count, stationary=stationary,
                         length=count*spec['step_length_body_heights']*height,
                         label=spec['label'])
            block['turn_steps'] = []
            self.blocks.append(block)
            leading = max(lanes, key=lanes.get) if angle > 0 else min(lanes, key=lanes.get)
            trailing = next(s for s in lanes if s != leading)
            for index in range(count):
                side = (leading if index % 2 == 0 else trailing)
                duration = self.period * ((.84 if index % 2 == 0 else 1.16) if stationary else 1.)
                entry = dict(start=time, end=time+duration, side=side, block=block, index=index,
                             inner=index % 2 == 0, duration=duration)
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
            target_center, target_heading = self.body(min(block['end'],step['end']+.35*self.period))
            lane = self.lateral*math.cos(target_heading)-self.forward*math.sin(target_heading)
            target = self.origin+target_center+lane*lanes[side]
            if block['stationary'] and step['index'] < block['count']-2:
                forward = self.forward*math.cos(target_heading)+self.lateral*math.sin(target_heading)
                target += forward*self.height*(-.018 if step['inner'] else .032)
            target += self.up*(foot_heights[side]-target@self.up)
            self.events.append(dict(step, old=anchors[side].copy(), target=target,
                oldHeading=headings[side], targetHeading=target_heading, label=block['label']))
            anchors[side], headings[side] = target, target_heading

    def body(self, time):
        b = next((b for b in self.blocks if time <= b['end']), self.blocks[-1])
        u = smooth((time-b['start'])/(b['end']-b['start']))
        if b['stationary'] and b['turn_steps']:
            # Overlapping support exchanges advance heading, with a shorter
            # opening step and a longer outer accommodation step.
            weights = [.72 if e['inner'] else 1.28 for e in b['turn_steps']]
            u = sum(w*smooth((time-max(b['start'],e['start']-.12*e['duration'])) /
                            (min(b['end'],e['end']+.12*e['duration'])-max(b['start'],e['start']-.12*e['duration'])))
                    for w,e in zip(weights,b['turn_steps'])) / sum(weights)
        theta, h = b['angle']*u, b['heading']
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
            unload = smooth((time-(e['start']-.16*d))/(.34*d))
            reload = smooth((time-(e['end']-.18*d))/(.34*d))
            weight -= math.copysign(1.,self.lanes[e['side']]) * unload*(1-reload)
        return weight

    def sample(self, time):
        center, heading = self.body(time)
        feet = {}
        for side in self.anchors:
            position, yaw = self.anchors[side].copy(), 0.
            contact, swing, roll = True, 0., 0.
            for e in self.events:
                if e['side'] != side: continue
                if time >= e['end']:
                    position, yaw = e['target'].copy(), e['targetHeading']
                    continue
                if time < e['start']: break
                phase = (time-e['start'])/e['duration']
                peak_roll = 5. if e['block']['stationary'] else 18.
                if phase <= .18:
                    roll = peak_roll*smooth(phase/.18)
                elif phase < .82:
                    swing = (phase-.18)/.64
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
                    lift = 64*swing**3*(1-swing)**3
                    position += self.up*(clearance*self.height*lift)
                    yaw = (1-yaw_blend)*e['oldHeading']+yaw_blend*e['targetHeading']
                    roll = peak_roll*(1-smooth(swing/.32))
                    contact = False
                else:
                    position, yaw = e['target'].copy(), e['targetHeading']
                break
            feet[side] = dict(contact=contact, position=position, heading=yaw,
                             swing_phase=swing, roll_degrees=roll)
        axis = self.lateral*math.cos(heading)-self.forward*math.sin(heading)
        shift = axis*(.055*self.height*self.weight(time))
        label = next((e['label'] for e in self.events if e['start']<=time<=e['end']), 'settle')
        return dict(weight=self.weight(time), time=time, center=center+shift, heading=heading, feet=feet, label=label, turn_in_place=next((b['stationary'] for b in self.blocks if time<=b['end']),self.blocks[-1]['stationary']))
