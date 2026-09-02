"""Small reusable C1 shape-preserving channel interpolator; no rig imports."""
import numpy as np


def curve(time, keys):
    """Carry monotonic waypoint velocity; stop only at this channel's extrema."""
    rows=np.asarray(keys,dtype=float)
    x,y=rows[:,0],rows[:,1]
    h=np.diff(x)
    if len(x)<2 or np.any(h<=0) or not np.isfinite(rows).all():
        raise ValueError('channel needs ordered finite keys')
    sec=np.diff(y)/h
    tangent=np.zeros(len(x))
    for i in range(1,len(x)-1):
        if sec[i-1]*sec[i]>0:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1]
            tangent[i]=(w1+w2)/(w1/sec[i-1]+w2/sec[i])
    if time<=x[0]:return float(y[0])
    if time>=x[-1]:return float(y[-1])
    i=int(np.searchsorted(x,time,side='right')-1)
    u=(time-x[i])/h[i]
    return float((2*u**3-3*u**2+1)*y[i]+(u**3-2*u**2+u)*h[i]*tangent[i]
                 +(-2*u**3+3*u**2)*y[i+1]+(u**3-u**2)*h[i]*tangent[i+1])
