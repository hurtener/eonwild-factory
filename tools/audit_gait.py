#!/usr/bin/env python3
"""Usage: audit_gait.py <replay.json> <t0> <t1>. Compares stride with Alexander dynamic similarity (stride/hip = 2.3 Fr^0.3).
Gait audit over a steady window: body oscillations, stride, duty factor, foot slip, dynamic similarity."""
import json,sys,numpy as np
path,t0,t1=sys.argv[1],float(sys.argv[2]),float(sys.argv[3])
r=json.load(open(path));fr=[f for f in r['frames'] if t0<=f['time_s']<=t1];t=np.array([f['time_s'] for f in fr])
meta=r['metadata'];L=sum(meta['segment_lengths_m']);bw=meta['mass_kg']*9.80665
C=lambda n:np.array([f['coordinates'][n]['value'] for f in fr])
B=lambda b:np.array([f['bodies'][b]['origin'] for f in fr])
hip=.5*(B('thigh_l')+B('thigh_r'));fwd=B('head')-B('trunk');
v=np.gradient(hip[:,0],t);speed=float(np.median(np.abs(v)))
def amp(x):return float(np.percentile(x,95)-np.percentile(x,5))
out=dict(window_s=[t0,t1],speed_mps=speed,leg_length_m=L,hip_height_m=float(hip[:,1].mean()),
 froude=speed**2/(9.80665*hip[:,1].mean()),
 pelvis_vertical_excursion_m=amp(hip[:,1]),pelvis_lateral_excursion_m=amp(hip[:,2]),
 pitch_deg=amp(np.degrees(C('pitch'))),roll_deg=amp(np.degrees(C('roll'))),yaw_deg=amp(np.degrees(C('yaw'))))
for n in ('neck','head','chest','tail_0','tail_0_yaw','tail_3','tail_3_yaw','tail_6_yaw','knee_l','ankle_l','hip_l','mtp_l'):
    try:x=C(n);out[n+'_range_deg']=[round(float(np.degrees(x.min())),1),round(float(np.degrees(x.max())),1)]
    except KeyError:pass
# head world stability
head=B('head');out['head_vertical_excursion_m']=amp(head[:,1]);out['head_lateral_excursion_m']=amp(head[:,2])
tip=[k for k in fr[0]['bodies'] if k.startswith('tail_')];tip=sorted(tip,key=lambda k:int(k.split('_')[1]))[-1]
out['tail_tip_lateral_excursion_m']=amp(B(tip)[:,2]);out['tail_tip_vertical_excursion_m']=amp(B(tip)[:,1])
# contacts per side
for s in ('l','r'):
    F=np.array([sum(c['force_N'][1] for c in f['contacts'] if c['name'].endswith('_'+s) and 'pad' in c['name']) for f in fr])
    load=F>.05*bw;out['duty_factor_'+s]=float(load.mean())
    slip=[max(abs(c['surface_velocity_mps'][0]),abs(c['surface_velocity_mps'][2])) for f in fr for c in f['contacts'] if c['name'].endswith('_'+s) and 'pad' in c['name'] and c['force_N'][1]>.05*bw]
    out['loaded_slip_p95_mps_'+s]=float(np.percentile(slip,95)) if slip else None
    on=np.flatnonzero(load[1:]&~load[:-1])
    if len(on)>1:out['stride_period_s_'+s]=float(np.median(np.diff(t[on+1])))
sp=np.nanmean([out.get('stride_period_s_l',np.nan),out.get('stride_period_s_r',np.nan)])
out['stride_length_m']=float(speed*sp);out['relative_stride_length']=out['stride_length_m']/out['hip_height_m']
out['alexander_expected_relative_stride']=2.3*out['froude']**0.3
Fz=np.array([sum(c['force_N'][1] for c in f['contacts']) for f in fr])/bw;out['ground_force_BW_mean_min_max']=[float(Fz.mean()),float(Fz.min()),float(Fz.max())]
print(json.dumps({k:(round(v,3) if isinstance(v,float) else v) for k,v in out.items()},indent=1))
