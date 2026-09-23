"""Task-space warm starts for walking on straight or constant-curvature paths.

These are declared engineering gait tasks, not predicted dinosaur choreography.
The same OpenSim anatomy/contact/effort model subsequently evaluates and refines
them. Stance anchors live in the world, including on a curved path.
"""
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from .moco_tasks import smooth, rot


def path_frame(t, speed, yaw_rate):
    t = np.asarray(t)
    theta = yaw_rate*t
    rotation = Rotation.from_rotvec(np.stack((np.zeros_like(t), theta, np.zeros_like(t)), axis=-1)).as_matrix()
    if abs(yaw_rate) < 1e-10:
        origin = np.stack((speed*t, np.zeros_like(t), np.zeros_like(t)), axis=-1)
    else:
        origin = np.stack((speed*np.sin(theta)/yaw_rate, np.zeros_like(t), speed*(np.cos(theta)-1)/yaw_rate), axis=-1)
    return origin, rotation


def to_world(q, times, index, speed, rate):
    """Compose the path transform before root pitch/yaw/roll, never after IK."""
    q = np.array(q, copy=True)
    origin, rotation = path_frame(times, speed, rate)
    xyz = [index[n] for n in ('forward', 'height', 'lateral')]
    angles = [index[n] for n in ('pitch', 'yaw', 'roll')]
    q[:, xyz] = origin + np.einsum('tij,tj->ti', rotation, q[:, xyz])
    local = Rotation.from_euler('ZYX', q[:, angles]).as_matrix()
    q[:, angles] = Rotation.from_matrix(rotation@local).as_euler('ZYX')
    return q


def foot_task(problem, t, side):
    task = problem.policy['path_task']
    T, speed = problem.period, problem.speed
    duty, rate = task['duty_factor'], task['yaw_rate_rad_s']
    offset = 0 if side == 'l' else .5
    continuous = t/T+offset
    cycle = np.floor(continuous)
    phase = continuous-cycle
    start = (cycle-offset)*T
    hip_width = abs(problem.admission['points']['leftLeg.0'][2]-problem.admission['points']['rightLeg.0'][2])
    sign = np.sign(problem.admission['points'][('left' if side == 'l' else 'right')+'Leg.0'][2])
    lane = sign*task['half_track_hip_width_ratio']*hip_width
    anchor_time = start+duty*T*.5
    origin0, R0 = path_frame(anchor_time, speed, rate)
    origin1, R1 = path_frame(anchor_time+T, speed, rate)
    anchor0 = origin0+R0@np.array([task['catch_bias_m'],0,lane])
    anchor1 = origin1+R1@np.array([task['catch_bias_m'],0,lane])
    outward = -sign*task['toe_out_radians']
    yaw0 = rate*anchor_time+outward
    swing = max(0., (phase-duty)/(1-duty))
    if phase < duty:
        ramp = float(np.clip((phase/duty-.4)/.6,0,1))
        peel = 6*ramp**3-8*ramp**4+3*ramp**5
        angle = -task['toe_off_radians']*peel
        toe_angle = angle*(1-float(smooth((phase/duty-.35)/.5)))
        anchor = anchor0
        yaw = yaw0
        lift = 0.
    else:
        blend = float(smooth(swing))
        angle = -task['toe_off_radians']*(1-blend)
        release_rate = -task['toe_off_radians']/(.6*duty*T)
        angle += release_rate*(1-duty)*T*(swing-6*swing**3+8*swing**4-3*swing**5)
        toe_angle = -task['recovery_toe_radians']*float(smooth(swing/.22))*(1-float(smooth((swing-.45)/.55)))
        anchor = (1-blend)*anchor0+blend*anchor1
        yaw = yaw0+rate*T*blend
        lift = task['clearance_m']*np.sin(np.pi*swing)**2
    Ry = Rotation.from_rotvec([0,yaw,0]).as_matrix()
    foot_rotation = Ry@rot(angle)
    digit_rotation = Ry@rot(toe_angle)
    geometry = problem.metadata['foot_geometry']
    pivot = np.array(geometry['toe_midpoint_m'])
    front = np.array(geometry['sites'][-1]['center_local_m'])
    front[1] -= geometry['sites'][-1]['radius_m']
    anchor = anchor+np.array([0,lift-task['initial_pad_compression_m'],0])
    distal = anchor-digit_rotation@front
    mtp = distal-foot_rotation@pivot
    return mtp, foot_rotation, toe_angle-angle


