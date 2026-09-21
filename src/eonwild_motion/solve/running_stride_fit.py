"""Offline periodic leg fit with reduced sagittal inverse dynamics.

The first mode fits metatarsal redundancy with fixed body/foot tasks. The
floating-body mode couples bilateral joint paths, free-foot recovery and a
reduced torso through mass and angular momentum. Neither estimates measured
muscle forces. Segment masses and inertias are explicit engineering priors.
"""
from copy import deepcopy
import math
import numpy as np
from scipy.interpolate import CubicSpline, PchipInterpolator
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix

from ..errors import ContractError
from .airborne_gait import solve_airborne_plan_sample


def periodic_derivatives(times, period):
    """Three-point physical-time derivatives on a nonuniform periodic grid."""
    t = np.asarray(times, dtype=float)
    if len(t) < 8 or not np.isfinite(t).all() or np.any(np.diff(t) <= 0) or period <= t[-1]-t[0]:
        raise ContractError('stride fit requires an ordered open periodic grid')
    before = (t-np.roll(t, 1)) % period
    after = (np.roll(t, -1)-t) % period
    d1, d2 = np.zeros((len(t), len(t))), np.zeros((len(t), len(t)))
    for i, (a, b) in enumerate(zip(before, after)):
        ids = [(i-1) % len(t), i, (i+1) % len(t)]
        d1[i, ids] = [-b/(a*(a+b)), (b-a)/(a*b), a/(b*(a+b))]
        d2[i, ids] = [2/(a*(a+b)), -2/(a*b), 2/(b*(a+b))]
    return d1, d2


def inverse_dynamics(points, forces, segment_masses, gravity, d2):
    """Planar Newton-Euler moments, including moving segment COM and inertia.

    points: time x hip/knee/ankle/toe-base x forward/up. External force is
    applied at the toe base (a reduced contact approximation). The pelvis
    reaction is unconstrained; this does not certify whole-body equilibrium.
    """
    p = np.asarray(points)
    segments = np.diff(p, axis=1)
    centers = .5*(p[:, :-1]+p[:, 1:])
    acceleration = np.einsum('ij,jkl->ikl', d2, centers)
    acceleration[:, :, 1] += gravity
    inertial = acceleration*np.asarray(segment_masses)[None, :, None]
    angles = np.unwrap(np.arctan2(segments[:, :, 1], segments[:, :, 0]), axis=0)
    inertia = np.sum(segments**2, axis=2)*np.asarray(segment_masses)[None, :]/12
    rotation = (d2@angles)*inertia
    cross = lambda a,b: a[..., 0]*b[..., 1]-a[..., 1]*b[..., 0]
    torque = np.empty((len(p), 3))
    for joint in range(3):
        torque[:, joint] = (cross(centers[:, joint:]-p[:, joint, None], inertial[:, joint:]).sum(axis=1)
            + rotation[:, joint:].sum(axis=1)-cross(p[:, -1]-p[:, joint], forces))
    return torque


