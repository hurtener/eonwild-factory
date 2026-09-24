"""Contact-constrained temporal IK initializer, not a dynamics solver.

Solve neighboring poses together so acceleration is a physical-time quantity,
not a sequential prediction that feeds correction errors into later frames.
The caller owns task targets, admitted coordinate bounds and final mechanics.
"""
import numpy as np
from scipy.optimize import least_squares
from scipy.sparse import lil_matrix
from scipy.spatial.transform import Rotation


def acceleration_rows(values, dt, leg_length, coordinate_scales):
    return np.diff(values,n=2,axis=0)*coordinate_scales*(leg_length/9.80665)/dt**2


def coordinate_contacts(problem, times, reference, positions, rotations, digits, settings):
    p=problem;t=np.asarray(times);q=np.asarray(reference).copy();dt=float(t[1]-t[0])
    if len(t)<9 or not np.allclose(np.diff(t),dt,rtol=1e-8,atol=1e-10):
        raise ValueError('Uniform physical-time samples and nine poses required')
    names=['forward','height','lateral']+[n for n in p.names if n.startswith(('hip_','knee_','ankle_','mtp_','digit_'))]
    indices=[p.index[n] for n in names];count=len(indices);free=np.arange(3,len(t)-3)
    scales=np.array([1/p.L if n in ('forward','height','lateral') else 1. for n in names])
    lo=q[free][:,indices]-.3;hi=q[free][:,indices]+.3
    for j,n in enumerate(names):
        if n in p.metadata['coordinates']:
            lo[:,j],hi[:,j]=p.metadata['coordinates'][n]['bounds_rad']
    # Preserve the existing contact-IK reference/task balance. The acceleration
    # ratio is inherited from finite whole-body coordination, not fitted per rig.
    contact=35.;orientation=4.;ratio=contact/settings['foot_position_weight']
    reference_weights=np.array([4/p.L if n in ('forward','height','lateral') else .08 for n in names])
    old=None;geometry=np.zeros((len(t),14));calls=0
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
                row.extend(contact*(pos-positions[k,side])/p.L)
                row.extend(orientation*Rotation.from_matrix(rotations[k,side].T@mat).as_rotvec())
                row.append(.8*(values[k,p.index['digit_'+('l','r')[side]]]-digits[k,side]))
            geometry[k]=row
        old=values.copy();calls+=1
        deviation=(values[:,indices]-q[:,indices])*reference_weights
        acceleration=np.zeros_like(deviation)
        acceleration[1:-1]=ratio*settings['acceleration_weight']*acceleration_rows(values[:,indices],dt,p.L,scales)
        return np.c_[geometry,deviation,acceleration].ravel()
    rows=14+2*count;pattern=lil_matrix((len(t)*rows,len(free)*count),dtype=int)
    for j,k in enumerate(free):
        pattern[k*rows:(k+1)*rows,j*count:(j+1)*count]=1
        for neighbor in (k-1,k+1):pattern[neighbor*rows+14+count:(neighbor+1)*rows,j*count:(j+1)*count]=1
    x=q[free][:,indices].ravel();initial=residual(x)
    result=least_squares(residual,np.clip(x,lo.ravel()+1e-10,hi.ravel()-1e-10),
        bounds=(lo.ravel()+1e-11,hi.ravel()-1e-11),jac_sparsity=pattern.tocsr(),
        max_nfev=settings.get('max_evaluations',8),diff_step=1e-5,
        ftol=1e-5,xtol=1e-5,gtol=1e-5,verbose=1,tr_solver='lsmr')
    final=residual(result.x);output=q.copy();output[np.ix_(free,indices)]=result.x.reshape(len(free),count)
    return output,dict(classification='Temporal contact IK initializer, not physical convergence',
        optimizer_success=bool(result.success),message=result.message,evaluations=result.nfev,
        residual_calls=calls,initial_cost=float(initial@initial),final_cost=float(final@final),
        acceleration_contact_ratio=ratio*settings['acceleration_weight'],
        maximum_foot_position_error_m=float(np.max(np.linalg.norm(geometry.reshape(len(t),2,7)[:,:,:3],axis=2))*p.L/contact),
        settings=settings,coordinate_limits_unchanged=True)
