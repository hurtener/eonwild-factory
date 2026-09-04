# V8.3 target architecture and release plan

## 1. Mission

Ship a productized procedural-animation baseline that can reproduce the approved V8.2 Tarbosaurus walk, recover the valuable V5.5 animation factory capabilities without regressing contact, and expose stable contracts for V9.

V8.3 is not yet the full segment-mass/momentum engine. It is the clean foundation that makes that engine possible.

## 2. Proposed repository layout

```text
src/eonmotion/
  math/
  gltf/
  rig/
  profiles/
  contacts/
  legacy_balance/
  solve/
  overlays/
  transitions/
  bake/
  release/
  validation/

config/v8_3/
  release.yaml
  rig.yaml
  body-posture.yaml
  contact.yaml
  terrain.yaml
  tail.yaml
  jaw.yaml
  transitions.yaml
  clips/

profiles/
  families/heavy-predatory-biped.yaml
  species/tarbosaurus/
  fixtures/

motions/
  contracts/
  programs/
  tarbosaurus/

fixtures/
  v8.2/
  v5.5-reference/
  terrain/

artifacts/v8.3/
  compatibility/
  balanced/
  evidence/

tests/
```

Historical `procedural-animation-toolkit(v*)` directories remain immutable.

## 3. Modular configuration

### `release.yaml`

Declares source artifacts/hashes, output products, deterministic mode, expected clip inventory, allowed channel scopes, evidence requirements, and release tolerances.

### `rig.yaml`

Declares coordinate system, unit scale, semantic role mappings, expected hierarchy, skin/joint inventory, required and optional chains, jaw/foot/toe witnesses, and rig-migration status.

### `body-posture.yaml`

Holds neutral posture, support-phase body-balance proxy limits, pelvis/chest/neck/head authority, preferred stance, and explicit statement that V8.3 balance is not physical COM.

### `contact.yaml`

Holds contact-state definitions, sole/toe witness IDs, stance/load/toe-off schedules, planted-patch tolerances, friction assumptions for fixtures, and IK authority.

### `terrain.yaml`

Holds terrain-query interface, probe radius, normal blending, foot orientation limits, pelvis response limits, and deterministic test surfaces.

### `tail.yaml`

Holds rest sag, proximal/distal stiffness, damping, coupling, lag, parent follow, dynamic limits, warmup, and program-conditioned input gains.

### `jaw.yaml`

Holds resolved jaw/skull chains, calibrated neutral close, witness sets and gaps, hard/preferred gape, and action-specific staging limits.

### `transitions.yaml`

Holds bridge types, duration envelopes, phase/contact matching, pose/velocity tolerances, deadline/fallback behavior, and exact-handoff requirements.

### `clips/*.yaml`

Each clip references a semantic AnimationSpec and reusable MotionProgram. Clip config chooses parameters and entry/exit presets; it does not contain an opaque pile of per-bone keyframes.

## 4. Build pipeline

```text
1. verify input SHAs and immutable directories
2. load and validate modular schemas
3. resolve semantic rig and hierarchy
4. resolve jaw/contact witnesses and profile derivations
5. reproduce exact V8.2 compatibility walk
6. create V8.3 balanced walk candidate
   - propose pelvis/body correction
   - lock loaded foot/toe patches in world space
   - counter-solve leg chains
   - apply V8.2-authoritative trunk stabilization
   - solve damped tail response
7. generate recovered states/actions/terrain fixtures
8. generate endpoint/state-compatible transitions
9. derive root-motion and in-place views from each world plan
10. attach typed phase/contact/gameplay events
11. bake GLB and manifests
12. run mechanical, structural, and schema validation
13. render fixed-camera evidence
14. obtain independent perceptual review
15. write exact inventory and release hashes
```

## 5. Two walk outputs

### Compatibility output

- must reproduce SHA `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5` when using the original lean V8.2 packaging path, or prove sampled/accessor equality when repackaged;
- used as the immutable regression and visual A/B side;
- no V5.5 pelvis or leg changes.

### Balanced V8.3 output

- may alter only declared body/leg channels;
- preserves root displacement, contact timing, and loaded foot/toe witness positions within release tolerances;
- uses V5.5 support-phase ideas as a labeled legacy proxy;
- cannot be accepted merely because a posture metric improves;
- requires side and 3Q approval against V8.2.

## 6. V8.3 clip delivery

The compatibility-complete target is 37 clips: the 21 historical base/action semantics and 16 bridges. The target names and migration rules are recorded in `matrices/v8_3_clip_recovery.yaml`.

### P0

- relaxed walk root/in-place;
- neutral idle;
- alert idle;
- alert walk root/in-place;
- walk start root/in-place;
- walk stop root/in-place;
- grounded committed bite;
- feeding compatibility sequence;
- threat/territorial call;
- all bridges among shipped P0 endpoints.

### P1

- signed-curvature left/right turn presets;
- uneven-terrain deterministic fixture;
- upslope deterministic fixture;
- remaining bridges if any endpoint was staged.

## 7. Runtime contract

Runtime receives:

```text
clip/program semantic
current phase and support state
root pose and velocity
tail state
interruptibility/commitment windows
typed events and event cursor
procedural channel authority
```

Runtime may:

- schedule an authored bridge at a compatible contact phase;
- use bounded snapshot blending for mechanically compatible noncritical changes;
- apply terrain/contact correction within declared authority;
- apply breathing, gaze, exertion, and small variation;
- derive audio/particles/gameplay from typed events.

Runtime may not:

- cancel a non-interruptible action;
- crossfade through an incompatible loaded-foot state;
- invent root displacement;
- hide a failed transition with a teleport;
- change the motion tier without preserving phase and velocity.

## 8. Required V8.3 artifacts

```text
resolved-profile.v8.3.json
rig-resolution-report.json
contact-witness-report.json
jaw-calibration-report.json
animation-manifest.v8.3.json
compatibility GLB
balanced GLB
changed-channel reports
mechanical/contact/joint reports
transition-state report
fixed-camera side videos
fixed-camera three-quarter videos
contact-debug videos
review records
release manifest
SHA256SUMS.txt
```

## 9. Release-blocking gates

- exact pinned inputs;
- historical directories unchanged;
- semantic roles and hierarchy resolve;
- skin/joint/rest deformation integrity;
- compatibility walk passes exact reproduction;
- balanced walk does not regress loaded foot/toe contacts or root motion;
- no contact-critical smoothing;
- all point/window/condition events are valid;
- transition pose, velocity, support, and tail state are compatible;
- root-motion and in-place views reconstruct the same plan;
- every P0 clip passes side and 3Q review;
- no physical COM or biological-capacity claim is made from the legacy proxy;
- independent reviewer approves or blocks release.

## 10. V8.3 completion boundary

Do not begin the airborne V9 power attack merely because a ballistic equation can be coded. V8.3 is complete when the factory, profile, contact, transition, and evidence contracts are stable enough that V9 can change the planner without reorganizing the entire production system again.
