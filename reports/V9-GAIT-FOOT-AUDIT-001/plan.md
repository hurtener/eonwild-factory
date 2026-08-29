# V9 gait and foot-artifact audit plan

## Bounded task

Perform an independent, read-only audit of the V8.3 GLB, semantic rig and
contact layers, final-skinned witnesses, synchronized side/front/three-quarter
media, and all eighteen phase crops. Compare the pinned V8.3 artifact with the
approved V8.2 GLB at exact common phases. Classify foot-adjacent observations
as motion, skinning, lighting/occlusion, evidence setup, or inherited contact
behavior. Separately verify the primary-source claims in PMC4108409,
PMC2752196, and PMC5550975, then specify a normalized, family-level
narrow-gauge contract with explicit uncertainty and gait-state boundaries.

This task writes evidence documentation only. It does not edit engine code,
motion programs, schemas, GLBs, media, branches, or commits.

Pinned inputs:

- Worktree: `/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip`
- V8.3 HEAD: `195a8b4707997b3309f86f8821217ed1d7e9c22a`
- V8.3 GLB: `assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb`
- V8.2 GLB: `/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-2-release/procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb`

## Intended files

Only these files in this report directory are in scope:

- `reports/V9-GAIT-FOOT-AUDIT-001/plan.md`
- `reports/V9-GAIT-FOOT-AUDIT-001/audit.md`
- `reports/V9-GAIT-FOOT-AUDIT-001/audit.json`
- `reports/V9-GAIT-FOOT-AUDIT-001/narrow-gauge-contract.json`
- `reports/V9-GAIT-FOOT-AUDIT-001/commands.md`

No source, asset, media, schema, or engine file is to be changed.

## Ownership confirmation

The productized repository ownership map at
`/Volumes/m2-extended-disk/Repos/eonwild/config/ownership.yml` assigns
`reports/**` to `task_owner`, with each task restricted to its own report
directory. This task therefore owns only the directory named above. The
pre-existing untracked `reports/V9-EXTENSION-001/` directory and any other
worktree changes remain untouched.

## Acceptance checks

1. `git rev-parse HEAD` remains the pinned V8.3 commit.
2. The two GLB SHA-256 values in `audit.json` match the pinned files exactly.
3. `audit.json` and `narrow-gauge-contract.json` parse with the standard JSON
   parser; required measurements and classifications are present.
4. The report records the Blender version, media dimensions/timing, witness
   and dense-mask measurements, exact inherited toe-tip penetration, plane-edge
   evidence defect, and semantic-axis risk without presenting proposals as
   fossil facts.
5. Primary-source URLs resolve to PMC4108409, PMC2752196, and PMC5550975 and
   each claim is bounded to what that source supports.
6. `git diff --check -- reports/V9-GAIT-FOOT-AUDIT-001` passes, and no path
   outside this report directory is changed by this task.

## Method

- Import both GLBs directly in Blender 5.2.0 with the default action selected;
  evaluate corresponding integer frames over the common `[0, 97]` action
  range.
- Compare all vertices predominantly weighted to foot/toe chains in addition
  to the six sparse final-skinned witnesses. Separate toe-dominant masks from
  broad masks that include ankle/shin spill-through weights.
- Inspect fixed side, front, three-quarter, full-body, and foot-phase media;
  do not treat existing PASS text as independent visual proof.
- Calculate the fixed render-plane level from the render script and test the
  lowest toe vertices against that plane for both V8.2 and V8.3.
- Use measured root displacement for the local travel axis. Do not silently
  trust a semantic `forwardAxis` field that conflicts with the exported
  coordinate basis.

## Unresolved assumptions and boundaries

- Blender's imported world axes are used only to evaluate the exported GLBs;
  normalized contract definitions are expressed in an explicit local
  ground-plane frame (`up`, measured travel tangent, lateral).
- A toe contact centroid is computed from a deterministic sole/toe mask, not
  from an ankle or foot-bone origin. A COM target requires an explicit mass or
  proxy definition; no COM value is inferred from the cited trackways.
- Numeric gait-state bands in the contract are provisional engineering priors
  with stated uncertainty, not measurements of Tarbosaurus. The cited papers
  support narrow-gauge and speed-conditioned step-width trends but do not
  validate attack, brace, or turn ranges.
- A floor penetration inherited by both versions is reported as a real
  geometry/ground mismatch and as a non-regression result; it is not relabeled
  as a V8.3 fix.
