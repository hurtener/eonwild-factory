# V9 gait and foot-artifact audit commands

All commands were run read-only from:

`/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip`

The long dense comparison used a transient Blender `--python-expr` evaluator;
no evaluator source file was written. Its mask definitions, frame range, and
outputs are serialized in [`audit.json`](/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip/reports/V9-GAIT-FOOT-AUDIT-001/audit.json).

## Repository identity

```sh
git rev-parse HEAD
```

Expected output:

```text
195a8b4707997b3309f86f8821217ed1d7e9c22a
```

## Exact artifact hashes

```sh
sha256sum \
  assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb \
  '/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-2-release/procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb'
```

Expected output:

```text
b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03  assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb
a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5  /Volumes/m2-extended-disk/Repos/eonwild-factory-v8-2-release/procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb
```

## Media probes

```sh
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,nb_frames,r_frame_rate,duration -of csv=p=0 reports/PROCEDURAL-ENGINE-V8-3/media/side.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,nb_frames,r_frame_rate,duration -of csv=p=0 reports/PROCEDURAL-ENGINE-V8-3/media/front.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,nb_frames,r_frame_rate,duration -of csv=p=0 reports/PROCEDURAL-ENGINE-V8-3/media/front-three-quarter.mp4
find reports/PROCEDURAL-ENGINE-V8-3/media/phases -maxdepth 1 -type f -name '*.png' | wc -l
```

Expected video output for each file:

```text
960,540,24/1,10.000000,240
```

Expected phase-crop count:

```text
18
```

## Manifest and report JSON parsing

```sh
jq empty reports/PROCEDURAL-ENGINE-V8-3/evidence/media-manifest.json
jq empty reports/V9-GAIT-FOOT-AUDIT-001/audit.json
jq empty reports/V9-GAIT-FOOT-AUDIT-001/narrow-gauge-contract.json
```

The audit JSON can be checked against the pinned identity and key limits with:

```sh
python3 -c 'import json; from pathlib import Path; p=Path("reports/V9-GAIT-FOOT-AUDIT-001/audit.json"); d=json.loads(p.read_text()); assert d["scope"]["head"]=="195a8b4707997b3309f86f8821217ed1d7e9c22a"; assert d["inputs"]["v8_3"]["sha256"]=="b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03"; assert d["inputs"]["v8_2"]["sha256"]=="a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5"; assert d["floorContactCheck"]["candidate"]["maximumPenetrationM"]==0.005569492967027145; print("audit identity and floor check: PASS")'
```

Expected output:

```text
audit identity and floor check: PASS
```

## Blender import and action probe

```sh
/opt/homebrew/bin/blender --background --factory-startup --python-exit-code 1 --python-expr 'import bpy,json; bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath="assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb"); meshes=[o for o in bpy.context.scene.objects if o.type=="MESH" and len(o.data.vertices)>10000]; arms=[o for o in bpy.context.scene.objects if o.type=="ARMATURE"]; print(json.dumps({"blender":"5.2.0 LTS","vertices":len(meshes[-1].data.vertices),"polygons":len(meshes[-1].data.polygons),"action":arms[-1].animation_data.action.name,"frameRange":list(arms[-1].animation_data.action.frame_range)}))'
```

Expected semantic result:

```text
vertices=59169; polygons=102258; action contains ROOTMOTION; frameRange=[0.0,97.66957092285156]
```

## Layer metric extraction

```sh
jq '{pelvis: ."pelvis_balance_pre_ik@1", contact: ."leg_contact_resolve@1"}' reports/PROCEDURAL-ENGINE-V8-3/evidence/layer-metrics.json
```

The audit records exact maxima of `2.5823128856601336e-15 m` foot position
error, `0.000005454337916859027 degrees` foot orientation error,
`4.867755750919621e-8 m` pivot translation, and
`2.1284536214200096 degrees` local leg delta.

## Whitespace and scope checks

```sh
python3 -c 'from pathlib import Path; root=Path("reports/V9-GAIT-FOOT-AUDIT-001"); bad=[]; [bad.append(str(p)) for p in root.rglob("*") if p.is_file() and any(line.endswith((" ","\t")) for line in p.read_text().splitlines())]; assert not bad, bad; print("report trailing whitespace: PASS")'
git diff --check -- reports/V9-GAIT-FOOT-AUDIT-001
git status --short -- reports/V9-GAIT-FOOT-AUDIT-001
```

The status command should list only the five new report files as untracked
until the parent task stages them. Existing untracked report directories are
outside this task and were not modified.

## Recommended executable V9 gates

The following values are the machine-check inputs, not a claim that the
current V8.3 artifact satisfies every future V9 state:

```text
common phases: 120
dense playback: 240 Hz
quantiles: q05, q50, q95
repository witness Euclidean regression: <= 0.002 m
repository witness worst-axis regression: <= 0.0005 m
toe-dominant Euclidean regression: <= 0.0005 m
foot target error: <= 0.00035 m
foot-pivot translation: <= 0.015 m
sole penetration regression: <= 0.0005 m
absolute inherited toe-tip penetration observed: 0.005569492967027145 m
```

For visual proof, render synchronized V8.2-left/V8.3-right side, front,
three-quarter, and locked top-view panes. The top view must overlay contact
centroids, foot headings, COM/capture point, support polygon, local travel
tangent, phase/frame/time identifiers, and a ground surface whose boundary is
outside the crop.
