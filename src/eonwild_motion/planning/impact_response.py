"""Support-coupled impact preview. Reduced horizontal dynamics, authored compliance.

The source gait supplies entry state; contacts and bounded effective reactions
brake the body. This is not articulated inverse dynamics or collision detection.
"""
import math
from copy import deepcopy
import numpy as np
from .directional_steps import DirectionalSteps
from .grounded_gait import smooth


def quintic(p, v, a, target, duration):
    c0 = np.asarray(p); c1 = np.asarray(v)*duration
    c2 = .5*np.asarray(a)*duration**2
    b = np.asarray(target)-c0-c1-c2; e = -c1-2*c2; f = -2*c2
    return np.array([c0,c1,c2,10*b-4*e+.5*f,-15*b+7*e-f,6*b-3*e+.5*f])


class ReactiveImpactSteps(DirectionalSteps):
    def __init__(self, origin, forward, lateral, up, height, lanes, foot_heights,
                 capabilities, recipe):
        if len(recipe['blocks']) != 1:
            raise ValueError('Select one impact case; review cases have independent entry states')
        self.origin=np.asarray(origin,dtype=float)
        self.forward,self.lateral,self.up=map(np.asarray,(forward,lateral,up))
        self.height,self.lanes,self.foot_heights=height,lanes,foot_heights
        self.walking=recipe['walking'];self.turn_stance={'support_shift_fraction_of_half_width':0.}
        self.policy=recipe['impact']; self.c=capabilities
        self.anatomy=capabilities['impactResponse']; spec=recipe['blocks'][0]
        self.period=max(capabilities['stepLengthM']/capabilities['preferredSpeedMps']*
                        self.policy['step_fraction_of_normal_step'],1/capabilities['maximumStepFrequencyHz'])
        self.anchors={s:self.origin+self.lateral*lanes[s]+self.up*
                      (foot_heights[s]-self.origin@self.up) for s in lanes}
        components=np.asarray(spec['impulse_lateral_up_forward_ns'],dtype=float)
        if components.shape!=(3,) or not np.isfinite(components).all() or np.linalg.norm(components)<=0 or abs(components[1])>1e-8:
            raise ValueError('Grounded impact requires a finite nonzero horizontal impulse')
        self.impulse=self.lateral*components[0]+self.forward*components[2]
        self.impulse_velocity=self.impulse/capabilities['massKg']
        if np.linalg.norm(self.impulse_velocity)>self.policy['maximum_velocity_change_mps']:
            raise ValueError('Impact requires a fall or another movement family')
        self.direction=math.copysign(1.,components[0] or components[2])
        self.entry=None;self.events=[];self.catches=[];self.decisions=[]
        if spec.get('entry')=='walk':
            entry_walk=deepcopy(recipe['entry_walking'])
            step=capabilities['stepLengthM']*self.policy['entry_step_fraction']
            period=step/(capabilities['preferredSpeedMps']*self.policy['entry_speed_fraction'])
            self.entry=DirectionalSteps(origin,forward,lateral,up,height,lanes,foot_heights,
                [dict(steps=5,turn_degrees=0.,step_length_body_heights=step/height,
                      label='incoming slow walk')],period,turn_stance=self.turn_stance,walking=entry_walk)
            entry_event=self.entry.events[spec['entry_step_index']]
            self.hit=entry_event['start']+.38*entry_event['duration']
            self.events=[dict(e,end=min(e['end'],self.hit)) for e in self.entry.events if e['start']<self.hit]
            center,heading=self.entry.body(self.hit)
            velocity=(self.entry.body(self.hit+.0005)[0]-self.entry.body(self.hit-.0005)[0])/.001
            initial_feet=self.entry.sample(self.hit)['feet']
        else:
            self.hit=self.policy['initial_hold_seconds'];center=np.zeros(3);heading=0.;velocity=np.zeros(3)
            initial_feet={s:dict(position=p.copy(),heading=0.,contact=True,swing_phase=0.,roll_degrees=0.,walk_articulation_scale=1.) for s,p in self.anchors.items()}
        self.hit_center=center.copy();self.initial_feet=deepcopy(initial_feet)
        region=spec['region']; offsets=self.anatomy['applicationOffsetsBodyHeights'][region]
        arm=height*(self.lateral*offsets[0]+self.up*offsets[1]+self.forward*offsets[2])
        if 'application_offset_m' in spec:
            x,y,z=spec['application_offset_m'];arm=self.lateral*x+self.up*y+self.forward*z
        self.application_point=self.origin+center+arm
        self.angular_impulse=float(np.cross(arm,self.impulse)@self.up)
        self.region_gain=1.+abs(offsets[2])
        self.threat=self.origin+center+height*(self.lateral*spec['threat_lateral_forward'][0]+self.forward*spec['threat_lateral_forward'][1])
        self.duration=self.hit+self.policy['recovery_horizon_seconds']+self.policy['ready_hold_seconds']
        b=dict(start=self.hit,end=self.duration-self.policy['ready_hold_seconds'],center=center.copy(),
               delta=np.zeros(3),heading=heading,angle=0.,stationary=False,count=0,length=0.,side=spec['side'],
               direction=self.direction,label=spec['label'],period=self.period,walk_articulation_scale=1.,
               walk_clearance_scale=1.,received_impulse_ns=float(np.linalg.norm(self.impulse)),
               velocity_change_mps=float(np.linalg.norm(self.impulse_velocity)),region=region)
        self.blocks=[b];self.steps=self.events
        self.times=np.arange(self.hit,self.duration+1/240,1/240)
        self.values=[];self.diagnostics=[]; self.channels=np.zeros(5)
        yaw_rate=0.; status='recovering'
        for t in self.times:
            age=t-self.hit; feet=self._feet(t); loads=self._loads(t)
            # Begin the next preparation once the previous catch can bear
            # weight, while its final compression is still settling.
            handover=self.policy.get('next_catch_acceptance_fraction',1.)
            active=next((e for e in self.catches if t<e['touch']+
                         handover*self.policy['acceptance_seconds']),None)
            impulse_remaining=1-smooth(age/self.policy['pulse_seconds'])
            predicted_velocity=velocity+self.impulse_velocity*impulse_remaining
            midpoint=sum(f['position']-self.origin for f in feet.values())/2
            error=center-midpoint;error-=self.up*(error@self.up)
            need=np.linalg.norm(predicted_velocity)>self.policy['settled_speed_mps'] or np.linalg.norm(error)>self.policy['support_error_body_heights']*height
            if age>=self.policy['reaction_seconds'] and active is None and need and t<b['end']-.5:
                airborne=[s for s,f in feet.items() if not f['contact']]
                if airborne:
                    side=airborne[0];reason='redirect available walking swing'
                else:
                    desired=center+predicted_velocity*.40
                    def deficit(s):
                        d=desired+self._lane(heading,s)-(feet[s]['position']-self.origin)
                        d-=self.up*(d@self.up)
                        return float(np.linalg.norm(d))+.015*float((feet[s]['position']-self.origin)@self.lateral)*self.direction
                    scores={s:deficit(s) for s in lanes}
                    # A catch still accepting weight cannot immediately lift again.
                    eligible=[s for s in scores if not any(e['side']==s and t<e['end'] for e in self.catches)]
                    side=max(eligible,key=scores.get);reason='largest reachable support deficit'
                other=next(s for s in lanes if s!=side)
                if len(self.catches)>=self.policy['maximum_catches']:
                    status='requires_fall_or_other_behavior';break
                flight=self.period*self.policy['catch_duration_scales'][min(len(self.catches),3)]*.76
                lift=t if airborne else t+.018
                touch=lift+flight;end=touch+self.policy['acceptance_seconds']
                target_center=center+predicted_velocity*(flight+.18)
                toward=self.threat-(self.origin+center)
                requested=math.atan2(toward@self.lateral,toward@self.forward)
                aim=float(np.clip(requested,-math.radians(self.policy['body_follow_degrees']),math.radians(self.policy['body_follow_degrees'])))
                # Reorient only the recovering foot; body follows accepted support.
                foot_heading=heading+(aim-heading)*smooth(age/.6)
                target=self.origin+target_center+self._lane(foot_heading,side)
                target+=self.up*(foot_heights[side]-target@self.up)
                # Non-crossing placement relative to the current other support.
                axis=self.lateral*math.cos(heading)-self.forward*math.sin(heading)
                sign=math.copysign(1.,lanes[side]); gap=sign*((target-feet[other]['position'])@axis)
                minimum=self.policy['minimum_width_body_heights']*height
                if gap<minimum:target+=axis*sign*(minimum-gap)
                delta=target-feet[side]['position'];delta-=self.up*(delta@self.up)
                reach=self.policy['catch_reach_body_heights']*height
                limited=np.linalg.norm(delta)>reach
                if limited:target=feet[side]['position']+delta*reach/np.linalg.norm(delta)+self.up*(foot_heights[side]-feet[side]['position']@self.up)
                v0=np.zeros(3);a0=np.zeros(3)
                if airborne:
                    eps=.0005
                    p0=self.entry.sample(t-eps)['feet'][side]['position'];p1=self.entry.sample(t)['feet'][side]['position'];p2=self.entry.sample(t+eps)['feet'][side]['position']
                    v0=(p2-p0)/(2*eps);a0=(p2-2*p1+p0)/eps**2
                e=dict(start=t,end=end,duration=end-t,period=self.period,side=side,block=b,index=len(self.catches),inner=False,
                    old=feet[side]['position'].copy(),target=target,oldHeading=feet[side]['heading'],targetHeading=foot_heading,
                    oldSwing=feet[side]['swing_phase'] if airborne else 0.,oldRoll=feet[side]['roll_degrees'],
                    lift=lift,touch=touch,alreadyFree=bool(airborne),label=spec['label']+'/catch '+str(len(self.catches)+1))
                e['curve']=quintic(e['old'],v0,a0,target,touch-lift)
                self.catches.append(e);self.events.append(e);active=e
                self.decisions.append(dict(timeS=float(t),side=side,reason=reason,reachLimited=bool(limited),targetM=target.tolist()))
            # Existing support reacts immediately but a newly accepted catch
            # contributes greater braking authority. Free feet contribute zero.
            accepted={s:0. for s in lanes}
            for e in self.catches:
                accepted[e['side']]=max(accepted[e['side']],smooth((t-e['touch'])/self.policy['acceptance_seconds']))
            catch_load=sum(loads[s]*accepted[s] for s in lanes)
            support=sum(loads[s]*(feet[s]['position']-self.origin) for s in lanes)
            support-=self.up*(support@self.up)
            desired=-velocity/self.policy['braking_response_seconds']+(support-center)*self.policy['support_position_gain']
            capacity=self.policy['existing_support_fraction']+(1-self.policy['existing_support_fraction'])*catch_load
            ax=float(np.clip(desired@self.lateral,-capabilities['lateralAccelerationMps2']*capacity,capabilities['lateralAccelerationMps2']*capacity))
            az=float(np.clip(desired@self.forward,-capabilities['brakingAccelerationMps2']*capacity,capabilities['brakingAccelerationMps2']*capacity))
            reaction=self.lateral*ax+self.forward*az
            dt=1/240
            pulse=(smooth((age+dt)/self.policy['pulse_seconds'])-smooth(age/self.policy['pulse_seconds']))/dt
            acceleration=reaction+self.impulse_velocity*pulse
            supported_heading=sum(loads[s]*feet[s]['heading'] for s in lanes)
            yaw_acc=float(np.clip(8*(supported_heading-heading)-4*yaw_rate,-capabilities['yawBrakingRadps2'],capabilities['yawBrakingRadps2']))
            yaw_acc+=self.angular_impulse/capabilities['yawInertiaKgM2']*pulse
            # Region compliance is authored. Yaw dynamics above uses canonical
            # inertia; roll is not advertised as a solved inertia-axis response.
            severity=np.linalg.norm(self.impulse_velocity)/self.policy['reference_velocity_mps']
            excite=smooth(age/.065)*math.exp(-age/.48)*min(severity,1.5)
            absorb=catch_load*min(1.,np.linalg.norm(velocity)/.5)
            ready=smooth(age/.6)
            targets=np.array([excite*self.region_gain,excite*.7-absorb*.15,absorb,ready,excite])
            taus=np.asarray(self.anatomy['responseSeconds'])
            self.channels+=(targets-self.channels)*(1-np.exp(-dt/taus))
            self.values.append(np.r_[center,velocity,heading,yaw_rate,self.channels])
            self.diagnostics.append(dict(timeS=float(t),velocityMps=velocity.tolist(),reactionAccelerationMps2=reaction.tolist(),catchLoad=float(catch_load),loadShares=loads.copy()))
            center=center+velocity*dt+.5*acceleration*dt*dt;velocity=velocity+acceleration*dt
            heading+=yaw_rate*dt+.5*yaw_acc*dt*dt;yaw_rate+=yaw_acc*dt
        self.times=self.times[:len(self.values)];self.values=np.asarray(self.values)
        if status!='recovering':raise ValueError(status)
        b.update(count=len(self.catches),length=float(np.linalg.norm(center-self.hit_center)),delta=center-self.hit_center,angle=heading)
        final=self._state(self.duration);center=final[:3];velocity=final[3:6];heading=float(final[6])
        self.exit_state=dict(responseChannels=final[8:13].tolist(),supportShares=self.planned_loads(self.duration),stance='alert_recovery',rootOffsetM=center.tolist(),velocityMps=velocity.tolist(),headingRadians=float(heading),
            contacts={s:dict(anchorM=f['position'].tolist(),headingRadians=float(f['heading'])) for s,f in self._feet(self.duration).items()},
            threatTargetM=self.threat.tolist(),injury='not_inferred',status='ready' if np.linalg.norm(velocity)<.1 else 'residual_motion')

    def _lane(self,heading,side):
        return (self.lateral*math.cos(heading)-self.forward*math.sin(heading))*self.lanes[side]

    def _feet(self,time):
        feet=deepcopy(self.entry.sample(min(time,self.hit+self.policy['reaction_seconds']))['feet'] if self.entry else self.initial_feet)
        for e in self.catches:
            if time<e['start']:continue
            s=e['side'];u=float(np.clip((time-e['lift'])/(e['touch']-e['lift']),0,1))
            p=sum(e['curve'][k]*u**k for k in range(6))
            p+=self.up*self.height*self.walking['clearance_body_heights']*64*u**3*(1-u)**3
            feet[s]=dict(position=p,heading=e['oldHeading']+(e['targetHeading']-e['oldHeading'])*smooth(u),
                         contact=bool(time<=e['lift'] and not e['alreadyFree'] or time>=e['touch']),swing_phase=e['oldSwing']+(1-e['oldSwing'])*u if time<e['touch'] else 0.,
                         roll_degrees=(1-smooth(u/.35))*e['oldRoll']+self.walking['heel_roll_degrees']*math.sin(math.pi*u)**2,walk_articulation_scale=1.)
            if self.policy.get('carry_entry_articulation') and e['alreadyFree']:
                # Keep the incoming joint clock independent of the shortened
                # catch trajectory; blend its shape into contact over the flight.
                incoming=self.entry.sample(time)['feet'][s]
                feet[s]['walking_swing_phase']=incoming['swing_phase']
                start_gain=1-smooth((e['start']-self.hit)/self.policy['entry_articulation_blend_seconds'])
                feet[s]['entry_articulation_weight']=start_gain*(1-smooth(u))
        return feet

    def _loads(self,time):
        if self.entry and time<=self.hit+self.policy['reaction_seconds'] and not self.catches:
            from ..solve.turn_support import contact_loads
            return contact_loads(self.entry,time)
        raw={s:1. for s in self.lanes}
        for e in self.catches:
            if time<e['start']:continue
            if e['alreadyFree']:unload=1.
            else:unload=smooth((time-e['start'])/max(.001,e['lift']-e['start']))
            reload=smooth((time-e['touch'])/self.policy['acceptance_seconds'])
            raw[e['side']]*=1-unload*(1-reload)
        feet=self._feet(time)
        for s in raw:
            if not feet[s]['contact']:raw[s]=0.
        total=sum(raw.values())
        if total<=1e-8:raise ValueError('Impact recovery has no grounded support')
        return {s:float(v/total) for s,v in raw.items()}

    def planned_loads(self,time):
        if self.entry and time<self.hit+self.policy['reaction_seconds']:
            from ..solve.turn_support import contact_loads
            return contact_loads(self.entry,time)
        return self._loads(time)

    def _state(self,time):
        return np.array([np.interp(time,self.times,self.values[:,j]) for j in range(self.values.shape[1])])

    def body(self,time):
        if time<self.hit:return self.entry.body(time) if self.entry else (np.zeros(3),0.)
        a=self._state(time);return a[:3],float(a[6])

    def weight(self,time):
        return -sum(math.copysign(v,self.lanes[s]) for s,v in self.planned_loads(time).items())

    def sample(self,time):
        if self.entry and time<self.hit+self.policy['reaction_seconds']:
            sample=self.entry.sample(time)
            if time>=self.hit:sample['center'],sample['heading']=self.body(time)
            return sample
        center,heading=self.body(time)
        return dict(time=time,center=center.copy(),heading=heading,feet=self._feet(time),weight=self.weight(time),
                    label=self.blocks[0]['label'],turn_in_place=False)

    def response(self,time):
        if time<=self.hit:a=np.zeros(13)
        else:a=self._state(time)
        chest,tail,absorb,ready,startle=a[8:13]
        toward=self.threat-(self.origin+a[:3]);bearing=math.atan2(toward@self.lateral,toward@self.forward)
        look=ready*(bearing-a[6])-self.direction*.15*chest
        return dict(roll_radians=-self.direction*math.radians(self.anatomy['pelvisRollDegrees'])*chest,
            drop_m=self.height*(self.policy['compression_body_heights']*(.35*chest+.65*absorb)+self.policy['ready_crouch_body_heights']*ready),
            torso_roll_radians=-self.direction*math.radians(self.anatomy['torsoRollDegrees'])*chest,
            torso_yaw_radians=-self.direction*math.radians(self.anatomy['torsoYawDegrees'])*chest,
            tail_yaw_radians=self.direction*math.radians(self.anatomy['tailYawDegrees'])*tail,
            look_normal_fraction=0.,look_yaw_radians=float(look),arm_guard=float(.9*startle+.22*ready),jaw_startle=float(startle),
            absorption=float(absorb),ready=float(ready))

    def review_receipt(self):
        return dict(method='Fixed 240 Hz reduced horizontal/yaw response. Effective support reactions; authored vertical/regional compliance. Not articulated inverse dynamics.',
            hitTimeS=self.hit,applicationPointM=self.application_point.tolist(),impulseWorldNs=self.impulse.tolist(),
            angularImpulseUpNms=self.angular_impulse,threatTargetM=self.threat.tolist(),decisions=self.decisions,
            exitState=self.exit_state,samples=self.diagnostics)
