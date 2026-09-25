"""Contact-constrained temporal IK initializer, not a dynamics solver.

Solve neighboring poses together so acceleration is a physical-time quantity,
not a sequential prediction that feeds correction errors into later frames.
The caller owns task targets, admitted coordinate bounds and final mechanics.
"""
import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix
from scipy.spatial.transform import Rotation


def periodic_contact_seed(problem, times, seed, reference, settings):
    """Jointly fit a periodic leg seed; contact owns support, swing can relax.

    A soft anatomical reference resolves the redundant chain. It is not an
    anatomical limit, and this kinematic initializer is audited by mechanics.
    """
    from .moco_path_task import foot_task, to_world
    from .moco_tasks import smooth
    p=problem;task=p.policy['path_task'];t=np.asarray(times[:-1]);dt=t[1]-t[0]
    indices=[p.index[n] for n in p.names if n.startswith(('hip_','knee_','ankle_','mtp_','digit_'))]
    names=[p.names[i] for i in indices];count=len(indices);N=len(t)
    feet=[p.model.getBodySet().get('toe_'+s) for s in ('l','r')]
    targets=[ [foot_task(p,float(v),s) for s in ('l','r')] for v in t]
    gate=[]
    for v in t:
        row=[]
        for offset in (0.,.5):
            phase=(v/p.period+offset)%1.;swing=np.clip((phase-task['duty_factor'])/(1-task['duty_factor']),0,1)
            relax=float(smooth(swing/.22)*(1-smooth((swing-.72)/.28))) if phase>task['duty_factor'] else 0.
            row.append(1-relax)
        gate.append(row)
    gate=np.asarray(gate);old=None;geometry=np.zeros((N,16));calls=0
    contact_forces=[[p.model.getForceSet().get(c['force']) for c in p.metadata['contacts'] if c['force'].endswith('_'+s)] for s in ('l','r')]
    bounds=np.array([p.metadata['coordinates'][n]['bounds_rad'] for n in names])
    margin=.01*np.diff(bounds,axis=1)[:,0];lo=bounds[:,0]+margin;hi=bounds[:,1]-margin
    target_reference=np.asarray(reference[:-1])[:,indices]
    def residual(x):
        nonlocal old,calls
        angles=x.reshape(N,count);q=np.array(seed[:-1],copy=True);q[:,indices]=angles
        changed=np.arange(N) if old is None else np.flatnonzero(np.any(q!=old,axis=1))
        for k in changed:
            world=to_world(q[k:k+1],t[k:k+1],p.index,p.speed,task['yaw_rate_rad_s'])[0]
            p.set_state(float(t[k]),world,np.zeros(len(world)));row=[]
            for side,foot in enumerate(feet):
                pos,R,digit=targets[k][side];r=foot.getTransformInGround(p.state).R()
                mat=np.array([[r.get(i,j) for j in range(3)] for i in range(3)])
                loaded=gate[k,side]
                wp=settings['position_weight']*(loaded+(1-loaded)*settings['swing_position_fraction'])
                wr=settings['orientation_weight']*(loaded+(1-loaded)*settings['swing_orientation_fraction'])
                row.extend(wp*(foot.getPositionInGround(p.state).to_numpy()-pos)/p.L)
                row.extend(wr*Rotation.from_matrix(R.T@mat).as_rotvec())
                row.append(settings['digit_weight']*(world[p.index['digit_'+('l','r')[side]]]-digit))
                phase=(t[k]/p.period+(0.,.5)[side])%1
                expected=np.sin(np.pi*phase/task['duty_factor'])**2/task['duty_factor'] if phase<task['duty_factor'] else 0.
                actual=sum(f.getRecordValues(p.state).get(1) for f in contact_forces[side])/p.bw
                row.append(settings.get('support_force_weight',10.)*(actual-expected))
            geometry[k]=row
        old=q.copy();calls+=1
        acceleration=(np.roll(angles,1,axis=0)-2*angles+np.roll(angles,-1,axis=0))/dt**2
        return np.c_[geometry,settings['reference_weight']*(angles-target_reference),
                     settings['acceleration_weight']*acceleration*p.L/9.80665].ravel()
    rows=16+2*count;pattern=lil_matrix((N*rows,N*count),dtype=int)
    for k in range(N):
        pattern[k*rows:(k+1)*rows,k*count:(k+1)*count]=1
        for j in ((k-1)%N,(k+1)%N):pattern[j*rows+16+count:(j+1)*rows,k*count:(k+1)*count]=1
    initial=np.clip(seed[:-1,indices],lo+1e-7,hi-1e-7).ravel();before=residual(initial)
    result=least_squares(residual,initial,bounds=(np.tile(lo,N),np.tile(hi,N)),
        jac_sparsity=pattern.tocsr(),tr_solver='lsmr',max_nfev=settings['max_evaluations'],
        ftol=1e-6,xtol=1e-6,gtol=1e-6,verbose=1)
    after=residual(result.x);q=np.array(seed,copy=True);q[:-1,indices]=result.x.reshape(N,count);q[-1]=q[0]
    receipt=dict(classification='Periodic temporal contact IK, not dynamics convergence',
        evaluations=result.nfev,success=bool(result.success),message=result.message,
        initial_cost=float(before@before),final_cost=float(after@after),residual_calls=calls,
        settings=settings,coordinate_limits_unchanged=True)
    return q,receipt


def acceleration_rows(values, dt, leg_length, coordinate_scales):
    return np.diff(values,n=2,axis=0)*coordinate_scales*(leg_length/9.80665)/dt**2


