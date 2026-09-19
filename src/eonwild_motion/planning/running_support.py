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
        if policy.get('articulation_search') not in (None, 'feasible_basins'):
            raise ValueError('Invalid running articulation search')
        if not (0 < self.gravity <= 20 and 0 <= policy['speed_yield_fraction'] <= .15
                and .05 <= policy['support_ramp_fraction'] <= .4
                and 0 < policy['recovery_peak_fraction'] <= .5):
            raise ValueError('Invalid running support policy')
        if policy.get('recovery_path') == 'rear_fold':
            ranges = {'rear_fold_transport_delay': (0., .3),
                      'forward_sweep_clearance_body_heights': (0., .2),
                      'forward_sweep_peak_fraction': (.4, .8),
                      'recovery_hock_back_degrees': (0., 60.),
                      'recovery_pitch_degrees': (-60., 60.)}
            for key, (low, high) in ranges.items():
                value = policy.get(key)
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or not low <= value <= high):
                    raise ValueError('Invalid running recovery policy: '+key)
        if policy.get('tail_response_mode') == 'damped_curvature':
            for key, low, high in [('tail_damping_step_fraction', .05, .5),
                                   ('tail_propagation_step_fraction', 0., 1.)]:
                value = policy.get(key)
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or not low <= value <= high):
                    raise ValueError('Invalid running tail policy: '+key)
        regional = policy.get('regional_body_response')
        fold = policy.get('recovery_fold_window')
        if fold is not None:
            if (not isinstance(fold, list) or len(fold) != 3
                    or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in fold)
                    or not 0 < fold[0] < fold[1] < fold[2] <= 1):
                raise ValueError('Invalid running recovery fold window')
        if regional is not None:
            bounds = {'trunk_yaw_degrees': (0., 12.), 'trunk_roll_degrees': (0., 8.),
                      'breathing_pitch_degrees': (0., 2.), 'tail_yaw_degrees': (0., 30.),
                      'trunk_propagation_step_fraction': (0., .3),
                      'tail_base_weight': (.15, 1.), 'tail_response_time_scale': (.3, 1.)}
            optional = {'tail_lateral_proximal_bias': (0., 6.),
                        'pelvis_yaw_degrees': (0., 8.),
                        'tail_loop_pitch_degrees': (0., 6.),
                        'axial_cycle_phase_radians': (-math.pi, math.pi),
                        'neck_reach_degrees': (0., 10.),
                        'head_yaw_stabilization': (0., 1.)}
            if (not isinstance(regional, dict) or not set(bounds) <= set(regional)
                    or set(regional)-set(bounds)-set(optional)):
                raise ValueError('Invalid regional running response schema')
            for key, (low, high) in (bounds | optional).items():
                if key not in regional:
                    continue
                value = regional[key]
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or not low <= value <= high):
                    raise ValueError('Invalid regional running response: '+key)
        # Reference height is a standing-relative authoring choice. All changing
        # vertical motion comes from the integrated support schedule below.
        low = self.vertical(self.contact * .5, offset=False)[0]
        self.vertical_offset = -gait.pelvis_crouch_body_heights * height - low

    def vertical(self, phase, offset=True):
        c, p, g, dt = self.contact, phase % 1, self.gravity, self.step
        if self.policy.get('support_shape') == 'rounded_impulse':
            # Integrate a finite loading/drive impulse instead of the previous
            # long plateau. Landing and launch share the resulting momentum.
            if p < c:
                load = (1-math.cos(2*math.pi*p/c))/c
                impulse = p/c-math.sin(2*math.pi*p/c)/(2*math.pi)
                displacement = p*p/(2*c)+c*(math.cos(2*math.pi*p/c)-1)/(4*math.pi**2)
            else:
                load, impulse, displacement = 0., 1., p-c*.5
            velocity = g*dt*(impulse-p-(1-c)*.5)
            y = g*dt*dt*(displacement-p*p*.5-(1-c)*p*.5)
            return y+(self.vertical_offset if offset else 0.), velocity, g*(load-1), load
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
                u, gather, fold, rise = 0., 0., 0., smooth((local/(c*step)-.25)/.75)
                x, h, pitch = anchor, 0., g.push_off_pitch_degrees*rise
                release, pad, toe = pitch, 0., g.toe_flex_degrees*.55*rise
            else:
                u = (local-c*step)/((2-c)*step)
                gather = self.gather(u)
                fold = gather
                if self.policy.get('recovery_fold_window'):
                    rise_end, open_start, open_end = self.policy['recovery_fold_window']
                    # Shape can stay collected while its spatial arc continues.
                    # The later release overlaps the approach; no event reset.
                    fold = smooth(u/rise_end)*(1-smooth((u-open_start)/(open_end-open_start)))
                # Fold behind the hip before sweeping forward. This changes the
                # spatial recovery arc, not just an IK angle preference.
                progress = transport_progress(u,g.swing_transport_ramp_fraction)
                if self.policy.get('recovery_path') == 'rear_fold':
                    progress -= self.policy['rear_fold_transport_delay']*gather*(1-u)
                x = anchor+2*self.speed*self.step*progress
                h = g.swing_clearance_body_heights*self.height*gather
                if self.policy.get('recovery_path') == 'rear_fold':
                    # Keep clearance through the forward sweep. An early-only
                    # fold drops the foot while the body is still airborne,
                    # forcing a straight knee before the catch.
                    crest = self.policy['forward_sweep_peak_fraction']
                    sweep = (smooth(u/crest) if u <= crest
                             else 1-smooth((u-crest)/(1-crest)))
                    h += self.policy['forward_sweep_clearance_body_heights']*self.height*sweep
                release = g.push_off_pitch_degrees*(1-smooth(u/.36))
                pitch = release+self.policy.get('recovery_pitch_degrees',g.foot_recovery_pitch_degrees)*fold
                pad = self.policy['pad_gather_degrees']*fold
                toe = g.toe_flex_degrees*(fold+.55*(1-smooth(u/.36)))
            feet[side] = dict(contact=stance,touchdown_time_s=touchdown,
                forward_m=x,height_m=h,swing_phase=u,foot_pitch_degrees=pitch,
                stance_roll_pitch_degrees=pitch,stance_roll_swing_pitch_degrees=release,
                pad_pitch_degrees=pad,toe_flex_degrees=toe,
                recovery_shape=gather,distal_endpoint_role='shape_preference',
                recovery_pitch_carrier='authored',support_load_bodyweights=load if stance else 0.)
            if 'leg_drive' in self.policy:
                shape = self.policy['leg_drive']
                if stance:
                    v = local/(c*step)
                    compression = math.sin(math.pi*min(v/.7,1.))**2
                    opening = smooth(v)
                    knee = shape['landing_knee']-shape['knee_compression']*compression+(shape['release_knee']-shape['landing_knee'])*opening
                    ankle = shape['landing_ankle']-shape['ankle_compression']*compression+(shape['release_ankle']-shape['landing_ankle'])*opening
                else:
                    knee = shape['release_knee']-(shape['release_knee']-shape['gathered_knee'])*fold+(shape['landing_knee']-shape['release_knee'])*smooth(u)
                    ankle = shape['release_ankle']-(shape['release_ankle']-shape['gathered_ankle'])*fold+(shape['landing_ankle']-shape['release_ankle'])*smooth(u)
                feet[side]['running_leg_shape'] = dict(knee_interior_degrees=knee,ankle_interior_degrees=ankle)
                if self.policy.get('articulation_search') == 'feasible_basins':
                    feet[side]['running_leg_shape']['search_feasible_basins'] = True
                feet[side]['leg_heading_degrees'] = self.policy['leg_heading_degrees']
                if self.policy.get('recovery_path') == 'rear_fold':
                    feet[side]['running_leg_shape']['metatarsus_min_degrees'] = -5.-self.policy['recovery_hock_back_degrees']*fold
                    feet[side]['running_leg_shape']['pitch_preference_weight'] = .15
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
    pelvis_yaw = np.zeros(len(query))
    lateral = cycle.policy['pelvis_sway_body_heights']*cycle.height*lag(balance,tau[2])
    tails = list(roles.get('tail',[]))
    weights = np.asarray([(i+1)**.6 for i in range(len(tails))]); weights /= max(1.,weights.sum())
    if cycle.policy.get('tail_response_mode') == 'damped_curvature':
        # Two first-order responses have no resonant overshoot. Drive with
        # body travel, not the sharp contact-force peak that kicked the base.
        displacement = np.asarray([r['pelvis_height_offset_m'] for r in rows])
        displacement -= displacement.mean()
        displacement /= max(.001,np.max(np.abs(displacement)))
        base_response = sample_periodic_response(times,displacement,
            cycle.policy['tail_damping_step_fraction']*cycle.step,times)
        base_response = sample_periodic_response(times,base_response,
            cycle.policy['tail_damping_step_fraction']*cycle.step,times)
        fractions = np.linspace(0,1,len(tails))
        regional = cycle.policy.get('regional_body_response', {})
        weights = regional.get('tail_base_weight', .15)+np.sin(.5*math.pi*fractions)**2
        weights /= weights.sum()
        tail = {}
        for i,name in enumerate(tails):
            fraction = fractions[i]
            delayed = (query-cycle.policy['tail_propagation_step_fraction']*cycle.step*fraction) % (2*cycle.step)
            response = sample_periodic_response(times,base_response,
                tau[1]*(1+fraction)*regional.get('tail_response_time_scale', 1.),delayed)
            tail[name] = cycle.policy['tail_response_degrees']*weights[i]*response
    elif cycle.policy.get('tail_propagation_step_fraction') is not None:
        # Responsive heavy base with delayed curvature along the chain.
        # Previously amplitude favored the tip and phases barely differed.
        weights = np.exp(-1.8*np.linspace(0,1,len(tails))); weights /= weights.sum()
        tail = {}
        for i,name in enumerate(tails):
            fraction = i/max(1,len(tails)-1)
            delayed = (query-cycle.policy['tail_propagation_step_fraction']*cycle.step*fraction) % (2*cycle.step)
            response = sample_periodic_response(times,drive,tau[0]+(tau[1]-tau[0])*fraction,delayed)
            tail[name] = cycle.policy['tail_response_degrees']*weights[i]*response
    else:
        tail = {name:cycle.policy['tail_response_degrees']*weights[i]*lag(drive,tau[1]*(1+.6*i/max(1,len(tails)-1))) for i,name in enumerate(tails)}
    regional_pitch, regional_axial = {}, {}
    regional = cycle.policy.get('regional_body_response')
    if regional is not None:
        # The trunk bends through the spine into the shoulders. Alternating
        # support drives roll and yaw; vertical load drives pitch. No event
        # resets or extra leg motion. Breath is an authored effort cue.
        trunk = list(roles.get('spine', [])) + [roles['chest']]
        if len(trunk) < 2 or len(set(trunk)) != len(trunk):
            raise ValueError('Regional running response needs a unique spine/chest chain')
        alternating = sample_periodic_response(times, balance, tau[2], times)
        alternating = sample_periodic_response(times, alternating, .1*cycle.step, times)
        phase = math.pi*times/cycle.step-regional.get('axial_cycle_phase_radians', 0.)
        axial_cycle = 'tail_loop_pitch_degrees' in regional
        if axial_cycle:
            # One lateral cycle per stride, two restrained vertical lobes.
            # Pelvis and tail share a stride clock; response delay comes from
            # the animal profile and increases along the semantic tail chain.
            alternating = np.sin(phase)
            pelvis_yaw = math.radians(regional.get('pelvis_yaw_degrees', 0.))*lag(alternating,tau[2])
        breathing = np.sin(math.pi*times/cycle.step-.65)
        fractions = np.linspace(0., 1., len(trunk))
        weights = np.linspace(.6, 1.4, len(trunk)); weights /= weights.sum()
        trunk_pitch = np.zeros(len(query)); trunk_roll = np.zeros(len(query)); trunk_yaw = np.zeros(len(query))
        for name, fraction, weight in zip(trunk, fractions, weights):
            delayed = (query-regional['trunk_propagation_step_fraction']*cycle.step*fraction) % (2*cycle.step)
            pitch = -cycle.policy['chest_response_degrees']*sample_periodic_response(times, drive, tau[1], delayed)
            pitch += regional['breathing_pitch_degrees']*sample_periodic_response(times, breathing, tau[1], delayed)
            side = sample_periodic_response(times, alternating, .035*cycle.step, delayed)
            regional_pitch[name] = weight*pitch
            regional_axial[name] = (weight*regional['trunk_roll_degrees']*side, weight*regional['trunk_yaw_degrees']*side)
            trunk_pitch += regional_pitch[name]
            trunk_roll += regional_axial[name][0]; trunk_yaw += regional_axial[name][1]
        # Partial stabilization retains follow-through at the neck root and
        # leaves the head riding the body instead of pinning it in space.
        for name in roles.get('neck', []):
            regional_pitch[name] = -.5*trunk_pitch/len(roles['neck'])
            regional_axial[name] = (-.5*trunk_roll/len(roles['neck']), -.55*trunk_yaw/len(roles['neck']))
        regional_pitch[roles['head']] = -.15*trunk_pitch
        regional_axial[roles['head']] = (-.15*trunk_roll, -.15*trunk_yaw)
        if 'head_yaw_stabilization' in regional:
            # Include pelvic rotation in the counter-bend. Compensating only
            # trunk yaw leaves the skull sweeping with every pelvic drive.
            counter = -regional['head_yaw_stabilization']*(trunk_yaw+np.degrees(pelvis_yaw))
            for name in roles.get('neck', []):
                regional_axial[name] = (regional_axial[name][0], .85*counter/len(roles['neck']))
            regional_axial[roles['head']] = (regional_axial[roles['head']][0], .15*counter)
        neck_names = list(roles.get('neck', []))
        if len(neck_names) > 1 and regional.get('neck_reach_degrees'):
            neck_weights = np.linspace(1., -1., len(neck_names))
            neck_weights /= np.sum(np.maximum(neck_weights, 0.))
            reach = regional['neck_reach_degrees']*lag(np.sin(2*phase-.7),tau[0])
            for name, weight in zip(neck_names, neck_weights):
                regional_pitch[name] += weight*reach
        tail_fractions = np.linspace(0.,1.,len(tails))
        if 'tail_lateral_proximal_bias' in regional:
            # Normalized chain fraction transfers the proximal emphasis to
            # different tail counts; no fixed bone names or species branch.
            tail_weights = .25+np.exp(-regional['tail_lateral_proximal_bias']*tail_fractions)
        else:
            tail_weights = .6+np.sin(.5*math.pi*tail_fractions)**2
        tail_weights /= tail_weights.sum()
        for i, name in enumerate(tails):
            fraction = i/max(1,len(tails)-1)
            delayed = (query-cycle.policy['tail_propagation_step_fraction']*cycle.step*fraction) % (2*cycle.step)
            side = sample_periodic_response(times, alternating, tau[1]*(.5+fraction), delayed)
            regional_axial[name] = (np.zeros(len(query)), -regional['tail_yaw_degrees']*tail_weights[i]*side)
            if axial_cycle:
                tail[name] = regional['tail_loop_pitch_degrees']*tail_weights[i]*sample_periodic_response(
                    times, np.sin(2*phase), tau[1]*(.5+fraction), delayed)
    binding = sha256_json(cycle.policy)
    samples = []
    for i,row in enumerate(plan['samples']):
        angles = {roles['chest']:float(chest[i]),roles['head']:float(head[i])}
        angles.update({name:float(neck[i]/len(roles['neck'])) for name in roles.get('neck',[])})
        angles.update({name:float(values[i]) for name,values in tail.items()})
        angles.update({name:float(values[i]) for name,values in regional_pitch.items()})
        samples.append(dict(time_s=row['time_s'],support_count=row['support_count'],
            sagittal_node_degrees=angles,body_support_control=dict(
                policy_id='periodic_body_support_control.v1',
                binding_sha256=binding,translation_forward_up_lateral_m=[0.,0.,float(lateral[i])],
                rotation_pitch_roll_yaw_radians=[0.,float(roll[i]),float(pelvis_yaw[i])])))
        if regional is not None:
            samples[-1]['node_roll_yaw_degrees'] = {name:[float(r[i]),float(y[i])] for name,(r,y) in regional_axial.items()}
    return samples
