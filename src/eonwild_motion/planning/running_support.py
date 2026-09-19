"""Contact-driven sustained running, using a reduced vertical body proxy.

The prescribed support impulse integrates to a periodic body path. It is not
an articulated force solution: footfall timing and joint preferences are authored.
Free feet exert no support, and flight follows the configured gravity exactly.
"""
import math
import numpy as np

from .airborne_gait import build_airborne_plan
from .grounded_gait import smooth
from .swing_transport import transport_progress


class RunningSupportCycle:
    def __init__(self, gait, height, policy):
        self.gait, self.height, self.policy = gait, height, policy
        self.step = gait.step_period_s
        self.contact = 1 - gait.flight_fraction
        self.speed = gait.step_length_body_heights * height / self.step
        self.gravity = policy['gravity_mps2']
        if not (0 < self.gravity <= 20 and 0 <= policy['speed_yield_fraction'] <= .15
                and .05 <= policy['support_ramp_fraction'] <= .4
                and 0 < policy['recovery_peak_fraction'] <= .5):
            raise ValueError('Invalid running support policy')
        # Reference height is a standing-relative authoring choice. All changing
        # vertical motion comes from the integrated support schedule below.
        low = self.vertical(self.contact * .5, offset=False)[0]
        self.vertical_offset = -gait.pelvis_crouch_body_heights * height - low

    def vertical(self, phase, offset=True):
        c, p, g, dt = self.contact, phase % 1, self.gravity, self.step
        width = self.policy['support_ramp_fraction']*c
        def integral(u):
            if u <= 0: return 0.
            if u >= 1: return u-.5
            return 2.5*u**4-3*u**5+u**6
        def double_integral(u):
            if u <= 0: return 0.
            if u >= 1: return .5*u*u-.5*u+1/7
            return .5*u**5-.5*u**6+u**7/7
        a, b = p/width, (p-c+width)/width
        load = (smooth(a)-smooth(b))/(c-width) if p < c else 0.
        impulse = width*(integral(a)-integral(b))/(c-width)
        displacement = width*width*(double_integral(a)-double_integral(b))/(c-width)
        velocity = g*dt*(impulse-p-(1-c)*.5)
        y = g*dt*dt*(displacement-p*p*.5-(1-c)*p*.5)
        return y+(self.vertical_offset if offset else 0.), velocity, g*(load-1), load

    def travel(self, time):
        p, c = (time/self.step) % 1, self.contact
        integral = (p*.5-c*math.sin(2*math.pi*p/c)/(4*math.pi)) if p < c else c*.5
        delta = self.speed*self.policy['speed_yield_fraction']
        return self.speed*time+delta*self.step*(c*p*.5-integral)

    def gather(self, u):
        if not 0 < u < 1:
            return 0.
        peak = self.policy['recovery_peak_fraction']
        a, b = 3., 3.*(1-peak)/peak
        return (u/peak)**a*((1-u)/(1-peak))**b

    def sample(self, time):
        g, step, c = self.gait, self.step, self.contact
        y, vy, ay, load = self.vertical(time/step)
        feet = {}
        for side, offset in [('left',0.),('right',step)]:
            local = (time-offset) % (2*step)
            if min(local,2*step-local) < 1e-10:
                local = 0.
            touchdown = time-local
            anchor = self.travel(touchdown)+g.touchdown_reach_body_heights*self.height
            stance = local < c*step-1e-10
            if stance:
                u, gather, rise = 0., 0., smooth((local/(c*step)-.25)/.75)
                x, h, pitch = anchor, 0., g.push_off_pitch_degrees*rise
                release, pad, toe = pitch, 0., g.toe_flex_degrees*.55*rise
            else:
                u = (local-c*step)/((2-c)*step)
                gather = self.gather(u)
                x = anchor+2*self.speed*self.step*transport_progress(u,g.swing_transport_ramp_fraction)
                h = g.swing_clearance_body_heights*self.height*gather
                release = g.push_off_pitch_degrees*(1-smooth(u/.36))
                pitch = release+g.foot_recovery_pitch_degrees*gather
                pad = self.policy['pad_gather_degrees']*gather
                toe = g.toe_flex_degrees*(gather+.55*(1-smooth(u/.36)))
            feet[side] = dict(contact=stance,touchdown_time_s=touchdown,
                forward_m=x,height_m=h,swing_phase=u,foot_pitch_degrees=pitch,
                stance_roll_pitch_degrees=pitch,stance_roll_swing_pitch_degrees=release,
                pad_pitch_degrees=pad,toe_flex_degrees=toe,
                recovery_shape=gather,distal_endpoint_role='shape_preference',
                recovery_pitch_carrier='authored',support_load_bodyweights=load if stance else 0.)
        support = sum(f['contact'] for f in feet.values())
        return dict(time_s=time,locomotion_time_s=time,review_segment='run',
            root_forward_m=self.travel(time),pelvis_height_offset_m=y,
            pelvis_vertical_velocity_mps=vy,pelvis_vertical_acceleration_mps2=ay,
            support_load_bodyweights=load,stage='FLIGHT' if not support else 'LOAD_AND_PROPEL',
            support_count=support,flight=support==0,feet=feet)

    def plan(self):
        plan = build_airborne_plan(self.gait,self.height)
        plan['samples'] = [self.sample(r['time_s']) for r in plan['samples']]
        plan['segments'] = [dict(name='run',start=2*self.step,end=4*self.step)]
        plan['coordination'] = self.policy
        plan['claims'] = 'Prescribed support impulse and ballistic body proxy; authored articulation, not full-body dynamics.'
        return plan