def coordinate_contacts(problem, times, reference, positions, rotations, digits, settings, support_weights=None, force_targets=None):
    p=problem;t=np.asarray(times);q=np.asarray(reference).copy();dt=float(t[1]-t[0])
    if len(t)<9 or not np.allclose(np.diff(t),dt,rtol=1e-8,atol=1e-10):
        raise ValueError('Uniform physical-time samples and nine poses required')
    periodic=settings.get('periodic',False)
    if periodic and settings.get('optimize_root',True):raise ValueError('Periodic contact polish preserves the root trajectory')
    endpoint=q[-1].copy()
    if periodic:t=t[:-1];q=q[:-1]
    roots=['forward','height','lateral'] if settings.get('optimize_root',True) else []
    names=roots+[n for n in p.names if n.startswith(('hip_','knee_','ankle_','mtp_','digit_'))]
    indices=[p.index[n] for n in names];count=len(indices);free=np.arange(len(t)) if periodic else np.arange(3,len(t)-3)
    scales=np.array([1/p.L if n in ('forward','height','lateral') else 1. for n in names])
    lo=q[free][:,indices]-.3;hi=q[free][:,indices]+.3
    for j,n in enumerate(names):
        if n in p.metadata['coordinates']:
            lo[:,j],hi[:,j]=p.metadata['coordinates'][n]['bounds_rad']
    # Preserve the existing contact-IK reference/task balance. The acceleration
    # ratio is inherited from finite whole-body coordination, not fitted per rig.
    contact=35.;orientation=4.;ratio=contact/settings['foot_position_weight']
    reference_weights=np.array([4/p.L if n in ('forward','height','lateral') else .08 for n in names])
    geometry_rows=14+(2 if force_targets is not None else 0)
    old=None;geometry=np.zeros((len(t),geometry_rows));calls=0
    contact_forces=[[p.model.getForceSet().get(c['force']) for c in p.metadata['contacts'] if c['force'].endswith('_'+side)] for side in ('l','r')] if force_targets is not None else None
    def residual(x):
        nonlocal old,calls
        values=q.copy();values[np.ix_(free,indices)]=x.reshape(len(free),count)
        changed=np.arange(len(t)) if old is None else np.flatnonzero(np.any(values!=old,axis=1))
        for k in changed:
            p.state.setTime(float(t[k]))
            for j,c in enumerate(p.coordinates):c.setValue(p.state,float(values[k,j]),False)
            p.model.realizePosition(p.state);row=[]
            for side,foot in enumerate(p.feet):
                pos=foot.getPositionInGround(p.state).to_numpy();r=foot.getTransformInGround(p.state).R()
                mat=np.array([[r.get(i,j) for j in range(3)] for i in range(3)])
                support=1. if support_weights is None else float(support_weights[k,side])
                row.extend(contact*support*(pos-positions[k,side])/p.L)
                row.extend(orientation*support*Rotation.from_matrix(rotations[k,side].T@mat).as_rotvec())
                row.append(.8*(values[k,p.index['digit_'+('l','r')[side]]]-digits[k,side]))
            if force_targets is not None:
                p.model.realizeDynamics(p.state)
                row.extend(settings['contact_force_weight']*(sum(f.getRecordValues(p.state).get(1) for f in side)/p.bw-force_targets[k,j]) for j,side in enumerate(contact_forces))
            geometry[k]=row
        old=values.copy();calls+=1
        deviation=(values[:,indices]-q[:,indices])*reference_weights
        acceleration=np.zeros_like(deviation)
        if periodic:
            acceleration=ratio*settings['acceleration_weight']*(np.roll(values[:,indices],1,axis=0)-2*values[:,indices]+np.roll(values[:,indices],-1,axis=0))*scales*(p.L/9.80665)/dt**2
        else:acceleration[1:-1]=ratio*settings['acceleration_weight']*acceleration_rows(values[:,indices],dt,p.L,scales)
        return np.c_[geometry,deviation,acceleration].ravel()
    rows=geometry_rows+2*count;pattern=lil_matrix((len(t)*rows,len(free)*count),dtype=int)
    for j,k in enumerate(free):
        pattern[k*rows:(k+1)*rows,j*count:(j+1)*count]=1
        for neighbor in ((k-1)%len(t),(k+1)%len(t)):
            pattern[neighbor*rows+geometry_rows+count:(neighbor+1)*rows,j*count:(j+1)*count]=1
    x=q[free][:,indices].ravel();initial=residual(x)
    result=least_squares(residual,np.clip(x,lo.ravel()+1e-10,hi.ravel()-1e-10),
        bounds=(lo.ravel()+1e-11,hi.ravel()-1e-11),jac_sparsity=pattern.tocsr(),
        max_nfev=settings.get('max_evaluations',8),diff_step=1e-5,
        ftol=1e-5,xtol=1e-5,gtol=1e-5,verbose=1,tr_solver='lsmr')
    final=residual(result.x);output=q.copy();output[np.ix_(free,indices)]=result.x.reshape(len(free),count)
    if periodic:
        endpoint[indices]=output[0,indices];output=np.vstack([output,endpoint])
    return output,dict(classification='Temporal contact IK initializer, not physical convergence',
        optimizer_success=bool(result.success),message=result.message,evaluations=result.nfev,
        residual_calls=calls,initial_cost=float(initial@initial),final_cost=float(final@final),
        acceleration_contact_ratio=ratio*settings['acceleration_weight'],
        maximum_foot_position_error_m=float(np.max(np.linalg.norm(geometry[:,:14].reshape(len(t),2,7)[:,:,:3],axis=2)/(1. if support_weights is None else support_weights[:len(t)]))*p.L/contact),
        settings=settings,coordinate_limits_unchanged=True)