def fit_running_stride(context, plan, response, cycle, profile, policy):
    """Fit both anatomical legs with one shared objective, then freeze curves."""
    if policy.get('model') not in (None,'floating_body'):
        raise ContractError('unknown stride dynamics model')
    if policy.get('model') == 'floating_body':
        return fit_floating_body_stride(context, plan, cycle, profile, policy)
    period = 2*cycle.step
    # Same uniform analysis clock for both animals, independent of emission
    # knots. Interpolate target corrections from the fresh source solve only.
    count = policy['samples_per_stride']
    if isinstance(count, bool) or not isinstance(count, int) or not 24 <= count <= 256:
        raise ContractError('invalid stride sample count')
    for name in ('reference_weight','acceleration_weight','jerk_weight','effort_weight','effort_rate_weight'):
        v = policy[name]
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0 <= v <= 10:
            raise ContractError('invalid stride objective weight: '+name)
    times = np.arange(count)*period/count
    source_t = np.asarray([r['time_s'] for r in plan['samples']])
    rows, bodies = [], []
    from ..planning.running_support import support_body_response
    for t in times:
        row = cycle.sample(float(t))
        for side in context.legs:
            target = np.array([r['feet'][side]['world_foot_target_m'] for r in plan['samples']])
            row['feet'][side]['world_foot_target_m'] = [float(np.interp(t, source_t, target[:, k])) for k in range(3)]
        rows.append(row)
    local_plan = dict(plan, samples=rows)
    bodies = support_body_response(cycle, local_plan, context.roles, profile, context.hip_offsets)
    grid = np.linspace(-45., 85., 261)
    samples = {side: [] for side in context.legs}
    def observe(side, hip, evaluate, best):
        points, valid = [], []
        for angle in grid:
            c = evaluate(float(angle))
            points.append([hip, c[4], c[5], c[2]])
            valid.append(c[6] < 1e-7 and c[7] < 1e-7)
        samples[side].append((np.asarray(points), np.asarray(valid), best[-1]))
    for row, body in zip(rows, bodies):
        solve_airborne_plan_sample(context, row, body_response_sample=body, leg_candidate_observer=observe)
    d1, d2 = periodic_derivatives(times, period)
    omega = 2*math.pi/period
    mass = profile['authoring']['animalInstance']['measurements']['body_mass']['value']
    fractions = np.asarray(policy['segment_mass_fractions'])
    if fractions.shape != (3,) or not np.isfinite(fractions).all() or np.any(fractions <= 0) or fractions.sum() >= .3:
        raise ContractError('invalid reduced limb mass fractions')
    gravity = cycle.gravity
    curves, receipts = {}, {}
    root_travel = np.array([r['root_forward_m']-cycle.speed*t for r,t in zip(rows,times)])
    body_ax = d2@root_travel
    for side, values in samples.items():
        xyz = np.stack([v[0] for v in values], axis=1) # pitch x time x point x xyz
        pts = np.stack((xyz@context.forward, xyz@context.up), axis=-1)
        # Remove constant travel so differentiating around the loop does not
        # invent a root reset impulse. Constant velocity has zero acceleration.
        pts[:, :, :, 0] -= cycle.speed*times[None, :, None]
        table = PchipInterpolator(grid, pts, axis=0)
        lower, upper, seed = [], [], []
        for _, valid, initial in values:
            ids = np.flatnonzero(valid)
            if not len(ids):
                raise ContractError('no feasible sampled articulation basin')
            groups = np.split(ids, np.flatnonzero(np.diff(ids)>1)+1)
            group = min(groups, key=lambda g: min(abs(grid[g]-initial)))
            if len(group) < 5:
                raise ContractError('stride articulation basin too narrow')
            lo, hi = grid[group[0]]+.75, grid[group[-1]]-.75
            lower.append(lo); upper.append(hi); seed.append(np.clip(initial, lo, hi))
        seed = np.array(seed)
        loads = np.array([r['feet'][side]['support_load_bodyweights'] for r in rows])
        contact = np.array([r['feet'][side]['contact'] for r in rows])
        forces = mass*np.column_stack((np.where(contact,body_ax,0),gravity*loads))
        chain = context.legs[side]
        length = sum(float(np.linalg.norm(context.base_w[b][:3,3]-context.base_w[a][:3,3])) for a,b in zip(chain,chain[1:]))
        scale = mass*gravity*length
        coeff = table.c
        def geometry(x):
            j = np.clip(np.searchsorted(grid,x)-1,0,len(grid)-2)
            delta = (x-grid[j])[:,None,None]
            c = coeff[:, j, np.arange(count)]
            return ((c[0]*delta+c[1])*delta+c[2])*delta+c[3]
        def quantities(x):
            p = geometry(x)
            segment = np.diff(p,axis=1)
            theta = np.unwrap(np.arctan2(segment[:,:,0],-segment[:,:,1]),axis=0)
            q = np.column_stack((theta[:,0],theta[:,1]-theta[:,0],theta[:,2]-theta[:,1]))
            torque = inverse_dynamics(p,forces,mass*fractions,gravity,d2)/scale
            return p,q,torque
        _,q0,tau0 = quantities(seed)
        # Weights are engineering regularization, not inferred dinosaur
        # preferences. The seed is freshly generated; no historical clip input.
        def residual(x):
            _,q,tau = quantities(x)
            blocks = [policy['reference_weight']*(q-q0),
                      policy['acceleration_weight']*(d2@q)/omega**2,
                      policy['jerk_weight']*(d1@d2@q)/omega**3,
                      policy['effort_weight']*tau,
                      policy['effort_rate_weight']*(d1@tau)/omega]
            return np.concatenate([b.ravel() for b in blocks])
        sparsity = lil_matrix((count*3*5,count),dtype=int)
        for block in range(5):
            for i in range(count):
                for j in range(-3,4):
                    sparsity[block*count*3+i*3:block*count*3+i*3+3,(i+j)%count]=1
        initial_cost = float(residual(seed)@residual(seed))
        result = least_squares(residual,seed,bounds=(lower,upper),jac_sparsity=sparsity.tocsr(),
            max_nfev=policy['max_evaluations'],ftol=1e-5,xtol=1e-5,gtol=1e-5)
        if not np.isfinite(result.x).all():
            raise ContractError('nonfinite stride fit')
        curve = CubicSpline(np.r_[times,period],np.r_[result.x,result.x[0]],bc_type='periodic')
        curves[side] = curve
        _,q,tau = quantities(result.x)
        receipts[side] = dict(optimizer_success=bool(result.success),message=result.message,
            evaluations=result.nfev,initial_objective=initial_cost,final_objective=float(result.fun@result.fun),
            initial_acceleration_rms=float(np.sqrt(np.mean((d2@q0)**2))),
            fitted_acceleration_rms=float(np.sqrt(np.mean((d2@q)**2))),
            initial_torque_rms_nm=float(scale*np.sqrt(np.mean(tau0**2))),
            fitted_torque_rms_nm=float(scale*np.sqrt(np.mean(tau**2))),
            times_s=times.tolist(),seed_pitch_degrees=seed.tolist(),fitted_pitch_degrees=result.x.tolist(),
            fitted_joint_torque_nm=(tau*scale).tolist(),segment_masses_kg=(mass*fractions).tolist())
        print('STRIDE_FIT',side,'objective',round(initial_cost,3),'->',round(result.fun@result.fun,3),'evaluations',result.nfev,flush=True)
    for row in plan['samples']:
        for side, curve in curves.items():
            row['feet'][side]['stride_fitted_pitch_degrees'] = float(curve(row['time_s']%period))
    return dict(schema='eonwild.periodic-leg-fit.v1',policy=deepcopy(policy),legs=receipts,
        classification='Whole-stride articulation optimization with reduced sagittal inverse dynamics; prescribed body, foot path and contact schedule. No muscle, full-body equilibrium or measured dinosaur claim.',
        limitations=['Segment mass fractions and rod inertias are engineering priors.',
            'Ground reaction applied at toe base; distal toe inertia and moving pressure center omitted.',
            'Prior joint shape is a weak reference from the freshly generated shared source plan.',
            'Final material correction and emitted hard bounds must be measured after fitting.'])


