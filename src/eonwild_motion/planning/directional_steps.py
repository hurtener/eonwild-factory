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
        time, center, heading = 1., np.zeros(3), 0.
        for spec in blocks:
            count, angle = spec['steps'], math.radians(spec['turn_degrees'])
            stationary = abs(spec['step_length_body_heights']) < 1e-12
            block = dict(start=time, end=time+count*self.period, center=center.copy(),
                         heading=heading, angle=angle, count=count, stationary=stationary,
                         length=count*spec['step_length_body_heights']*height,
                         label=spec['label'])
            self.blocks.append(block)
            leading = max(lanes, key=lanes.get) if angle > 0 else min(lanes, key=lanes.get)
            trailing = next(s for s in lanes if s != leading)
            for index in range(count):
                side = (leading if index % 2 == 0 else trailing)
                self.steps.append(dict(start=time+index*self.period,
                    end=time+(index+1)*self.period, side=side, block=block, index=index))
            center, heading = self.body(block['end'])
            time = block['end']+1.
        self.duration = time
        self.anchors = {s:self.origin+self.lateral*lanes[s]
            +self.up*(foot_heights[s]-self.origin@self.up) for s in lanes}
        anchors = {s:p.copy() for s,p in self.anchors.items()}
        headings = {s:0. for s in lanes}
        self.events = []
        for step in self.steps:
            side, block = step['side'], step['block']
            target_center, target_heading = self.body(min(block['end'],step['end']+.45*self.period))
            lane = self.lateral*math.cos(target_heading)-self.forward*math.sin(target_heading)
            target = self.origin+target_center+lane*lanes[side]
            target += self.up*(foot_heights[side]-target@self.up)
            self.events.append(dict(step, old=anchors[side].copy(), target=target,
                oldHeading=headings[side], targetHeading=target_heading, label=block['label']))
            anchors[side], headings[side] = target, target_heading

    def body(self, time):
        b = next((b for b in self.blocks if time <= b['end']), self.blocks[-1])
        u = smooth((time-b['start'])/(b['end']-b['start']))
        theta, h = b['angle']*u, b['heading']
        if abs(b['angle']) > 1e-8:
            radius = b['length']/b['angle']
            x,z = radius*(math.cos(h)-math.cos(h+theta)), radius*(math.sin(h+theta)-math.sin(h))
        else:
            x,z = math.sin(h)*b['length']*u, math.cos(h)*b['length']*u
        return b['center']+self.lateral*x+self.forward*z, h+theta

    def weight(self, time):
        # One continuous transfer wave, not a list of hold/shift commands.
        b = next((b for b in self.blocks if time <= b['end']), self.blocks[-1])
        phase = (time-b['start'])/self.period
        if phase < 0 or phase > b['count']: return 0.
        lead = next(e['side'] for e in self.events if e['block'] is b)
        envelope = smooth(phase/.35)*smooth((b['count']-phase)/.35)
        return -math.copysign(1.,self.lanes[lead])*math.sin(math.pi*phase)*envelope

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
                phase = (time-e['start'])/self.period
                peak_roll = 0. if e['block']['stationary'] else 18.
                if phase <= .08:
                    roll = peak_roll*smooth(phase/.08)
                elif phase < .92:
                    swing = (phase-.08)/.84
                    blend = smooth(swing)
                    # The foot opens early in recovery; it is already aimed
                    # toward the intended support before weight arrives.
                    yaw_blend = blend
                    position = (1-blend)*e['old']+blend*e['target']
                    if e['block']['stationary']:
                        # Carry the foot around the body on an arc, with no
                        # marching push-off or early completed yaw command.
                        carried = (1-blend)*e['oldHeading']+blend*e['targetHeading']
                        axis = self.lateral*math.cos(carried)-self.forward*math.sin(carried)
                        position = self.origin+e['block']['center']+axis*self.lanes[side]
                        position += self.up*(self.foot_heights[side]-position@self.up)
                    clearance = .015 if e['block']['stationary'] else .035
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
        shift = axis*(.035*self.height*self.weight(time))
        label = next((e['label'] for e in self.events if e['start']<=time<=e['end']), 'settle')
        return dict(time=time, center=center+shift, heading=heading, feet=feet, label=label, turn_in_place=next((b['stationary'] for b in self.blocks if time<=b['end']),self.blocks[-1]['stationary']))
