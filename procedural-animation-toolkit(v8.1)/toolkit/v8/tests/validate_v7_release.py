#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,struct
from pathlib import Path

REQUIRED_BASE={
'PROC_WALK_RELAXED_V7_ROOTMOTION','PROC_WALK_RELAXED_V7_INPLACE',
'PROC_WALK_UNEVEN_TERRAIN_V7_ROOTMOTION','PROC_WALK_UNEVEN_TERRAIN_V7_INPLACE',
'PROC_WALK_UPSLOPE_V7_ROOTMOTION','PROC_WALK_UPSLOPE_V7_INPLACE',
'PROC_TURN_LEFT_35_V7_ROOTMOTION','PROC_TURN_LEFT_35_V7_INPLACE',
'PROC_TURN_RIGHT_35_V7_ROOTMOTION','PROC_TURN_RIGHT_35_V7_INPLACE',
'PROC_START_WALK_V7_ROOTMOTION','PROC_START_WALK_V7_INPLACE',
'PROC_BRAKE_TO_IDLE_V7_ROOTMOTION','PROC_BRAKE_TO_IDLE_V7_INPLACE',
'PROC_ALERT_WALK_V7_ROOTMOTION','PROC_ALERT_WALK_V7_INPLACE',
'PROC_IDLE_BREATH_V7','PROC_ALERT_IDLE_V7','PROC_EAT_LOOP_V7',
'PROC_BITE_ATTACK_V7','PROC_BITE_ATTACK_MIRRORED_V7','PROC_ROAR_V7'}


def glb_json(path:Path):
    raw=path.read_bytes();magic,version,total=struct.unpack_from('<4sII',raw,0)
    assert magic==b'glTF' and version==2 and total==len(raw)
    n,kind=struct.unpack_from('<II',raw,12);assert kind==0x4E4F534A
    return json.loads(raw[20:20+n].decode('utf-8'))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--glb',required=True);ap.add_argument('--report',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    gj=glb_json(Path(a.glb));report=json.loads(Path(a.report).read_text());manifest=json.loads(Path(a.manifest).read_text())
    animations=gj.get('animations',[]);names=[x.get('name') for x in animations];name_set=set(names)
    node_names={i:n.get('name','') for i,n in enumerate(gj['nodes'])};pelvis_node=next(i for i,n in node_names.items() if n=='Bone_001')
    per_anim={}
    for anim in animations:
        paths={(ch['target']['node'],ch['target']['path']) for ch in anim['channels']}
        per_anim[anim['name']]={'pelvis_translation':(pelvis_node,'translation') in paths,'channel_count':len(anim['channels'])}
    turn_diag={name:report['clips'][name]['diagnostics'].get('turn_mass_lead',{}) for name in ('PROC_TURN_LEFT_35_V7_ROOTMOTION','PROC_TURN_RIGHT_35_V7_ROOTMOTION')}
    base_without_pelvis=sorted(name for name in REQUIRED_BASE if name in per_anim and not per_anim[name]['pelvis_translation'])
    all_gates=[]
    failed=[]
    for name,payload in report.get('clips',{}).items():
        gates=payload.get('diagnostics',{}).get('quality_gates',{})
        for gate,val in gates.items():
            all_gates.append((name,gate,bool(val)))
            if not val: failed.append({'clip':name,'gate':gate})
    result={
      'status':'PASS' if (len(animations)==40 and REQUIRED_BASE<=name_set and not base_without_pelvis and not failed and all(d.get('peak_head_lead_deg',0)>=5 and d.get('peak_neck_lead_deg',0)>=3 and d.get('peak_tail_counter_target_deg',0)>=2 for d in turn_diag.values())) else 'FAIL',
      'animation_count':len(animations),'unique_animation_count':len(name_set),'skin_joint_count':len(gj['skins'][0]['joints']),
      'required_base_missing':sorted(REQUIRED_BASE-name_set),'base_clips_without_pelvis_translation':base_without_pelvis,
      'turn_diagnostics':turn_diag,'failed_quality_gates':failed,'manifest_clip_count':len(manifest.get('clips',manifest.get('animations',[]))),
      'all_channel_targets_valid':all(0<=ch['target']['node']<len(gj['nodes']) for anim in animations for ch in anim['channels']),
      'all_timelines_nonempty':all(anim['samplers'] for anim in animations),'report_status':report.get('status'),
    }
    Path(a.output).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='PASS' else 1)
if __name__=='__main__':main()