def initialize(problem, old_times, old_q, old_period):
    """Fresh feet/support task; reviewed C51 supplies only a warm body posture."""
    task = problem.policy['path_task']
    if not (.5 < task['duty_factor'] < 1 and problem.speed > 0 and problem.admission['step_length_m'] > 0):
        raise ValueError('Grounded walking task requires positive speed/step and overlapping support')
    if not np.isfinite(task['yaw_rate_rad_s']):raise ValueError('Nonfinite path yaw rate')
    problem.period = 2*problem.admission['step_length_m']/problem.speed
    times = np.linspace(0, problem.period, int(task.get('seed_samples',121)))
    old = CubicSpline(old_times,old_q,axis=0,bc_type='periodic')
    q = old(times/problem.period*old_period)
    ix = problem.index
    # Lower cadence does not simply slow a running clip: rebuild leg placement,
    # sole roll, and double support, while reducing the running body excursion.
    for name in problem.names:
        if name.startswith(('hip_','knee_','ankle_','mtp_','digit_')): continue
        mean = np.mean(q[:-1,ix[name]])
        q[:,ix[name]] = mean+task['body_excursion_scale']*(q[:,ix[name]]-mean)
    q[:,ix['forward']] = 0.
    q[:,ix['height']] += task.get('height_offset_m',0.)
    # An authored path-relative attention target, shared across anatomies.
    lead = task['yaw_rate_rad_s']*task['attention_lead_s']
    for name,share in [('chest_yaw',.10),('neck_yaw',.40),('neck_upper_yaw',.35),('head_yaw',.15)]:
        q[:,ix[name]] += lead*share
    errors=[]
    for k,t in enumerate(times[:-1]):
        world = to_world(q[k:k+1], np.array([t]), ix, problem.speed, task['yaw_rate_rad_s'])[0]
        problem.set_state(t,world,np.zeros(len(world)))
        for side in ('l','r'):
            names = ['hip_'+side,'hip_'+side+'_yaw','hip_'+side+'_roll','knee_'+side,'ankle_'+side,'mtp_'+side]
            indices = [ix[n] for n in names]
            coords = [problem.coordinates[i] for i in indices]
            target, orientation, digit = foot_task(problem,t,side)
            toe = problem.model.getBodySet().get('toe_'+side)
            reference = q[k,indices].copy()
            def residual(x):
                for c,value in zip(coords,x): c.setValue(problem.state,float(value),False)
                problem.model.realizePosition(problem.state)
                p=toe.getPositionInGround(problem.state).to_numpy()
                rotation=toe.getTransformInGround(problem.state).R()
                R=np.array([[rotation.get(i,j) for j in range(3)] for i in range(3)])
                return np.r_[(p-target)/problem.L, .4*Rotation.from_matrix(orientation.T@R).as_rotvec(),.002*(x-reference)]
            bounds=np.array([problem.metadata['coordinates'][n]['bounds_rad'] for n in names]).T
            result=least_squares(residual,np.clip(reference,bounds[0]+1e-5,bounds[1]-1e-5),bounds=bounds,max_nfev=40,ftol=1e-8,xtol=1e-8,gtol=1e-8)
            q[k,indices]=result.x
            q[k,ix['digit_'+side]]=digit
            errors.append(float(np.linalg.norm(residual(result.x)[:3])*problem.L))
    q[-1]=q[0]
    problem.metadata['path_cycle'] = dict(duration_s=problem.period,yaw_radians=task['yaw_rate_rad_s']*problem.period,
        translation_m=path_frame(problem.period,problem.speed,task['yaw_rate_rad_s'])[0].tolist(),
        symmetry='full_stride_no_leg_exchange',task=task,seed_max_foot_error_m=max(errors))
    return times,q
