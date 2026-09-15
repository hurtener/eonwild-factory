"""Current-rig running choreography over the shared airborne gait family.

Speeds and stride are authored animal inputs, not mass-derived biology.
The cyclic gait owns loading, push-off and recovery; consumers own entry state.
"""
import math
from copy import deepcopy
from .airborne_gait import AirborneGait, sample_airborne_gait, build_airborne_plan
from .grounded_gait import smooth


def resolve_running(profile, recipe):
    values = profile['locomotion']['run']
    for key, unit in [('preferredSpeed', 'm/s'), ('stepLength', 'm'), ('sameFootStride', 'm')]:
        item = values[key]
        if (item['unit'] != unit or isinstance(item['value'], bool)
                or not math.isfinite(item['value']) or item['value'] <= 0
                or not item.get('source', {}).get('citation')):
            raise ValueError('Invalid running input: ' + key)
    speed, step, stride = (values[k]['value'] for k in ('preferredSpeed', 'stepLength', 'sameFootStride'))
    if not math.isclose(stride, 2 * step):
        raise ValueError('A running stride must contain two alternating steps')
    height = profile['authoring']['bodyHeightM']
    reach_fraction = recipe.get('touchdown_reach_step_fraction', .5)
    if (isinstance(reach_fraction, bool) or not isinstance(reach_fraction, (int, float))
            or not math.isfinite(reach_fraction)
            or not 0 < reach_fraction < 1):
        raise ValueError('Running touchdown reach must be a fraction of one step')
    return AirborneGait(**recipe['parameters'], step_period_s=step / speed,
                       step_length_body_heights=step / height,
                       touchdown_reach_body_heights=reach_fraction * step / height)


def running_sample(gait, time_s, height):
    row = sample_airborne_gait(gait, time_s, height)
    for foot in row['feet'].values():
        u = foot['swing_phase']
        # The distal pad continues heel release while the metatarsal folds.
        # Its shape is never flattened simply because the animal is airborne.
        foot['distal_endpoint_role'] = 'shape_preference'
        foot['recovery_pitch_carrier'] = 'authored'
        if not foot['contact']:
            # Finish release while gathering; start opening the entire foot
            # before the leg reaches forward. No second fold on approach.
            gather = smooth(u / .28) * (1 - smooth((u - .28) / .52))
            foot['stance_roll_swing_pitch_degrees'] = gait.push_off_pitch_degrees * (1 - smooth(u / .30))
            foot['foot_pitch_degrees'] = foot['stance_roll_swing_pitch_degrees'] + gait.foot_recovery_pitch_degrees * gather
            foot['pad_pitch_degrees'] = 20 * gather
            foot['toe_flex_degrees'] = gait.toe_flex_degrees * (.55 * (1-smooth(u/.3)) + gather)
            # Running coordinates recovery through the hip objective and
            # foot trajectory. An additional world-metatarsal target held
            # the ankle at its flexion limit while the knee kept moving.
    return row


def _ramp_integral(u):
    u = max(0., min(1., u))
    return u**4 * (2.5 + u * (-3 + u))


