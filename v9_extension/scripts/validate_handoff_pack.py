#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, subprocess, sys
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
errors=[]; checks=[]

def check(cond,msg):
    if not cond: errors.append(msg)
    return bool(cond)

def load_yaml(p): return yaml.safe_load(p.read_text())

required=[
 'README_FIRST.md','docs/00_PRODUCT_AND_MOTION_CONTEXT.md','docs/01_VERSION_LINEAGE_AND_BASELINES.md',
 'docs/02_V5_5_TO_V8_3_RECOVERY_PLAN.md','docs/03_V8_3_TARGET_ARCHITECTURE_AND_RELEASE.md',
 'docs/03A_V8_3_CLIP_RECOVERY_CATALOG.md','docs/04_GLOBAL_ANIMATION_CONTRACT.md','docs/05_V9_BIOMECHANICAL_ENGINE.md',
 'docs/06_RUNTIME_METADATA_AND_SPEC_FORMAT.md','docs/07_IMPLEMENTATION_WORKSTREAMS.md',
 'docs/08_VALIDATION_AND_EVIDENCE.md','docs/09_GOAL_PROMPT.md','docs/10_OPEN_DECISIONS_AND_BOUNDARIES.md',
 'docs/animations/ALL_29_ANIMATIONS.md','matrices/v5_5_to_v8_3_recovery.yaml',
 'matrices/v8_3_clip_recovery.yaml','prompts/GOAL_PROMPT.txt','validation/v8_3-acceptance-gates.yaml'
]
found=sum((ROOT/x).is_file() for x in required)
check(found==len(required),f'required files {found}/{len(required)}')
checks.append({'id':'required_files','found':found,'expected':len(required)})

rec=load_yaml(ROOT/'matrices/v5_5_to_v8_3_recovery.yaml')
items=rec['items']; ids=[x['id'] for x in items]
check(len(items)>=50,f'recovery matrix too small: {len(items)}')
check(len(ids)==len(set(ids)),'duplicate recovery ids')
check(all(x.get('required_evidence') for x in items),'recovery item lacks evidence')
check(all(x.get('preserved_invariants') for x in items),'recovery item lacks invariants')
checks.append({'id':'recovery_matrix','items':len(items),'unique_ids':len(set(ids))})

cm=load_yaml(ROOT/'matrices/v8_3_clip_recovery.yaml')
check(len(cm['base_clips'])==21,f"expected 21 base clips, got {len(cm['base_clips'])}")
check(len(cm['transitions'])==16,f"expected 16 transitions, got {len(cm['transitions'])}")
checks.append({'id':'v8_3_clip_matrix','base_clips':len(cm['base_clips']),'transitions':len(cm['transitions'])})

cat=load_yaml(ROOT/'motions/tarbosaurus/catalog.yaml')
check(len(cat['animations'])==29,f"expected 29 animations, got {len(cat['animations'])}")
full=(ROOT/'docs/animations/ALL_29_ANIMATIONS.md').read_text()
nums=[int(x) for x in re.findall(r'^## (\d{2}) — ',full,re.M)]
check(nums==list(range(1,30)),f'combined catalog headings not 01..29: {nums}')
for fn,lo,hi in [
 ('01_STATES_LOCOMOTION_AND_TRANSITIONS.md',1,10),('02_PERCEPTION_AND_COMBAT.md',11,17),
 ('03_FEEDING_DRINKING_AND_GROUND_POSTURE.md',18,24),('04_INJURY_CALLS_AND_DEATH.md',25,29)]:
    t=(ROOT/'docs/animations'/fn).read_text(); got=[int(x) for x in re.findall(r'^## (\d{2}) — ',t,re.M)]
    check(got==list(range(lo,hi+1)),f'{fn} headings wrong: {got}')
checks.append({'id':'animation_catalog','yaml':len(cat['animations']),'markdown':len(nums)})

prompt=(ROOT/'prompts/GOAL_PROMPT.txt').read_text().strip()
check(len(prompt)<4000,f'goal prompt exceeds 4000 chars: {len(prompt)}')
for term in ['V8.3','V9','V8.2','V5.5','independent','loaded foot','root-motion']:
    check(term.lower() in prompt.lower(),f'goal prompt missing {term}')
checks.append({'id':'goal_prompt','characters':len(prompt)})

refs=list((ROOT/'references/game-design').glob('*.md'))
check(len(refs)==12,f'expected 12 canonical game references, got {len(refs)}')
checks.append({'id':'game_design_references','count':len(refs)})

# Validate all yaml/json can parse, excluding generated reports that are still valid json anyway.
parse_count=0
for p in ROOT.rglob('*'):
    if not p.is_file(): continue
    try:
        if p.suffix in {'.yaml','.yml'}: yaml.safe_load(p.read_text()); parse_count+=1
        elif p.suffix=='.json': json.loads(p.read_text()); parse_count+=1
    except Exception as exc:
        errors.append(f'parse error {p.relative_to(ROOT)}: {exc}')
checks.append({'id':'structured_files_parse','count':parse_count})

# Run original V9 structural validator.
proc=subprocess.run([sys.executable,str(ROOT/'scripts/validate_spec_pack.py'),'--root',str(ROOT),'--output',str(ROOT/'validation-report.json')],capture_output=True,text=True)
check(proc.returncode==0,'V9 spec validator failed: '+proc.stdout[-2000:]+proc.stderr[-1000:])
checks.append({'id':'v9_spec_validator','returncode':proc.returncode})

report={'schema':'eonwild.handoff_pack_validation.v1','status':'PASS' if not errors else 'FAIL','checks':checks,'error_count':len(errors),'errors':errors,
        'scope':'Structural completeness and internal consistency only; no generated V8.3/V9 animation or perceptual approval is claimed.'}
(ROOT/'handoff-validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(0 if not errors else 1)
