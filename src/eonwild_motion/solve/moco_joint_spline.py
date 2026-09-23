"""Smooth interpolation inside admitted joint ranges, with exact derivatives.

Only input initialization is moved a tiny distance inside a stop. The resulting
continuous curve never clips a moving angle; foot/contact mechanics must be
replayed after using it.
"""
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.special import expit


def to_latent(values,lo,hi,interior_fraction=1e-10):
    width=.01*(hi-lo)
    margin=interior_fraction*(hi-lo)
    value=np.clip(values,lo+margin,hi-margin) # initialization only
    return value+width*np.log(-np.expm1(-(value-lo)/width))-width*np.log(-np.expm1(-(hi-value)/width))


def bounded(raw,lo,hi):
    width=.01*(hi-lo)
    low=(raw-lo)/width;high=(raw-hi)/width
    value=np.where(raw<(lo+hi)/2,
        lo+width*(np.logaddexp(0,low)-np.logaddexp(0,high)),
        hi-width*(np.logaddexp(0,-high)-np.logaddexp(0,-low)))
    a,b=expit(low),expit(high)
    return value,a-b,(a*(1-a)-b*(1-b))/width


class BoundedJointSpline:
    def __init__(self,times,values,bounds,bc_type='not-a-knot'):
        latent=np.array(values,copy=True)
        self.bounds=bounds
        self.initialization_adjustment={}
        for i,(lo,hi) in bounds.items():
            span=hi-lo;fraction=(latent[:,i]-lo)/span
            if not np.isfinite(fraction).all() or span<=0:raise ValueError('Invalid bounded joint seed')
            if np.min(fraction)<0 or np.max(fraction)>1:
                self.initialization_adjustment[i]=float(max(lo-latent[:,i].min(),latent[:,i].max()-hi,0))
            latent[:,i]=to_latent(latent[:,i],lo,hi)
        self.spline=CubicSpline(times,latent,axis=0,bc_type=bc_type)

    def __call__(self,times,derivative=0):
        if derivative not in (0,1,2):raise ValueError('Only position, velocity and acceleration supported')
        z=self.spline(times);out=self.spline(times,derivative)
        for i,(lo,hi) in self.bounds.items():
            value,first,second=bounded(z[...,i],lo,hi)
            if derivative==0:out[...,i]=value
            elif derivative==1:out[...,i]=first*self.spline(times,1)[...,i]
            else:out[...,i]=first*self.spline(times,2)[...,i]+second*self.spline(times,1)[...,i]**2
        return out
