"""Directional contact choreography: curved walking and leading-foot step turns.

Step turns own their support order. The leading foot opens before body rotation;
weight then transfers onto it so the trailing foot can follow. Rig solving is
separate from this authored behavior law.
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
            if stationary and count % 2:
                raise ValueError('step turns need complete leading/trailing pairs')
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
        self.events, self.weight_keys = [], [(0.,0.)]
        for step in self.steps:
            side, block = step['side'], step['block']
            if block['stationary']:
                pair = step['index']//2
                target_heading = block['heading']+block['angle']*(pair+1)/(block['count']/2)
                target_center = block['center']
            else:
                target_center, target_heading = self.body(min(block['end'],step['end']+.65*self.period))
            lane = self.lateral*math.cos(target_heading)-self.forward*math.sin(target_heading)
            target = self.origin+target_center+lane*lanes[side]
            target += self.up*(foot_heights[side]-target@self.up)
            self.events.append(dict(step, old=anchors[side].copy(), target=target,
                oldHeading=headings[side], targetHeading=target_heading, label=block['label']))
            anchors[side], headings[side] = target, target_heading
            support = -math.copysign(1., lanes[side])
            self.weight_keys.extend([(step['start']+.18*self.period,support),
                                     (step['start']+.82*self.period,support)])
            if step['index']==block['count']-1:
                self.weight_keys.append((block['end']+.6,0.))

    def body(self, time):
        b = next((b for b in self.blocks if time <= b['end']), self.blocks[-1])
        if b['stationary']:
            # The leading foot lands at .82 of its step. Only then does the
            # pelvis rotate into that support while the trailing foot follows.
            pairs = b['count']//2
            progress = np.clip((time-b['start'])/(2*self.period),0,pairs)
            pair = min(int(progress), pairs-1)
            local = progress-pair
            gain = smooth((local-.41)/.54)
            return b['center'].copy(), b['heading']+b['angle']*(pair+gain)/pairs
        u = smooth((time-b['start'])/(b['end']-b['start']))
        theta, h = b['angle']*u, b['heading']
        if abs(b['angle']) > 1e-8:
            radius = b['length']/b['angle']
            x,z = radius*(math.cos(h)-math.cos(h+theta)), radius*(math.sin(h+theta)-math.sin(h))
        else:
            x,z = math.sin(h)*b['length']*u, math.cos(h)*b['length']*u
        return b['center']+self.lateral*x+self.forward*z, h+theta

    def weight(self, time):
        for (a,x),(b,y) in zip(self.weight_keys,self.weight_keys[1:]):
            if time <= b:
                return x+(y-x)*smooth((time-a)/(b-a))
        return self.weight_keys[-1][1]

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
                peak_roll = 6. if e['block']['stationary'] else 18.
                if phase <= .18:
                    roll = peak_roll*smooth(phase/.18)
                elif phase < .82:
                    swing = (phase-.18)/.64
                    blend = smooth(swing)
                    # The foot opens early in recovery; it is already aimed
                    # toward the intended support before weight arrives.
                    yaw_blend = smooth(min(1.,swing/.75))
                    position = (1-blend)*e['old']+blend*e['target']
                    clearance = .018 if e['block']['stationary'] else .035
                    position += self.up*(clearance*self.height*math.sin(math.pi*swing)**2)
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
        return dict(time=time, center=center+shift, heading=heading, feet=feet, label=label)
