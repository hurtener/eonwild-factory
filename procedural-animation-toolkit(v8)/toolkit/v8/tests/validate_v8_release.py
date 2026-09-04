#!/usr/bin/env python3
"""Validate the final 40-clip V8 GLB, reports and action/turn quality gates."""
from __future__ import annotations
import argparse,json,struct
from pathlib import Path

REQUIRED_BASE={
'PROC_WALK_RELAXED_V8_ROOTMOTION','PROC_WALK_RELAXED_V8_INPLACE','PROC_WALK_UNEVEN_TERRAIN_V8_ROOTMOTION','PROC_WALK_UNEVEN_TERRAIN_V8_INPLACE','PROC_WALK_UPSLOPE_V8_ROOTMOTION','PROC_WALK_UPSLOPE_V8_INPLACE','PROC_TURN_LEFT_35_V8_ROOTMOTION','PROC_TURN_LEFT_35_V8_INPLACE','PROC_TURN_RIGHT_35_V8_ROOTMOTION','PROC_TURN_RIGHT_35_V8_INPLACE','PROC_START_WALK_V8_ROOTMOTION','PROC_START_WALK_V8_INPLACE','PROC_BRAKE_TO_IDLE_V8_ROOTMOTION','PROC_BRAKE_TO_IDLE_V8_INPLACE','PROC_ALERT_WALK_V8_ROOTMOTION','PROC_ALERT_WALK_V8_INPLACE','PROC_IDLE_BREATH_V8','PROC_ALERT_IDLE_V8','PROC_EAT_LOOP_V8','PROC_BITE_ATTACK_V8','PROC_BITE_ATTACK_MIRRORED_V8','PROC_ROAR_V8'}

def glb_json(path:Path):
 raw=path.read_bytes();magic,version,total=struct.unpack_from('<4sII',raw,0);assert magic==b'glTF' and version==2 and total==len(raw);n,kind=struct.unpack_from('<II',raw,12);assert kind==0x4E4F534A;return json.loads(raw[20:20+n].decode('utf-8'))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--glb',required=True);ap.add_argument('--report',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
 gj=glb_json(Path(a.glb));report=json.loads(Path(a.report).read_text());manifest=json.loads(Path(a.manifest).read_text());animations=gj.get('animations',[]);names=[x.get('name') for x in animations];name_set=set(names);node_names={i:n.get('name','') for i,n in enumerate(gj['nodes'])};pelvis_node=next(i for i,n in node_names.items() if n=='Bone_001')
 per_anim={}
 for anim in animations:
  paths={(ch['target']['node'],ch['target']['path']) for ch in anim['channels']};per_anim[anim['name']]={'pelvis_translation':(pelvis_node,'translation') in paths,'channel_count':len(anim['channels'])}
 base_without_pelvis=sorted(name for name in REQUIRED_BASE if name in per_anim and not per_anim[name]['pelvis_translation'])
 failed=[]
 for name,payload in report.get('clips',{}).items():
  for gate,val in payload.get('diagnostics',{}).get('quality_gates',{}).items():
   if not bool(val):failed.append({'clip':name,'gate':gate})
 turns=[report['clips'][n]['diagnostics'] for n in ('PROC_TURN_LEFT_35_V8_ROOTMOTION','PROC_TURN_RIGHT_35_V8_ROOTMOTION')]
 bites=[report['clips'][n]['diagnostics'].get('power_attack_v8',{}) for n in ('PROC_BITE_ATTACK_V8','PROC_BITE_ATTACK_MIRRORED_V8')]
 eat=report['clips']['PROC_EAT_LOOP_V8']['diagnostics'].get('feeding_expression_v8',{})
 checks={
  'animation_count_40':len(animations)==40,'unique_names':len(name_set)==len(names),'required_base_present':REQUIRED_BASE<=name_set,'all_base_pelvis_channels':not base_without_pelvis,'all_report_gates':not failed,'skin_joint_count_75':len(gj['skins'][0]['joints'])==75,'all_channel_targets_valid':all(0<=ch['target']['node']<len(gj['nodes']) for anim in animations for ch in anim['channels']),'manifest_count_matches':len(manifest.get('clips',[]))==len(animations),
  'turn_head_authored_ge_12':all(d.get('turn_expression_v8',{}).get('authored_peak_head_relative_deg',0)>=12 for d in turns),
  'turn_neck_authored_ge_7':all(d.get('turn_expression_v8',{}).get('authored_peak_neck_relative_deg',0)>=7 for d in turns),
  'attack_two_step_both_sides':all(d.get('sequential_catch_steps') for d in bites),'attack_closed_at_contact':all(abs(d.get('jaw_additive_at_contact_deg',99))<=1.5 for d in bites),'attack_closed_at_end':all(abs(d.get('jaw_additive_at_end_deg',99))<=1.5 for d in bites),'attack_delivery_both_sides':all(d.get('root_delivery_distance_m',0)>0.25 for d in bites),
  'feeding_three_events':eat.get('bite_event_count',0)>=3,'feeding_head_expression':eat.get('head_yaw_span_deg',0)>=6,'feeding_late_gape':bool(eat.get('late_gape_then_contact_closure')),
 }
 result={'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'animation_count':len(animations),'unique_animation_count':len(name_set),'skin_joint_count':len(gj['skins'][0]['joints']),'required_base_missing':sorted(REQUIRED_BASE-name_set),'base_clips_without_pelvis_translation':base_without_pelvis,'failed_quality_gates':failed,'action_diagnostics':{'bite_left':bites[0],'bite_right':bites[1],'eat':eat},'report_status':report.get('status')}
 Path(a.output).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='PASS' else 1)
if __name__=='__main__':main()
