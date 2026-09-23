#!/usr/bin/env python3
"""Measure saved physical contact, pelvis-relative foot track and ankle recovery."""
import argparse,json
from pathlib import Path
import numpy as np


def measure(data):
    frames=data['frames'];t=np.array([r['time_s'] for r in frames]);bw=data['metadata']['mass_kg']*9.80665
    rows={};summary={}
    for side,sign in [('l',-1),('r',1)]:
        load=np.array([sum(c['force_N'][1] for c in r['contacts'] if c['name'].endswith('_'+side))/bw for r in frames])
        ankle=np.array([r['coordinates']['ankle_'+side]['value'] for r in frames])
        rate=np.array([r['coordinates']['ankle_'+side]['speed'] for r in frames])
        local=np.array([np.array(r['bodies']['trunk']['rotation']).T@(np.array(r['bodies']['toe_'+side]['origin'])-r['bodies']['trunk']['origin']) for r in frames])
        world=np.array([r['bodies']['toe_'+side]['origin'] for r in frames])
        loaded=load>.05;swing=load<.03
        contact_speeds=[np.linalg.norm(np.array(c['surface_velocity_mps'])[[0,2]]) for r in frames for c in r['contacts'] if c['name'].endswith('_'+side) and c['force_N'][1]>.05*bw]
        rows[side]=dict(time_s=t.tolist(),load_BW=load.tolist(),ankle_deg=np.rad2deg(ankle).tolist(),ankle_rate_deg_s=np.rad2deg(rate).tolist(),foot_forward_m=local[:,0].tolist(),foot_outward_m=(sign*local[:,2]).tolist(),foot_world=world.tolist())
        def mm(a,mask):return [float(a[mask].min()),float(a[mask].max())] if mask.any() else None
        summary[side]=dict(loaded_foot_outward_range_m=mm(sign*local[:,2],loaded),loaded_foot_forward_range_m=mm(local[:,0],loaded),swing_ankle_angle_range_deg=mm(np.rad2deg(ankle),swing),swing_peak_ankle_rate_deg_s=float(np.max(abs(np.rad2deg(rate[swing])))) if swing.any() else None,peak_ankle_rate_deg_s=float(np.max(abs(np.rad2deg(rate)))),loaded_contact_speed_p95_mps=float(np.quantile(contact_speeds,.95)) if contact_speeds else None)
    return {'schema':'eonwild.moco.support-audit.v1','classification':'Saved state/contact audit, not independent forward simulation','summary':summary,'rows':rows}


def main():
    p=argparse.ArgumentParser();p.add_argument('replay',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--compare',type=Path);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    result=measure(json.loads(a.replay.read_text()));(a.output/'support-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],indent=2))
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(14,7),layout='constrained')
    inputs=[('candidate',result,'#168074')]
    if a.compare:inputs.insert(0,('C50 baseline',measure(json.loads(a.compare.read_text())),'#9c6a45'))
    for label,data,color in inputs:
        for i,side in enumerate(('l','r')):
            r=data['rows'][side];t=r['time_s'];ls='-' if label=='candidate' else '--'
            axes[i,0].plot(r['foot_forward_m'],r['foot_outward_m'],ls,color=color,label=label)
            axes[i,1].plot(t,r['ankle_deg'],ls,color=color,label=label)
            axes[i,2].plot(t,r['ankle_rate_deg_s'],ls,color=color,label=label)
    for i,side in enumerate(('Left','Right')):
        axes[i,0].set(xlabel='Foot forward from pelvis (m)',ylabel=f'{side}: outward from pelvis (m)')
        axes[i,1].set(xlabel='Time (s)',ylabel='Ankle coordinate (deg)')
        axes[i,2].set(xlabel='Time (s)',ylabel='Ankle angular speed (deg/s)')
        for ax in axes[i]:ax.grid(alpha=.2);ax.legend()
    fig.suptitle('Physical replay audit — pelvis-frame foot path and ankle recovery\nHalf-stride includes opposite support/swing phases; no pose correction')
    fig.savefig(a.output/'support-ankle.png',dpi=150);plt.close(fig)

if __name__=='__main__':main()
