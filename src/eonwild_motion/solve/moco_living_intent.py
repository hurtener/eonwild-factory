"""Authored attention and carriage intent, upstream of shared contact/mechanics.

Irregular interest events are deterministic behavior input, not reconstructed
physiology or random noise. Tail response uses admitted arc length, never a
fixed bone count. The caller must solve contacts and replay forces afterwards.
"""
import numpy as np
from .moco_tasks import smooth
from .moco_joint_spline import to_latent, bounded


def keyed(time, keys):
    if time <= keys[0][0]:
        return float(keys[0][1])
    for (a, x), (b, y) in zip(keys[:-1], keys[1:]):
        if time <= b:
            return float(x+(y-x)*smooth((time-a)/(b-a)))
    return float(keys[-1][1])


class LivingIntent:
    def __init__(self, policy, plan, names, tail_chain, leg_length, bounds=None):
        self.policy=policy; self.plan=plan
        self.bounds=bounds or {}
        self.index={name:i for i,name in enumerate(names)}
        self.chain=tail_chain; self.L=leg_length
        self.duration=plan.specification['duration_s']
        self.period=policy['breath_period_s']
        lengths=np.array([part['length_m'] for part in tail_chain])
        self.fractions=lengths/lengths.sum()
        self.arcs=np.cumsum(self.fractions)-self.fractions/2

    def envelope(self, time):
        ramp=self.policy['boundary_ease_s']
        return float(smooth(time/ramp)*smooth((self.duration-time)/ramp))

    def interest(self, time):
        return keyed(time,self.policy['interest_degrees'])

    def attention(self, time):
        return self.plan.attention_degrees(time)+self.interest(time)

    def breath(self, time):
        # The slower amplitude variation avoids identical breath cycles while
        # keeping the signal smooth and reproducible.
        phase=2*np.pi*time/self.period+.12*np.sin(2*np.pi*time/(self.period*2.7))
        return float(np.sin(phase))

    def apply(self, reference, time):
        q=np.array(reference,copy=True);p=self.policy;ix=self.index
        e=self.envelope(time);rad=np.pi/180
        breath=self.breath(time)
        inspect=keyed(time,p['inspect_pitch_degrees'])
        # Chest follows attention later and by much less; the skull receives
        # the actual attention solve afterwards, so it is not a rigid neck yaw.
        orient=self.attention(max(0,time-p['torso_delay_s']))
        q[ix['chest_yaw']]+=e*rad*p['torso_attention_share']*orient
        q[ix['chest_roll']]+=e*rad*p['torso_roll_degrees']*np.tanh(orient/25)
        chest=e*rad*p['chest_breath_degrees']*breath
        q[ix['chest']]+=chest
        q[ix['neck']]+=e*rad*.58*inspect-.65*chest
        q[ix['neck_upper']]+=e*rad*.24*inspect-.20*chest
        q[ix['head']]+=e*rad*.18*inspect-.15*chest
        # Living tail carriage: low-frequency sweep plus delayed reaction to
        # attention/turning. A wave in curvature travels along the real chain.
        for part,f,arc in zip(self.chain,self.fractions,self.arcs):
            delay=p['tail_base_delay_s']+p['tail_tip_delay_s']*arc
            t=max(0,time-delay)
            sweep=keyed(t,p['tail_sweep_degrees'])
            response=-p['tail_attention_share']*self.attention(t)
            heading_delta=np.degrees(self.plan.heading(t)-self.plan.heading(max(0,t-.55)))
            yaw=sweep+response-p['tail_turn_response']*heading_delta
            density=1.3-.6*arc
            q[ix[part['body']+'_yaw']]+=e*rad*f*density*yaw
            q[ix[part['body']]]+=e*rad*f*p['tail_vertical_degrees']*self.breath(t)*(.65+.35*arc)
        # Apply intent in the same smooth bounded space as the mechanical
        # optimizer. A tiny excursion beyond a stop must not become clipped
        # seed samples followed by a high-acceleration spline correction.
        for name,(lo,hi) in self.bounds.items():
            i=ix[name];delta=q[i]-reference[i]
            if delta:
                q[i]=bounded(to_latent(reference[i],lo,hi)+delta,lo,hi)[0]
        return q