def floating_body_geometry(angles, lengths, hip_offsets, com, fractions):
    """Exact COM reconstruction for a point torso plus two three-rod legs.

    Inputs use time, side, segment, forward/up. The torso holds the remaining
    mass at the bilateral hip center. This is a reduced model COM, not the
    measured COM of the rendered animal. Segment lengths are constant.
    """
    vectors = lengths[None, :, :, None]*np.stack((np.sin(angles), -np.cos(angles)), axis=-1)
    local = np.concatenate((hip_offsets[:, :, None, :],
        hip_offsets[:, :, None, :]+np.cumsum(vectors, axis=2)), axis=2)
    centers = .5*(local[:, :, :-1]+local[:, :, 1:])
    weighted = np.sum(centers*np.asarray(fractions)[None, None, :, None], axis=(1,2))
    body = com-weighted
    return body, local+body[:, None, None, :]


def reduced_angular_momentum(points, body, com, pitch, fractions, body_inertia, d1):
    """Angular momentum / total mass about the reduced model COM."""
    centers = .5*(points[:, :, :-1]+points[:, :, 1:])
    r = centers-com[:, None, None, :]
    v = np.einsum('ij,jskl->iskl', d1, r)
    cross = lambda a,b: a[...,0]*b[...,1]-a[...,1]*b[...,0]
    orbital = (cross(r,v)*np.asarray(fractions)[None,None,:]).sum(axis=(1,2))
    vectors = np.diff(points,axis=2)
    theta = np.unwrap(np.arctan2(vectors[:,:,:,1],vectors[:,:,:,0]),axis=0)
    inertia = np.sum(vectors*vectors,axis=3)*np.asarray(fractions)[None,None,:]/12
    spin = (inertia*np.einsum('ij,jsk->isk',d1,theta)).sum(axis=(1,2))
    rbody = body-com
    return orbital+spin+(1-2*sum(fractions))*cross(rbody,d1@rbody)+body_inertia*(d1@pitch)



def distributed_body_geometry(angles, lengths, hip_offsets, com, fractions, axial_local, axial_fractions, pitch):
    """Point-mass axial regions plus rod legs; exact reduced mass closure."""
    body, points = floating_body_geometry(angles, lengths, hip_offsets, com, fractions)
    c, sn = np.cos(pitch)[:, None], np.sin(pitch)[:, None]
    rotated = np.stack((c*axial_local[..., 0]-sn*axial_local[..., 1],
                        sn*axial_local[..., 0]+c*axial_local[..., 1]), axis=-1)
    offset = (rotated*axial_fractions[None, :, None]).sum(axis=1)
    body = body-offset
    return body, points-offset[:, None, None, :], body[:, None, :]+rotated


