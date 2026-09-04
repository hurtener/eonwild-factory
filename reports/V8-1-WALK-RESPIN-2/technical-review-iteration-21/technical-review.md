# Iteration 21 / iteration 3 independent technical review

**Scope:** final candidate-only review of iteration 21 GLB and iteration 3
approval MP4. This review does not approve release or replace user visual
approval. No candidate, accepted-package, or media file was modified.

## Verdict

- **P0: 0**
- **P1: 0**
- **P2:** two existing GLB portability warnings; see below. The base validator
  also retains obsolete broad-sole/proxy fields that report `FAIL`; the final
  decision must use the explicitly stricter distal-skinned-witness result, not
  mistake that legacy report's top-level status for a new failure.

## Identity and delivery

| item | observed SHA-256 | result |
| --- | --- | --- |
| `generated/iteration-21/tarbosaurus_procedural_v8_1_walk_respin.glb` | `c53e8f67df930a1a455bb7c35c041dd736753c90242321fc623489590781b329` | exact match |
| `showcase/v8.1-walk-respin-2/iteration-3/walk-relaxed-v8-1-respin-side.mp4` | `2ba831dddd482ae8f512f229a71257c76e1a730c969cccf1ac8bc6a9f5b5d0ac` | exact match |

The delivery directory has only `render-run.json` and that MP4. `ffprobe`
reports H.264/yuv420p, 960x540, 24 fps, 240 frames, and exactly 10.000 s.

Iteration 16 and its media are explicitly quarantined by
`generated/iteration-16/QUARANTINED.md` and
`showcase/v8.1-walk-respin-2/iteration-2/QUARANTINED.md`; neither is an
approval input.

## Exported skinned-geometry review

The final respin validator evaluates the *final GLB*, not root-subtracted
proxy positions. It deterministically selects three distal, toe-weighted mesh
witness vertices per side and skins them at 240 Hz through every loaded
contact group. The all-group worst cases are:

| check | measured worst | enforced limit | result |
| --- | ---:| ---:| --- |
| world X drift | 0.000496 m | 0.013750 m | pass |
| world Z drift | 0.007374 m | 0.008250 m | pass |
| world Y drift | 0.004279 m | 0.008250 m | pass |
| adjacent witness movement | 0.001636 m | 0.025000 m | pass |
| metatarsal net rise | 0.013661–0.022158 m | >=0.004 m | pass |
| metatarsal reversals >1 mm | 0 | 0 | pass |
| passive terminal toe-down keys | 8 per complete group | >=5 | pass |
| least toe-down terminal pitch | -9.301 deg | <=-4 deg | pass |

This also covers the startup stance: at t=0 the right leg is already in its
loaded contact group (phase .5). Its dense world-witness span through release
has no pop (worst adjacent movement 1.604 mm); release is followed by eight
toe-down exported keys before receiving preparation. The direct in-place loop
seam check gives zero horizontal witness drift and effectively zero toe-root
orientation difference; initial adjacent in-place witness movement is
21.22 mm left / 21.05 mm right, below the 25 mm two-pixel cap. Thus the
iteration-16 first-20-frame reset mechanism is not present in the final
channels; expected post-release/passive motion is distinct from planted-contact
motion.

## Gait and physical checks

Both sides and both baked cycles have rocker onset about `.45082`, measured
rear-extension peak about `.71311`, and release about `.73770`: the required
order is rocker before peak before release, with peak-to-release lead
`.02459` cycle. There are 18 loaded samples, `.09836` cycle distal dwell,
eight passive keys, and receiving-arm onset `.80328`.

The configured `.04–.10` rocker-to-peak lead is expressly a *desired* range,
not a locked failure criterion after the iteration-17 correction plan; the
locked criterion is onset lead > `.02` and peak before release by >=`.02`.
The actual `.26230` lead therefore passes the governing contract but should
remain visible to visual approval rather than be misrepresented as being in
that desired range.

Final measurements are 2.59999997 m reference same-foot stride, 4.59999986
km/h reference root speed, and 2.75636 m candidate world hip height. The GLB
has one `RESPIN_REFERENCE_SCALE_ROOT` wrapper (2.0086956434) for the 12 m
reference length; it must not be scaled again. Both named clips are present,
looped, and 4.069565 s/245 keys: root-motion and in-place.

The base all-key report has true results for both clips measured, speed/stride,
no selected-sole penetration, support, and joint continuity. Its old absolute
front-reach and broad `progressive_toe_contact_before_release` checks remain
false. They were not waived: `respin-2-validation.json` replaces those
proxies with (1) stride-scaled front extrema and (2) the stricter 240 Hz,
world-space, individually skinned distal-witness gate above. Its status is
`PASS` and all six final checks are true.

## Accepted V8.1 boundary

Iteration-21 generation recorded identical before/after accepted-tree hashes
(`d7f242...329d10` toolkit and `336b22...bcf753` showcase), source GLB SHA
`fbb42c2...90a65c7`, canonical-profile SHA `f128bd...240143`, and
`immutableUnchanged: true`. Independent package-manifest verification also
reports 285/285 accepted V8.1 files matching with zero mismatches. Raw source
tree digests are cache-environment volatile and are not treated as evidence of
a non-cache accepted-file change.

## P2 follow-up

`gltf-transform validate` reports no errors, but two existing warnings remain:
`MESH_PRIMITIVE_GENERATED_TANGENT_SPACE` on mesh primitive 0 and
`NODE_SKINNED_MESH_NON_ROOT` at `/nodes/75`. They are portability debt, not a
mechanical-contact failure for this candidate.

## Evidence paths

- `candidates/v8.1-walk-respin-2/generated/iteration-21/respin-2-validation.json`
- `candidates/v8.1-walk-respin-2/generated/iteration-21/base-validation.json`
- `candidates/v8.1-walk-respin-2/generated/iteration-21/generation-report.json`
- `candidates/v8.1-walk-respin-2/scripts/validate_walk_respin_2.py`
- `reports/V8-1-WALK-RESPIN-2/user-rejection-iteration-16/diagnostic-addendum.md`
