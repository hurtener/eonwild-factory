"""Loop-safe tangent-space quaternion polish filters."""
from __future__ import annotations
import numpy as np
from scipy.signal import savgol_filter
from scipy.spatial.transform import Rotation
from eonproc_v3.gltf_io import quaternion_continuity

def smooth_quaternions(values, loop=False, window=7, order=3):
    values=quaternion_continuity(np.asarray(values,dtype=np.float64)); n=len(values)
    w=min(window,n if n%2 else n-1); w=max(3,w if w%2 else w-1)
    if w<=order: return values.copy(),0.0
    q=Rotation.from_quat(values); ref=q[0]; rv=(ref.inv()*q).as_rotvec()
    if loop:
        core=rv[:-1]; pad=w//2; ext=np.concatenate([core[-pad:],core,core[:pad]])
        filt=savgol_filter(ext,w,order,axis=0,mode="interp")[pad:pad+len(core)]; filt=np.concatenate([filt,filt[:1]])
    else:
        filt=savgol_filter(rv,w,order,axis=0,mode="interp"); filt[0]=rv[0]; filt[-1]=rv[-1]
    out=quaternion_continuity((ref*Rotation.from_rotvec(filt)).as_quat())
    delta=Rotation.from_quat(values).inv()*Rotation.from_quat(out)
    return out,float(np.degrees(np.linalg.norm(delta.as_rotvec(),axis=1)).max())
