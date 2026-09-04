#!/usr/bin/env python3
"""V8-to-V8.1 walk regression with an explicit allowed-change seam."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parents[1]/'scripts';sys.path.insert(0,str(HERE))
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap
from eonproc_v4.animation_reader import AnimationPackReader
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--v8-glb',required=True);ap.add_argument('--v8-report',required=True);ap.add_argument('--v8-1-glb',required=True);ap.add_argument('--v8-1-report',required=True);ap.add_argument('--bone-map',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();sem=SemanticMap.load(a.bone_map);root=sem.bone('root');r8=AnimationPackReader(GlbAsset(a.v8_glb)).animation('PROC_WALK_RELAXED_V8_ROOTMOTION');r81=AnimationPackReader(GlbAsset(a.v8_1_glb)).animation('PROC_WALK_RELAXED_V8_1_ROOTMOTION');p8=json.loads(Path(a.v8_report).read_text())['clips']['PROC_WALK_RELAXED_V8_ROOTMOTION']['diagnostics'];p81=json.loads(Path(a.v8_1_report).read_text())['clips']['PROC_WALK_RELAXED_V8_1_ROOTMOTION']['diagnostics'];root_error=float(np.max(np.abs(r8.translations[root]-r81.translations[root])));checks={'same_duration':abs(r8.duration-r81.duration)<1e-9,'same_samples':len(r8.times)==len(r81.times),'same_timeline':bool(np.array_equal(r8.times,r81.times)),'same_root_delivery_track':root_error<=1e-7,'same_phase_cycles':p8.get('phase_advance_cycles')==p81.get('phase_advance_cycles'),'same_mean_speed':abs(p8.get('mean_speed_mps',0)-p81.get('mean_speed_mps',0))<=1e-9,'v8_1_contact_gates_pass':all(p81.get('quality_gates',{}).values())};out={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'maximumRootTrackErrorM':root_error,'allowedRotationDifferences':['pelvis/spine/neck/head from accepted neutral-chain correction','foot/ankle/toe and upstream IK from accepted 90% foot-pivot calibration'],'forbiddenDifferences':['timeline','cycle phase count','root delivery','mean speed','contact gate regression']};Path(a.output).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2));return 0 if out['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