def support_body_response(cycle, plan, roles, profile, hip_offsets):
    """Continuous regional response, with the same response-time semantics as impact.

    The existing periodic exponential solver carries state through touchdown,
    load, release and flight. No resetting a response at each event.
    """
    from ..solve.airborne_gait import sample_periodic_response
    from ..hashing import sha256_json
    times = np.linspace(0,2*cycle.step,math.ceil(2*cycle.step*480)+1)
    rows = [cycle.sample(t) for t in times]
    loads = np.asarray([r['support_load_bodyweights'] for r in rows])
    velocity = np.asarray([r['pelvis_vertical_velocity_mps'] for r in rows])
    drive = .65*(loads-1)/max(1.,loads.max()-1)+.35*velocity/max(.01,np.max(np.abs(velocity)))
    balance = np.asarray([sum(math.copysign(1.,hip_offsets[s])*f['support_load_bodyweights'] for s,f in r['feet'].items()) for r in rows])
    balance /= max(1.,np.max(np.abs(balance)))
    tau = profile['impactResponse']['responseSeconds']
    query = np.asarray([r['time_s'] % (2*cycle.step) for r in plan['samples']])
    def lag(values, seconds):
        return sample_periodic_response(times,values,seconds,query)
    chest = -cycle.policy['chest_response_degrees']*lag(drive,tau[1])
    neck = -.55*chest
    head = -.4*chest
    roll = math.radians(cycle.policy['pelvis_roll_degrees'])*lag(balance,tau[2])
    lateral = cycle.policy['pelvis_sway_body_heights']*cycle.height*lag(balance,tau[2])
    tails = list(roles.get('tail',[]))
    weights = np.asarray([(i+1)**.6 for i in range(len(tails))]); weights /= max(1.,weights.sum())
    tail = {name:cycle.policy['tail_response_degrees']*weights[i]*lag(drive,tau[1]*(1+.6*i/max(1,len(tails)-1))) for i,name in enumerate(tails)}
    binding = sha256_json(cycle.policy)
    samples = []
    for i,row in enumerate(plan['samples']):
        angles = {roles['chest']:float(chest[i]),roles['head']:float(head[i])}
        angles.update({name:float(neck[i]/len(roles['neck'])) for name in roles.get('neck',[])})
        angles.update({name:float(values[i]) for name,values in tail.items()})
        samples.append(dict(time_s=row['time_s'],support_count=row['support_count'],
            sagittal_node_degrees=angles,body_support_control=dict(
                policy_id='periodic_body_support_control.v1',
                binding_sha256=binding,translation_forward_up_lateral_m=[0.,0.,float(lateral[i])],
                rotation_pitch_roll_yaw_radians=[0.,float(roll[i]),0.])))
    return samples
