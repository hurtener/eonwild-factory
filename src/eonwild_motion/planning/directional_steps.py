"""Authored alternating-contact turn choreography. Geometry enters as data."""
import math
import numpy as np
from .grounded_gait import smooth

class DirectionalSteps:
    def __init__(self, origin,forward,lateral,up,height,lanes,foot_heights,blocks,step_seconds=1.15):
        self.origin=np.array(origin);self.forward=np.array(forward);self.lateral=np.array(lateral);self.up=np.array(up);self.height=height;self.lanes=lanes;self.foot_heights=foot_heights;self.period=step_seconds
        # Gentle walking curve, short tighter curve, then a stepping turn in place.
        self.blocks=[(b['steps'],b['step_length_body_heights'],math.radians(b['turn_degrees']),b['label']) for b in blocks]
        self.steps=[];time=1.;center=np.zeros(3);heading=0.
        for count,distance,angle,label in self.blocks:
            self.steps.extend([{'start':time+i*self.period,'end':time+(i+1)*self.period,'blockStart':time,'blockEnd':time+count*self.period,'center':center.copy(),'heading':heading,'angle':angle,'length':count*distance*height,'side':'left' if len(self.steps)%2==0 else 'right','label':label} for i in range(count)])
            # Correct side assignment independent of list-comprehension append timing.
            for index,step in enumerate(self.steps):step['side']='left' if index%2==0 else 'right'
            center,heading=self.body(time+count*self.period);time+=count*self.period+1.
        self.duration=time
        self.anchors={s:self.origin+self.lateral*lanes[s]+self.up*(foot_heights[s]-self.origin@self.up) for s in lanes}
        self.events=[];anchors={s:p.copy() for s,p in self.anchors.items()};headings={s:0. for s in lanes}
        for step in self.steps:
            side=step['side'];end_center,end_heading=self.body(min(step['blockEnd'],step['end']+.65*self.period))
            lane=self.lateral*math.cos(end_heading)-self.forward*math.sin(end_heading)
            target=self.origin+end_center+lane*lanes[side];target+=self.up*(foot_heights[side]-target@self.up)
            event=dict(step,old=anchors[side].copy(),target=target,oldHeading=headings[side],targetHeading=end_heading)
            self.events.append(event);anchors[side]=target;headings[side]=end_heading
    def body(self,time):
        step=next((x for x in self.steps if time<=x['blockEnd']),self.steps[-1])
        u=smooth((time-step['blockStart'])/(step['blockEnd']-step['blockStart']));theta=step['angle']*u;h=step['heading']
        if abs(step['angle'])>1e-8:
            radius=step['length']/step['angle'];x=radius*(math.cos(h)-math.cos(h+theta));z=radius*(math.sin(h+theta)-math.sin(h))
        else:x=math.sin(h)*step['length']*u;z=math.cos(h)*step['length']*u
        return step['center']+self.lateral*x+self.forward*z,h+theta
    def sample(self,time):
        center,heading=self.body(time);feet={};active=None
        for side in self.anchors:
            position=self.anchors[side].copy();yaw=0.;contact=True;swing=0.;roll=0.;roll_scale=0.
            for e in self.events:
                if e['side']!=side:continue
                if time>=e['end']:position=e['target'].copy();yaw=e['targetHeading'];continue
                if time<e['start']:break
                u=(time-e['start'])/self.period
                # Heel release begins while the leg is still supporting the body.
                roll=18.*smooth(u/.22) if u<=.22 else 18.*(1-smooth((u-.22)/.22))
                roll_scale=roll/18.
                if .22<u<.88:
                    swing=(u-.22)/.66;blend=smooth(swing);position=(1-blend)*e['old']+blend*e['target'];position+=self.up*(.045*self.height*math.sin(math.pi*swing)**2);yaw=(1-blend)*e['oldHeading']+blend*e['targetHeading'];contact=False;active=side
                elif u>=.88:position=e['target'].copy();yaw=e['targetHeading']
                break
            feet[side]={'contact':contact,'position':position,'heading':yaw,'swing_phase':swing,'roll_degrees':roll,'roll_scale':roll_scale}
        shift=np.zeros(3)
        if active:
            u=feet[active]['swing_phase'];sign=-math.copysign(1,self.lanes[active]);axis=self.lateral*math.cos(heading)-self.forward*math.sin(heading);shift=axis*(sign*.025*self.height*math.sin(math.pi*u)**2)
        return {'time':time,'center':center+shift,'heading':heading,'feet':feet,'label':next((e['label'] for e in self.events if e['start']<=time<=e['end']),'settle')}
