#!/usr/bin/env python3
"""Select already-replayed native states for diagnostic skin export.

This does not repair dynamics or certify intersample physics. The original dense
Moco-resampling diagnostic is retained separately, including all its failures.
The selected skin interpolates native bounded poses linearly, rather than using
an unconstrained resampling spline as a second motion author.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import numpy as np


def select(data):
    rows=data['nodes']; meta=data['metadata']; times=np.array([r['time_s'] for r in rows])
    if len(rows)<3 or np.max(np.diff(times))>1/24+1e-8:
        raise ValueError('Native sampling must be at least 24 Hz throughout')
    for name,limits in meta['coordinates'].items():
        q=np.array([r['coordinates'][name]['value'] for r in rows]);lo,hi=limits['bounds_rad']
        if not np.isfinite(q).all() or np.min(q)<lo-1e-10 or np.max(q)>hi+1e-10:
            raise ValueError('Native source violates admitted bounds: '+name)
    mass=meta['mass_kg'];bw=mass*9.80665
    force=np.array([[c['force_N'] for c in r['contacts']] for r in rows]).sum(axis=1)
    velocity=np.array([r['com_velocity_mps'] for r in rows]); acceleration=np.gradient(velocity,times,axis=0)
    balance=mass*(acceleration+[0,9.80665,0])-force
    slips=[float(np.linalg.norm(np.array(c['surface_velocity_mps'])[[0,2]])) for r in rows for c in r['contacts'] if c['force_N'][1]>.05*bw]
    report=copy.deepcopy(data['report'])
    report.update(sample_scope='Exact native saved-state replay; no new resampling. Original unconstrained dense diagnostic retained separately; not forward integration or continuous-time acceptance.',samples=len(rows),
        vertical_force_BW_range=[float(force[:,1].min()/bw),float(force[:,1].max()/bw)],
        mean_vertical_force_BW=float(np.trapezoid(force[:,1],times)/((times[-1]-times[0])*bw)),
        airborne_fraction_under_0_05_BW=float(np.mean(force[:,1]<.05*bw)),
        max_penetration_m=max(c['penetration_m'] for r in rows for c in r['contacts']),
        max_loaded_surface_speed_mps=max(slips,default=0),p95_loaded_surface_speed_mps=float(np.percentile(slips,95)) if slips else 0,
        rms_dense_force_balance_BW=float(np.sqrt(np.mean(balance[2:-2,:2]**2))/bw),
        max_dense_force_balance_BW=float(np.max(np.linalg.norm(balance[2:-2,:2],axis=1))/bw),
        rms_dense_3d_force_balance_BW=float(np.sqrt(np.mean(balance[2:-2]**2))/bw),
        max_dense_3d_force_balance_BW=float(np.max(np.linalg.norm(balance[2:-2],axis=1))/bw),
        max_activation=max(abs(v) for r in rows for v in r['activations'].values()),
        knee_opening_deg={s:[float(min(180+np.degrees(r['coordinates']['knee_'+s]['value']) for r in rows)),float(max(180+np.degrees(r['coordinates']['knee_'+s]['value']) for r in rows))] for s in ['l','r']})
    for frame in meta.get('clearance_frames',[]):
        report['bone_clearance'][frame['path']]={'minimum_height_m':frame['minimum_height_m'],'minimum_margin_m':min(r['clearance_heights_m'][frame['path']]-frame['minimum_height_m'] for r in rows)}
    return dict(metadata=meta,report=report,nodes=rows,frames=rows,source_dense_diagnostic=data['report'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():raise FileExistsError('Preserve existing output')
    result=select(json.loads(a.source.read_text()))
    result['native_export']={'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),'coordinates_changed':False,'anatomical_limits_changed':False,'physical_acceptance':'NOT_ACCEPTED'}
    a.output.write_text(json.dumps(result,separators=(',',':'))+'\n')
