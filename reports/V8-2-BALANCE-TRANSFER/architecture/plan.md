# V8.2 balance-transfer architecture plan

## Task

Define a minimal, isolated V8.2 walk overlay that preserves the user-approved
V8.1 walk-respin-2 iteration-38 locomotion and transfers only the useful
whole-body balance behavior observed in V5.5. This is a read-only architecture
pass; no engine, profile, GLB, validator, media, or showcase asset is changed.

## Immutable inputs

- V8.1 iteration-38 GLB:
  `candidates/v8.1-walk-respin-2/generated/iteration-38/tarbosaurus_procedural_v8_1_walk_respin.glb`
  (`sha256 1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`)
- V8.1 profile:
  `candidates/v8.1-walk-respin-2/generated/iteration-38/resolved-profile-v8.1-walk-respin.json`
- V8.1 final mechanical and visual reviews:
  `reports/V8-1-WALK-RESPIN-2/technical-review-iteration-38/technical-review.md`
  and `reports/V8-1-WALK-RESPIN-2/visual-review-iteration-38/visual-review.md`
- V5.5 GLB:
  `procedural-animation-toolkit(v5.5)/validated_result/v5.5/tarbosaurus_procedural_v5_5_animation_pack.glb`
- V5.5 balance profile:
  `procedural-animation-toolkit(v5.5)/toolkit/v5.5/examples/profiles/tarbosaurus-v5.5.json`

## Files written

- `reports/V8-2-BALANCE-TRANSFER/architecture/plan.md`
- `reports/V8-2-BALANCE-TRANSFER/architecture/architecture.md`

No other path is in scope. The factory checkout has no local
`config/ownership.yml`; the requested report directory is treated as the
bounded ownership surface for this analysis.

## Analysis sequence

1. Inspect the actual animation channels in both final GLBs, rather than infer
   ownership from profiles alone.
2. Map semantic chains and the order in which pelvis, upper body, tail, and leg
   IK are authored.
3. Define an exact-freeze V8.2 candidate whose only write allowlist is selected
   upper-body and tail rotations in the two approved walk clips.
4. Define a separate pelvis experiment, with explicit re-solve and
   world-contact-equivalence requirements, because pelvis motion cannot coexist
   with byte-identical leg/contact channels.
5. Specify automated invariants, visual evidence, and stop conditions.

## Acceptance checks for this architecture report

- Pin the exact iteration-38 source identity and both walk clip names.
- Enumerate root, pelvis, bilateral leg/foot/toe, spine, neck/head, and tail
  bones and their animation paths.
- Separate exact-channel preservation from world-contact equivalence.
- State the safe transform order and why a post-bake pelvis change is invalid.
- Provide quantitative lower-body, loop, stride, motion-bound, and visual
  acceptance gates.
- Leave all implementation and accepted assets unchanged.

## Assumptions

- “Freeze approved V8.1 legs/feet” means exact float32 channel preservation for
  the first V8.2 candidate, not merely a visually similar result.
- V5.5 is a behavior reference, not a source animation to copy wholesale;
  cadence, stride, stance timing, and foot mechanics differ materially.
- V8.2 initially concerns only the two relaxed-walk clips. All other clips stay
  byte-identical.
- Pelvis balance is desirable but optional in the first candidate because it is
  upstream of both leg chains.

