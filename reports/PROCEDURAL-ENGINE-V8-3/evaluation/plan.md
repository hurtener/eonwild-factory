# V8.3 hip-balance evaluation plan

## Objective

Define a fail-closed V8.3 working-candidate gate: increase pelvis
lateral/vertical/roll balance toward V5.5 while preserving V8.2 root/timeline,
2.60 m stride, 4.6 km/h speed, final-skinned foot/toe contact,
rocker/passive/receiving timing, declared V5.5-inspired upper-body
counterbalance envelopes, head stability, and loop seam.

## Evidence inputs

- V8.2 stable rollback SHA-256:
  a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5.
- V8.2 official 120-phase metrics and final-skinned contact evidence in the
  legacy V8.2 evidence directory.
- Accepted V5.5 metrics/reference analysis as a directional target only; no
  V5.5 curve, local rotation, timing, or binary is a V8.3 input.
- The recorded V8.3 contract-conflict search. It proves that a world-space
  pelvis-roll increase has no valid intersection with frozen chest/tail local
  tracks and component-wise world-relative limits. It is the basis for this
  narrow, declared third-layer amendment.

## Scope

Only this plan, contract.md, thresholds.json, and the short amendment rationale
are changed. No engine, profile/channel state, candidate, media, V8.2 release,
or V5.5 artifact is edited.

## Required handoff

The candidate must declare semantic-role-only layers in this exact order:

    pelvis_balance_pre_ik@1
      -> leg_contact_resolve@1
      -> chest_tail_head_stabilization@1

Run every declared amplitude scale, retain all evidence, and select the
strongest all-hard-gate PASS. Mechanical PASS precedes synchronized locked-bounds
side/front/three-quarter playback and independent technical/visual/user review.

The final layer must declare one additive, zero-mean counterbalance manifest
for semantic upper-spine, chest, tail, neck, and head roles. It cannot write
translations, pelvis/root, or any leg/foot/toe role. Its trunk/tail curves use
the same sweep scale as the pelvis; neck/head remain residual world-head
stabilizers. The amended envelope is deliberately smaller than V5.5 and is not
a license to transplant, retime, or freely animate V5.5 tracks.