def running_adjustment_sample(gait, time_s, height, *, kind, walking_speed, side='left'):
    """A short entry or retained-support braking catch, in current gait units.

    This owns placement and support, rather than slowing a walking stop.
    Left/right variants let the consumer enter at the next available landing.
    Authored kinematics, not a force or biological reconstruction.
    """
    if kind not in ('entry', 'brake') or side not in ('left', 'right'):
        raise ValueError('Unknown running adjustment')
    step = gait.step_period_s
    speed = gait.step_length_body_heights * height / step
    t = max(0., time_s)
    row = running_sample(gait, t, height)
    if kind == 'entry':
        ramp = .95 * step
        def travel(clock):
            if clock <= 0: return walking_speed * clock
            u = min(1., clock / ramp)
            return walking_speed * min(clock,ramp) + (speed-walking_speed)*ramp*_ramp_integral(u) + speed*max(0.,clock-ramp)
        def anchor(clock):
            velocity = walking_speed+(speed-walking_speed)*smooth(clock/ramp)
            return travel(clock)+gait.touchdown_reach_body_heights*height*velocity/speed
        row['root_forward_m'] = travel(t)
        for f in row['feet'].values():
            a = f['touchdown_time_s']
            progress = (f['forward_m']-(speed*a+gait.touchdown_reach_body_heights*height))/(2*speed*step)
            f['forward_m'] = anchor(a)+(anchor(a+2*step)-anchor(a))*progress
        gain = .65+.35*smooth(t/ramp)
        row['pelvis_height_offset_m'] *= gain
        row['performance_gain'] = gain
    else:
        duration = 1.35*step
        u = min(1.,t/duration)
        distance = speed*duration*(u-_ramp_integral(u))
        final_distance = .5*speed*duration
        row['root_forward_m'] = distance
        # Keep the first catch loaded. Bring the returning foot into a useful
        # staggered support; it never takes a cosmetic step backward afterward.
        anchor = gait.touchdown_reach_body_heights*height
        initial = running_sample(gait,0,height)
        first = deepcopy(initial['feet']['left'])
        first.update(forward_m=anchor,contact=True,height_m=0.,foot_pitch_degrees=0.,
                     stance_roll_pitch_degrees=0.,toe_flex_degrees=0.,swing_phase=0.)
        catch = .86*step
        v = min(1.,t/catch)
        other = deepcopy(initial['feet']['right'])
        x0 = other['forward_m']; y0 = other['height_m']
        # Preserve incoming travel at entry, decelerating smoothly into contact.
        eps=1e-5
        next_foot=running_sample(gait,eps,height)['feet']['right']
        vx=(next_foot['forward_m']-x0)/eps;vy=(next_foot['height_m']-y0)/eps
        target=final_distance+.06*height
        base=smooth(v)
        velocity_carrier=v*(1-v)**3*(1+3*v)
        other['forward_m']=x0+(target-x0)*base+vx*catch*velocity_carrier
        other['height_m']=max(0.,y0*(1-base)+vy*catch*velocity_carrier)
        other.update(contact=t>=catch,swing_phase=(initial['feet']['right']['swing_phase']+(1-initial['feet']['right']['swing_phase'])*v) if t<catch else 0.)
        open_gain=1-smooth(v/.8)
        for key in ('foot_pitch_degrees','stance_roll_swing_pitch_degrees','pad_pitch_degrees','toe_flex_degrees'):
            other[key]=initial['feet']['right'].get(key,0.)*open_gain
        other['articulation_scale']=open_gain
        row['feet']={'left':first,'right':other}
        # One continuous loading/settling response, without cyclic run bounce.
        initial_y=initial['pelvis_height_offset_m']
        settle=smooth(t/(1.8*step))
        row['pelvis_height_offset_m']=initial_y*(1-settle)-.025*height*settle-.024*height*math.sin(math.pi*u)**2
        row['performance_gain']=1-smooth(t/(1.8*step))
        row['stage']='RUN_BRAKING_CATCH' if t<catch else 'RUN_SETTLE'
    if side=='right': row['feet']={'left':row['feet']['right'],'right':row['feet']['left']}
    row['support_count']=sum(f['contact'] for f in row['feet'].values())
    row['flight']=row['support_count']==0
    row['locomotion_time_s']=t
    return row


def build_running_review_plan(gait, height, walking_speed):
    plan=build_airborne_plan(gait,height)
    plan['samples']=[running_sample(gait,r['time_s'],height) for r in plan['samples']]
    cycle=2*gait.step_period_s
    plan['segments']=[dict(name='run',start=cycle,end=2*cycle)]
    # Non-adjacent source intervals are separate segments, never played over
    # their inter-clip gaps. The runtime adopts actual state at each entry.
    for kind in ('entry','brake'):
        for side in ('left','right'):
            start=plan['samples'][-1]['time_s']+1/gait.sample_hz
            duration=(2 if kind=='entry' else 1.8)*gait.step_period_s
            count=math.ceil(duration*gait.sample_hz)
            times={duration*i/count for i in range(count+1)}
            if kind=='brake':times.update((.86*gait.step_period_s,1.35*gait.step_period_s))
            else:times.update((gait.step_period_s,(1-gait.flight_fraction)*gait.step_period_s,(2-gait.flight_fraction)*gait.step_period_s))
            unique=[]
            for t in sorted(times):
                if not unique or t-unique[-1]>1e-7:unique.append(t)
            for t in unique:
                row=running_adjustment_sample(gait,t,height,kind=kind,walking_speed=walking_speed,side=side)
                row['time_s']=start+t
                row['locomotion_time_s']=t%cycle
                row['review_segment']='run'+kind.title()+side.title()
                plan['samples'].append(row)
            plan['segments'].append(dict(name='run'+kind.title()+side.title(),start=start,end=start+duration))
    for row in plan['samples']:
        row.setdefault('locomotion_time_s',row['time_s']%cycle)
        row.setdefault('review_segment','run')
    plan['duration_s']=plan['samples'][-1]['time_s']
    plan['program']='gait_transition'
    return plan
