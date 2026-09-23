"""Smooth interpolation inside admitted joint ranges, with exact derivatives.

Only input initialization is moved a tiny distance inside a stop. The resulting
continuous curve never clips a moving angle; foot/contact mechanics must be
replayed after using it.
"""
import numpy as np
from scipy.interpolate import CubicSpline
from scipy.special import expit


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
            fraction=np.clip(fraction,1e-6,1-1e-6)
            latent[:,i]=span*.25*np.log(fraction/(1-fraction))
        self.spline=CubicSpline(times,latent,axis=0,bc_type=bc_type)

    def __call__(self,times,derivative=0):
        if derivative not in (0,1,2):raise ValueError('Only position, velocity and acceleration supported')
        z=self.spline(times);out=self.spline(times,derivative)
        for i,(lo,hi) in self.bounds.items():
            span=hi-lo;s=expit(4*z[...,i]/span)
            if derivative==0:out[...,i]=lo+span*s
            elif derivative==1:out[...,i]=4*s*(1-s)*self.spline(times,1)[...,i]
            else:out[...,i]=4*s*(1-s)*self.spline(times,2)[...,i]+16/span*s*(1-s)*(1-2*s)*self.spline(times,1)[...,i]**2
        return out
