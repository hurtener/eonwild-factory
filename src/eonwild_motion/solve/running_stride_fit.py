"""Offline periodic leg fit with reduced sagittal inverse dynamics.

The source geometry, contact anchors and body path remain authoritative. Joint
torques couple the complete stride; they are NOT measured muscle forces. Rod
inertias/segment masses are explicit engineering priors. This first stage fits
the remaining metatarsal degree of freedom, not the root, toes or gait timing.
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