def actuator_demand(torque, joint_angles, angle_rates, d1, policy):
    """Required signed joint-actuator activation and first-order excitation.

    Capacity is an engineering torque-angle-speed envelope, NOT identified
    muscle physiology. Demand is never clipped: infeasibility stays visible.
    Torque input/capacity is normalized by bodyweight times leg length.
    """
    peak = np.asarray(policy['peak_torque_bodyweight_leglength'])
    speed = np.asarray(policy['speed_scale_radians_s'])
    center = np.radians(policy['optimal_angles_degrees'])
    width = np.radians(policy['angle_width_degrees'])
    capacity = peak*(.65+.35*np.exp(-((joint_angles-center)/width)**2))/(1+(angle_rates/speed)**2)
    activation = torque/capacity
    excitation = activation+policy['activation_time_s']*np.einsum('ij,jsk->isk',d1,activation)
    return activation, excitation, capacity

def fit_floating_body_stride(context, plan, cycle, profile, policy):
    """Track contact tasks while fitting both legs and a floating reduced torso.

    COM motion is integrated from the existing support impulse. Changing leg
    shape produces a compensating torso displacement by mass conservation.
    Both leg trajectories, mean COM placement and torso pitch are variables.
    Contact geometry, angular momentum, joint effort and clearance constrain
    the fit. No muscle or extinct-animal anatomical identification is implied.
    """
    from ..planning.running_support import support_body_response
    period = 2*cycle.step
    count = policy['samples_per_stride']
    if not isinstance(count,int) or isinstance(count,bool) or not 24 <= count <= 256:
        raise ContractError('invalid floating stride sample count')
    ranges={key:(0.,20.) for key in ('reference_weight','acceleration_weight','jerk_weight','effort_weight','effort_rate_weight','power_weight','swing_task_weight','body_tracking_weight','angular_balance_weight','body_pitch_weight')}
    ranges.update(contact_task_weight=(10.,5000.),body_gyration_leg_lengths=(.1,2.),minimum_clearance_leg_lengths=(0.,.2),material_clearance_leg_lengths=(0.,.2),maximum_swing_adjustment_leg_lengths=(.01,.4),maximum_body_adjustment_leg_lengths=(.01,.2),projection_margin_degrees=(2.,12.))
    for key,(low,high) in ranges.items():
        value=policy.get(key)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low<=value<=high:
            raise ContractError('invalid floating stride policy: '+key)
    if isinstance(policy.get('max_evaluations'),bool) or not isinstance(policy.get('max_evaluations'),int) or not 10<=policy['max_evaluations']<=1000:
        raise ContractError('invalid floating stride evaluation budget')
    fractions = np.asarray(policy['segment_mass_fractions'],dtype=float)
    if fractions.shape != (3,) or not np.isfinite(fractions).all() or np.any(fractions<=0) or 2*fractions.sum() >= .5:
        raise ContractError('invalid floating stride mass fractions')
    actuation = policy.get('actuation')
    recovery = policy.get('forward_recovery')
    distribution = policy.get('axial_mass_distribution')
    if any(v is not None for v in (actuation,recovery,distribution)):
        if not all(isinstance(v,dict) for v in (actuation,recovery,distribution)):
            raise ContractError('distributed actuator fit requires all three policies')
        for key in ('peak_torque_bodyweight_leglength','speed_scale_radians_s','angle_width_degrees'):
            v=np.asarray(actuation[key],dtype=float)
            if v.shape!=(3,) or not np.isfinite(v).all() or np.any(v<=0):
                raise ContractError('invalid actuator envelope: '+key)
        v=np.asarray(actuation['optimal_angles_degrees'],dtype=float)
        if v.shape!=(3,) or not np.isfinite(v).all():raise ContractError('invalid actuator preferred angles')
        for value in (actuation['activation_time_s'],actuation['constraint_weight'],recovery['progress_tolerance_leg_lengths'],recovery['task_weight'],recovery['extension_weight']):
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:raise ContractError('invalid distributed fit policy')
        if recovery.get('mode', 'knee_opening') not in ('knee_opening', 'foot_approach'):
            raise ContractError('invalid forward recovery mode')
        if recovery.get('mode') == 'foot_approach':
            for key in ('approach_velocity_weight', 'release_extension_rate_weight'):
                value = recovery[key]
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0 <= value <= 10:
                    raise ContractError('invalid recovery task weight: '+key)
        shares=np.array([distribution[k] for k in ('trunk','neck_head','tail')])
        if not np.isfinite(shares).all() or np.any(shares<=0) or not np.isclose(shares.sum(),1):raise ContractError('invalid axial mass shares')
    times = np.arange(count)*period/count
    source_t = np.asarray([r['time_s'] for r in plan['samples']])
    sides = list(context.legs)
    if len(sides)!=2:
        raise ContractError('floating running requires two admitted legs')
    rows=[]
    for t in times:
        row=cycle.sample(float(t))
        for side in sides:
            targets=np.array([r['feet'][side]['world_foot_target_m'] for r in plan['samples']])
            row['feet'][side]['world_foot_target_m']=[float(np.interp(t,source_t,targets[:,k])) for k in range(3)]
        rows.append(row)
    bodies=support_body_response(cycle,dict(plan,samples=rows),context.roles,profile,context.hip_offsets)
    samples={side:[] for side in sides}
    def observe(side,hip,evaluate,best):
        def project(c):
            xyz=np.array([hip,c[4],c[5],c[2]])
            return np.stack((xyz@context.forward,xyz@context.up),axis=-1)
        p=project(best); plus=project(evaluate(float(best[-1]+.01)))
        theta=lambda v: math.atan2(v[0],-v[1])
        slope=(theta(plus[-1]-plus[-2])-theta(p[-1]-p[-2]))/.01
        samples[side].append((p,float(best[-1]),slope))
    axial_world=[]
    axial_fractions=None
    if distribution:
        bindings={v['role']:context.source.name_to_node[v['bone']] for v in profile['bindings']}
        grouped=[('trunk',['pelvis']+sorted(k for k in bindings if k.startswith('spine.'))),
                 ('neck_head',sorted(k for k in bindings if k.startswith('neck.'))+['head']),
                 ('tail',sorted((k for k in bindings if k.startswith('tail.')),key=lambda k:int(k.split('.')[-1])))]
        axial_nodes=[];weights=[]
        for name,roles in grouped:
            if not roles or any(k not in bindings for k in roles):raise ContractError('missing distributed-mass semantic chain: '+name)
            taper=np.linspace(1.,.15,len(roles)) if name=='tail' else np.ones(len(roles))
            weights.extend((distribution[name]*taper/taper.sum()).tolist());axial_nodes.extend(bindings[k] for k in roles)
        axial_fractions=np.array(weights)*(1-2*sum(fractions))
    for row,body in zip(rows,bodies):
        pose=solve_airborne_plan_sample(context,row,body_response_sample=body,leg_candidate_observer=observe)
        if distribution:
            from ..layers.leg_contact_resolve_v3 import _world_matrices
            w=np.asarray(_world_matrices(context.source,pose.translations,pose.rotations,context.base_s))
            xyz=w[axial_nodes,:3,3]
            axial_world.append(np.stack((xyz@context.forward,xyz@context.up),axis=-1))
    seed_points=np.stack([np.array([r[0] for r in samples[side]]) for side in sides],axis=1)
    seed_points[:,:,:,0]-=cycle.speed*times[:,None,None]
    seed_pitch=np.array([[samples[s][i][1] for s in sides] for i in range(count)])
    pitch_slope=np.array([[samples[s][i][2] for s in sides] for i in range(count)])
    if np.any(np.abs(pitch_slope)<.01):
        raise ContractError('degenerate sagittal pitch transport')
    hip0=seed_points[:,:,0].mean(axis=1)
    hip_offsets=seed_points[:,:,0]-hip0[:,None,:]
    segment=np.diff(seed_points,axis=2)
    # The sagittal projection is a reduced approximation to the full rig.
    lengths=np.mean(np.linalg.norm(segment,axis=3),axis=0)
    theta0=np.unwrap(np.arctan2(segment[:,:,:,0],-segment[:,:,:,1]),axis=0)
    local_centers=.5*(seed_points[:,:,:-1]+seed_points[:,:,1:])-hip0[:,None,None,:]
    mean_limb_com=np.mean(np.sum(local_centers*fractions[None,None,:,None],axis=(1,2)),axis=0)
    axial_local=None
    if distribution:
        axial_local=np.array(axial_world)-np.stack((cycle.speed*times,np.zeros(count)),axis=-1)[:,None,:]-hip0[:,None,:]
        mean_limb_com+=np.mean((axial_local*axial_fractions[None,:,None]).sum(axis=1),axis=0)
    desired_com=hip0+mean_limb_com
    # Remove pelvis roll/yaw perturbations from COM acceleration: integrated
    # impulse, not incidental hip geometry, owns the reduced body's travel.
    desired_com[:,0]=np.array([cycle.travel(t)-cycle.speed*t for t in times])+desired_com[:,0].mean()
    desired_com[:,1]=np.array([cycle.vertical(t/cycle.step)[0] for t in times])+desired_com[:,1].mean()-np.mean([cycle.vertical(t/cycle.step)[0] for t in times])
    d1,d2=periodic_derivatives(times,period);omega=2*math.pi/period
    mass=profile['authoring']['animalInstance']['measurements']['body_mass']['value']
    length=float(lengths.sum(axis=1).mean());g=cycle.gravity
    body_inertia=(1-2*sum(fractions))*(policy['body_gyration_leg_lengths']*length)**2
    contact=np.array([[r['feet'][s]['contact'] for s in sides] for r in rows])
    swing=np.array([[r['feet'][s]['swing_phase'] for s in sides] for r in rows])
    loads=np.array([[r['feet'][s]['support_load_bodyweights'] for s in sides] for r in rows])
    ax=np.array([0. if r['flight'] else (d2@desired_com[:,0])[i] for i,r in enumerate(rows)])
    forces=np.stack((ax[:,None]*contact,g*loads),axis=-1)
    margin=policy['projection_margin_degrees']
    if not 2 <= margin <= 12:raise ContractError('invalid projection margin')
    lower=np.empty((count,2,3));upper=lower.copy()
    for i,row in enumerate(rows):
        for j,side in enumerate(sides):
            f=row['feet'][side]
            if context.articulation_profile is not None:
                env=context.articulation_profile.effective(contact=f['contact'],swing_phase=f['swing_phase'])
                keys=('hip_sagittal_degrees','knee_interior_degrees','ankle_interior_degrees')
                lower[i,j]=[env[k].hard_min_deg+margin for k in keys]
                upper[i,j]=[env[k].hard_max_deg-margin for k in keys]
            else:
                gait=context.gait
                lower[i,j]=[-gait.hip_extension_limit_degrees+margin,gait.knee_min_interior_degrees+margin,gait.ankle_min_interior_degrees+margin]
                upper[i,j]=[gait.hip_flexion_limit_degrees-margin,gait.knee_max_interior_degrees-margin,gait.ankle_max_interior_degrees-margin]
    lower=np.radians(lower);upper=np.radians(upper)
    if recovery:
        limit=recovery['maximum_knee_opening_degrees']
        if isinstance(limit,bool) or not isinstance(limit,(int,float)) or not 140<=limit<=165:raise ContractError('invalid recovery extension reserve')
        upper[:,:,1]=np.minimum(upper[:,:,1],math.radians(limit))
    bend_sign=np.sign(np.diff(theta0,axis=2))
    baseline_foot=seed_points[:,:,-1]
    # Weight approaches contact smoothly. The free foot is a loose task, not
    # a prescribed arc; endpoints and support remain high-priority tasks.
    free_window=np.sin(np.pi*swing)**2*(~contact)
    task_weight=policy['swing_task_weight']+policy['contact_task_weight']*(1-free_window)**16
    task_weight[contact]=policy['contact_task_weight']
    material_floor=np.stack([np.interp(times,source_t,[r['feet'][s]['material_floor_foot_height_m'] for r in plan['samples']]) for s in sides],axis=1)
    clearance=np.maximum(baseline_foot[:,:,1].min(axis=0)[None,:]+policy['minimum_clearance_leg_lengths']*length*free_window,
        material_floor+policy['material_clearance_leg_lengths']*length*free_window)
    initial=np.c_[theta0.reshape(count,6),np.zeros(count)].ravel()
    initial=np.r_[initial,0.,0.]
    def evaluate(x):
        z=x[:-2].reshape(count,7);theta=z[:,:6].reshape(count,2,3);pitch=z[:,6]
        com=desired_com+length*x[-2:]
        axial=None
        if distribution:
            body,points,axial=distributed_body_geometry(theta,lengths,hip_offsets,com,fractions,axial_local,axial_fractions,pitch)
        else:
            body,points=floating_body_geometry(theta,lengths,hip_offsets,com,fractions)
        q=np.concatenate((theta[:,:,:1]-pitch[:,None,None],np.diff(theta,axis=2)),axis=2)
        torque=np.stack([inverse_dynamics(points[:,j],mass*forces[:,j],mass*fractions,g,d2)/(mass*g*length) for j in range(2)],axis=1)
        angles=np.concatenate((theta[:,:,:1],np.pi-np.abs(np.diff(theta,axis=2))),axis=2)
        h=reduced_angular_momentum(points,body,com,pitch,fractions,0. if distribution else body_inertia,d1)
        if distribution:
            cross=lambda a,b:a[...,0]*b[...,1]-a[...,1]*b[...,0]
            rbody=body-com;r=axial-com[:,None,:]
            h-=(1-2*sum(fractions))*cross(rbody,d1@rbody)
            h+=(cross(r,np.einsum('ij,jsk->isk',d1,r))*axial_fractions[None,:]).sum(axis=1)
        lever=baseline_foot-com[:,None,:]
        external=np.sum(lever[:,:,0]*forces[:,:,1]-lever[:,:,1]*forces[:,:,0],axis=1)
        balance=(d1@h-external)/(g*length)
        return theta,pitch,body,points,q,torque,angles,balance
    def residual(x,blocks_only=False):
        theta,pitch,body,points,q,tau,angles,balance=evaluate(x)
        flat=q.reshape(count,6);tflat=tau.reshape(count,6)
        foot_delta=points[:,:,-1]-baseline_foot
        body_delta=(body-hip0)/length
        fitted_pitch=seed_pitch+(theta[:,:,2]-theta0[:,:,2])/pitch_slope
        blocks=[policy['reference_weight']*(theta-theta0).reshape(count,6),
          policy['acceleration_weight']*(d2@flat)/omega**2,
          policy['jerk_weight']*(d1@d2@flat)/omega**3,
          policy['effort_weight']*tflat,
          policy['effort_rate_weight']*(d1@tflat)/omega,
          policy['power_weight']*tflat*(d1@flat)/omega,
          (task_weight[:,:,None]*foot_delta/length).reshape(count,4),
          80*np.maximum(0,clearance-points[:,:,-1,1])/length,
          80*np.maximum(0,lower-angles).reshape(count,6),
          80*np.maximum(0,angles-upper).reshape(count,6),
          80*np.maximum(0,-np.diff(theta,axis=2)*bend_sign).reshape(count,4),
          30*np.maximum(0,np.abs(foot_delta)/length-policy['maximum_swing_adjustment_leg_lengths']).reshape(count,4),
          policy['body_tracking_weight']*body_delta,
          40*np.maximum(0,np.abs(body_delta)-policy['maximum_body_adjustment_leg_lengths']),
          policy['angular_balance_weight']*balance[:,None],
          policy['body_pitch_weight']*pitch[:,None],
          .1*(d2@pitch)[:,None]/omega**2,
          40*np.maximum(0,np.abs(fitted_pitch-20)-64).reshape(count,2)]
        if actuation:
            rates=(d1@flat).reshape(count,2,3)
            activation,excitation,capacity=actuator_demand(tau,angles,rates,d1,actuation)
            blocks += [actuation['constraint_weight']*np.maximum(0,np.abs(activation)-1).reshape(count,6),
                       actuation['constraint_weight']*np.maximum(0,np.abs(excitation)-1).reshape(count,6),
                       .06*excitation.reshape(count,6)]
            # Functional reach guidance, not inferred dinosaur physiology:
            # advance throughout swing and open the knee on the forward path.
            progress_error=np.maximum(0,np.abs(foot_delta[:,:,0])/length-recovery['progress_tolerance_leg_lengths'])
            blocks += [recovery['task_weight']*progress_error]
            if recovery.get('mode', 'knee_opening') == 'knee_opening':
                # Retained only for reproducibility of C41 and older recipes.
                u=np.clip((swing-.20)/.62,0,1);opening=u*u*(3-2*u)
                target_knee=np.radians(82.+65.*opening)
                opening_gate=np.sin(np.pi*swing)**2*(~contact)
                blocks += [recovery['extension_weight']*opening_gate*np.maximum(0,target_knee-angles[:,:,1])]
            else:
                # Coordinate the approach of the endpoint, not a knee-angle
                # timetable. Toe clearance and capacity select the leg shape.
                u=np.clip((swing-.50)/.40,0,1)
                approach=u*u*(3-2*u)*(~contact)
                velocity_error=np.einsum('ij,jsk->isk',d1,foot_delta)/(length*omega)
                blocks += [(recovery['approach_velocity_weight']*approach[:,:,None]*velocity_error).reshape(count,4)]
                # Discourage re-extending an unloaded knee before gathering.
                # A smooth phase-local rate penalty, not a prescribed angle.
                release_gate=np.sin(np.pi*np.clip(swing/.30,0,1))**2*(~contact)
                knee_rate=d1@angles[:,:,1]
                blocks += [recovery['release_extension_rate_weight']*release_gate*np.maximum(0,knee_rate)/omega]
        if blocks_only:return blocks
        return np.concatenate([b.ravel() for b in blocks])
    blocks=residual(initial,True);size=sum(b.size for b in blocks)
    sparsity=lil_matrix((size,len(initial)),dtype=int)
    at=0
    for b in blocks:
        width=b.shape[1]
        for i in range(count):
            for j in range(-3,4):
                node=((i+j)%count)*7
                sparsity[at+i*width:at+(i+1)*width,node:node+7]=1
        sparsity[at:at+b.size,-2:]=1
        at+=b.size
    lo=np.r_[np.tile(np.r_[np.full(6,-2.8),-math.radians(6)],count),-.08,-.1]
    hi=np.r_[np.tile(np.r_[np.full(6,2.8),math.radians(6)],count),.08,.06]
    result=least_squares(residual,initial,bounds=(lo,hi),jac_sparsity=sparsity.tocsr(),
        max_nfev=policy['max_evaluations'],ftol=2e-5,xtol=2e-5,gtol=2e-5)
    theta,pitch,body,points,q,tau,angles,balance=evaluate(result.x)
    if not np.isfinite(result.x).all():raise ContractError('nonfinite floating stride fit')
    print('FLOATING_STRIDE_FIT',result.success,result.nfev,float(residual(initial)@residual(initial)),'->',float(result.fun@result.fun),flush=True)
    def curve(values):return CubicSpline(np.r_[times,period],np.concatenate((values,values[:1])),axis=0,bc_type='periodic')
    body_curve=curve(body-hip0);pitch_curve=curve(pitch)
    foot_curves=[curve(points[:,j,-1]-baseline_foot[:,j]) for j in range(2)]
    met_curves=[curve(seed_pitch[:,j]+(theta[:,j,2]-theta0[:,j,2])/pitch_slope[:,j]) for j in range(2)]
    for row in plan['samples']:
        t=row['time_s']%period
        row['stride_fitted_body_forward_up_m']=body_curve(t).tolist()
        row['stride_fitted_body_pitch_radians']=float(pitch_curve(t))
        for j,side in enumerate(sides):
            f=row['feet'][side]
            f['stride_fitted_pitch_degrees']=float(met_curves[j](t))
            f['stride_fitted_foot_forward_up_m']=([0.,0.] if f['contact'] else foot_curves[j](t).tolist())
    seed=evaluate(initial)
    actuator_receipt=None
    if actuation:
        a,u,cap=actuator_demand(tau,angles,(d1@q.reshape(count,6)).reshape(count,2,3),d1,actuation)
        actuator_receipt=dict(maximum_activation_demand=float(np.abs(a).max()),maximum_excitation_demand=float(np.abs(u).max()),
            maximum_normalized_capacity=float(cap.max()),activation=a.tolist(),excitation=u.tolist(),
            classification='Signed torque-actuator surrogate with angle/speed capacity and first-order activation; finite-weight limits, not muscle simulation.')
    return dict(actuator_demand=actuator_receipt,axial_mass_fractions=None if axial_fractions is None else axial_fractions.tolist(),
        axial_local_centers_m=None if axial_local is None else axial_local.tolist(),schema='eonwild.floating-body-stride-fit.v1',policy=deepcopy(policy),
        optimizer_success=bool(result.success),message=result.message,evaluations=result.nfev,
        initial_objective=float(residual(initial)@residual(initial)),final_objective=float(result.fun@result.fun),
        initial_torque_rms_nm=float(mass*g*length*np.sqrt(np.mean(seed[5]**2))),
        fitted_torque_rms_nm=float(mass*g*length*np.sqrt(np.mean(tau**2))),
        angular_momentum_residual_rms_bodyweight_leglength=float(np.sqrt(np.mean(balance**2))),
        maximum_support_task_residual_m=float(np.max(np.linalg.norm((points[:,:,-1]-baseline_foot)[contact],axis=1))),
        maximum_body_adjustment_m=float(np.max(np.linalg.norm(body-hip0,axis=1))),
        times_s=times.tolist(),joint_angles_degrees=np.degrees(angles).tolist(),
        fitted_segment_angles_degrees=np.degrees(theta).tolist(),fitted_body_offset_m=(body-hip0).tolist(),
        seed_points_m=seed_points.tolist(),fitted_points_m=points.tolist(),reduced_com_m=(desired_com+length*result.x[-2:]).tolist(),
        material_floor_height_m=material_floor.tolist(),minimum_swing_foot_height_m=clearance.tolist(),
        fitted_body_pitch_radians=pitch.tolist(),support_force_per_total_mass=forces.tolist(),
        fitted_foot_offset_m=(points[:,:,-1]-baseline_foot).tolist(),
        fitted_joint_torque_nm=(tau*mass*g*length).tolist(),
        classification=('Coupled bilateral planar fit with distributed axial point masses, rod legs and first-order torque-actuator demand. Exact reduced COM reconstruction; finite-weight contact, actuator and angular-momentum constraints. Not a muscle simulation or whole-rig force certificate.' if distribution else 'Coupled bilateral planar trajectory fit with a floating lumped torso, exact reduced COM reconstruction and soft angular-momentum balance. Contact tasks and effort are optimized; not a muscle simulation or whole-rig force certificate.'),
        limitations=[('Axial centers follow semantic bones with estimated region shares; mass fractions and actuator envelopes are engineering priors.' if distribution else 'Torso COM is at hip center; torso gyration and segment mass fractions are engineering estimates.'),
            'Sagittal projected segments and toe-base force point approximate the actual rig and material contact.',
            'Angular momentum and contact are finite-weight objectives; residuals are reported.',
            'Prescribed support force schedule, timing, toe choreography and axial artistic motion remain.',
            'Full-rig IK/contact correction follows the fit; final emitted motion requires separate measurement.'])
