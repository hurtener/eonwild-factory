#!/usr/bin/env python3
"""Turn measured skinned-mesh floor penetration into witness clearance.

Rigid body witnesses do not follow blended skin (deep knee folds, forelimbs
under the chest). This reads a retarget receipt from a previous pass and writes
extra clearance per witness group for the next pass. It is a calibration of the
contact proxy against the actual mesh, not tissue mechanics. Proxies used when
a region has no witness group of its own are recorded in the output.
"""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.ndimage import maximum_filter1d,gaussian_filter1d

# Skin region -> witness group it lifts. A shin has no witnesses: lifting the
# thigh raises the knee end. Forelimbs are cosmetic: the chest rests on them.
PROXY={'shin_l':'thigh_l','shin_r':'thigh_r','forelimb_l':'chest','forelimb_r':'chest'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--retarget',type=Path,required=True,action='append',help='one or more previous-pass receipts; the maximum is used')
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--margin-m',type=float,default=.01)
    ap.add_argument('--dilate-s',type=float,default=.5)
    ap.add_argument('--smooth-s',type=float,default=.12)
    a=ap.parse_args()
    extra={};times=None
    for path in a.retarget:
        m=json.loads(path.read_text())['measurements'];t=np.array([x['time_s'] for x in m])
        if times is None:times=t
        elif len(t)!=len(times) or np.abs(t-times).max()>1e-9:raise ValueError('Receipts must share a timeline')
        for region in m[0]['body_skin_floor_min_m']:
            group=PROXY.get(region,region)
            need=np.maximum(0.,-np.array([x['body_skin_floor_min_m'][region] for x in m])+a.margin_m)
            need[need<=a.margin_m+1e-9]=0.
            extra[group]=np.maximum(extra.get(group,0.),need)
    dt=times[1]-times[0];out={}
    for group,need in extra.items():
        if not need.any():continue
        # Anticipate and release gradually: clearance that appears in one frame
        # would itself be a pop. Never less than what was measured.
        spread=gaussian_filter1d(maximum_filter1d(need,size=max(1,int(round(a.dilate_s/dt)))),a.smooth_s/dt,mode='nearest')
        out[group]=dict(times_s=times.tolist(),values_m=np.maximum(spread,need).tolist())
    a.output.write_text(json.dumps(dict(schema='eonwild.motion.skin-clearance-feedback.v1',
        method='Previous-pass skinned-mesh floor penetration per region, dilated and smoothed in physical time, applied as extra witness clearance',
        proxies=PROXY,margin_m=a.margin_m,dilate_s=a.dilate_s,smooth_s=a.smooth_s,sources=[str(p) for p in a.retarget],
        maximum_extra_m={g:max(v['values_m']) for g,v in out.items()},extra_clearance_m=out),indent=1)+'\n')
    print(json.dumps({g:round(max(v['values_m']),3) for g,v in out.items()}))


if __name__=='__main__':main()
