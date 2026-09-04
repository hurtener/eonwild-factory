#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(HERE))
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import AnatomicalBasis,SemanticMap
from eonproc_v4.animation_reader import AnimationPackReader

def sha(path:Path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source',required=True); ap.add_argument('--glb',required=True); ap.add_argument('--bone-map',required=True); ap.add_argument('--report',required=True); ap.add_argument('--manifest',required=True); ap.add_argument('--profile',required=True); ap.add_argument('--pivots',required=True); ap.add_argument('--baked-ground',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
    report=json.loads(Path(a.report).read_text()); manifest=json.loads(Path(a.manifest).read_text()); profile=json.loads(Path(a.profile).read_text()); piv=json.loads(Path(a.pivots).read_text()); baked=json.loads(Path(a.baked_ground).read_text())
    names={c['name'] for c in manifest['clips']}; by={c['name']:c for c in manifest['clips']}; clips=report['clips']
    normal={'PROC_NORMAL_ATTACK_V8_1','PROC_NORMAL_ATTACK_MIRRORED_V8_1'}; power={'PROC_POWER_ATTACK_V8_1','PROC_POWER_ATTACK_MIRRORED_V8_1'}
    required_events={'takeoff','apex','bite_contact','landing','second_foot_catch','weight_arrest','feeding_ready'}
    power_diag=[clips[n]['diagnostics']['power_attack_v8_1'] for n in sorted(power)]
    asset=GlbAsset(a.glb); sem=SemanticMap.load(a.bone_map); basis=AnatomicalBasis.gltf_y_up(asset,sem); reader=AnimationPackReader(asset); root=sem.bone('root'); landing_dynamics={}
    source_asset=GlbAsset(a.source); before_ibm=source_asset.skin_data()[1]; after_ibm=asset.skin_data()[1]; independently_changed_slots=np.flatnonzero(np.max(np.abs(after_ibm-before_ibm),axis=(1,2))>1e-7).astype(int).tolist()
    for n in power:
        anim=reader.animation(n); values=anim.translations[root]; dt=float(np.median(np.diff(anim.times))); velocity=np.gradient(values,dt,axis=0); acceleration=np.gradient(velocity,dt,axis=0); lo=int(.43*(len(values)-1)); hi=int(.62*(len(values)-1))+1
        landing_dynamics[n]={'maximumForwardVelocityMps':float(np.max(np.abs(velocity[lo:hi]@basis.forward))),'maximumVerticalVelocityMps':float(np.max(np.abs(velocity[lo:hi]@basis.up))),'maximumAccelerationMps2':float(np.max(np.linalg.norm(acceleration[lo:hi],axis=1)))}
    hinge=[clips[n]['diagnostics']['jaw_hinge_v8_1']['maximum_off_hinge_degrees'] for n in names if n in clips and 'jaw_hinge_v8_1' in clips[n]['diagnostics']]
    transitions=[n for n in names if 'POWER_ATTACK' in n and '_TO_' in n]
    all_gates=[bool(v) for c in clips.values() for v in c['diagnostics'].get('quality_gates',{}).values()]
    checks={
      'automated_report_pass':report['automated_quality_pass'] is True,
      'separate_normal_catalog':normal<=names,
      'separate_power_catalog':power<=names,
      'mirrored_power_events':all(required_events<={e['type'] for e in by[n]['events']} for n in power),
      'source_grounded_airborne_window':baked['status']=='PASS' and all(.17<=d['measuredAirborneDurationSeconds']<=.21 for d in baked['power'].values()),
      'root_vertical_apex':all(.05<=d['root_vertical_apex_m']/1.3722147167<=.09 for d in power_diag),
      'persistent_forward_delivery':all(.30<=d['root_forward_delivery_m']/1.3722147167<=.45 for d in power_diag),
      'zero_power_penetration':all(d['worstPenetrationAcrossAllKeysM']<=1e-5 for d in baked['power'].values()),
      'ordered_landing':all(d['phase_fractions']['lead_land']<d['phase_fractions']['second_catch']<d['phase_fractions']['arrest_end'] for d in power_diag),
      'bounded_landing_velocity':all(d['maximumForwardVelocityMps']<=3.0 and d['maximumVerticalVelocityMps']<=2.0 for d in landing_dynamics.values()),
      'bounded_landing_acceleration':all(d['maximumAccelerationMps2']<=35.0 for d in landing_dynamics.values()),
      'jaw_closed_at_contact':all(abs(d['jaw_additive_at_contact_deg'])<=1.5 for d in power_diag),
      'jaw_local_hinge_geometric':bool(hinge) and max(hinge)<=.25,
      'power_to_eat_exact_endpoints':all(clips[n]['diagnostics'].get('exact_endpoints') for n in transitions if '_TO_EAT_' in n),
      'all_quality_gates':all(all_gates),
      'canonical_profile_hash_matches':sha(Path(a.profile))==sha(Path(a.report).parent/'resolved-profile-v8.1.json'),
      'pivot_fraction_90_percent':piv['gapFraction']==.9,
      'pivot_only_two_inverse_binds':piv['inverseBindSlotsChanged']==2 and len(independently_changed_slots)==2 and piv.get('changedInverseBindSlots')==independently_changed_slots,
      'pivot_toe_roots_fixed':piv['maximumToeRootOriginErrorM']<1e-6,
      'pivot_rest_mesh_unchanged':piv['maximumRestSkinnedVertexErrorM']<1e-6,
    }
    out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'profileSha256':sha(Path(a.profile)),'clipCount':len(names),'maximumJawOffHingeDegrees':max(hinge),'powerDiagnostics':power_diag,'measuredBakedFlight':{name:{key:value for key,value in data.items() if key!='keyMeasurements'} for name,data in baked['power'].items()},'landingDynamics':landing_dynamics,'independentlyChangedInverseBindSlots':independently_changed_slots,'pivotCalibration':piv}
    Path(a.output).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2)); return 0 if out['status']=='PASS' else 1
if __name__=='__main__': raise SystemExit(main())
