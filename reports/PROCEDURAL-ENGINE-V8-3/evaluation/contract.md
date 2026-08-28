# V8.3 hip-balance acceptance contract

## Authority

V8.3 is a working candidate only; stable remains V8.2. The evaluator uses
X=lateral, Y=vertical, Z=sagittal, translation P2P normalized by median sampled
hip height, 120 common phases, and final exported float32 GLB/final-skinned
witnesses as authority.

| Metric | V8.2 | V5.5 reference | V8.3 hard envelope |
| --- | ---: | ---: | ---: |
| Pelvis lateral P2P | .014857H | .101657H | .030-.040H |
| Pelvis vertical P2P | .012369H | .038808H | .016-.020H |
| Pelvis roll P2P | 2.696 deg | 7.362 deg | 3.5-4.1 deg |

Sagittal P2P stays within .0002H and pitch/yaw P2P within .15 deg of V8.2.
The V8.2 pelvis change necessarily rotates descendant world-relative
components. Therefore the third layer is a declared, bounded counterbalance
layer rather than a false claim that all chest/tail local arrays remain exact.
This amendment permits no changes outside the semantic upper-body roles below.

## Required layer order and ownership

    pelvis_balance_pre_ik@1
      -> leg_contact_resolve@1
      -> chest_tail_head_stabilization@1

The pelvis layer reads declared phase/load/support/root state and writes only
zero-mean pelvis lateral, vertical-load, and roll targets. It cannot write
root, sagittal, pitch, yaw, timing, or foot targets.

The contact layer consumes those targets and the frozen schedule, solves
bilateral semantic leg/foot/toe roles to original world targets, then reapplies
rocker/passive/receiving. It may claim only world-contact equivalence, never
unchanged local legs.

The final layer owns additive **rotation-only** deltas for declared semantic
`spine.*`, `chest`, `tail.*`, `neck.*`, and `head` roles. It must publish a
per-role delta manifest against the V8.2 track, including the shared sweep
scale, phase offsets, P2P envelope, means, and continuity measurements.
Trunk/chest/tail deltas are the balance response and share the pelvis sweep
scale. Neck/head deltas may only be the bounded residual required to keep the
world head quiet; they are not an independent gesture channel.

The final layer cannot write translations, root, pelvis, either leg, foot, or
toe role; it cannot alter key times, interpolation, the contact schedule, or
non-walk clips. Every semantic role outside the combined declared layer-write
sets retains its V8.2 walk local arrays exactly, and this layer cannot modify
contact-owned arrays. All ownership uses semantic roles; concrete GLB names
remain in the rig map. Unknown roles, implicit order, duplicate writers,
undeclared writes, absent delta manifests, or absent final-skinned witnesses
are hard FAIL.

## Hard machine gates

Thresholds.json is normative. The evaluator must reject absent/non-finite
metrics and prove source/profile/channel/tool identity, two byte-identical
independent builds, exact root/timeline/structure, controlled pelvis
progression, final-skinned contact/trajectory, rocker/passive/receiving timing,
upper-body counterbalance, head stability, and export seam.

The original foot targets, stance/release schedule, terrain, root path, stride,
and speed remain frozen. Final witnesses rather than local tracks decide
contact. Chest/tail are governed by bounded total-motion, delta, phase,
zero-mean, continuity, and head-quiet bands; this makes the desired body/tail/
neck response measurable without allowing arbitrary upper-body animation.

## Strongest-passing rule

Evaluate every declared scale, filter to all-hard-gate PASS, then choose the
largest scale. Equal scales choose lower worst-axis trajectory regression, then
lower maximum head-world delta, then lower pelvis-step discontinuity, then
lexical ID. No weighted score can offset a contact, trajectory, head, seam, or
preservation failure. If none pass, V8.2 stays stable.

## Visual approval boundary

Render only after machine PASS. Produce synchronized 10-second/24-fps/240-frame
V8.2-left/V8.3-right side, front, and fixed three-quarter playback with one
global full-body bounds/floor/light/camera configuration. Provide full-body and
foot crops at contact, load acceptance, midstance, rocker onset, rear-extension
peak, release, passive lag, receiving, and swing pass.

Native-speed review must show load-side hip settling rather than decorative
wobble, cohesive legs, quiet head, tail counterbalance, and readable approved
toe/rocker behavior. Static images, hashes, mechanical PASS, or one reviewer
do not grant approval. Promotion additionally needs independent technical
review, independent three-view visual review, and explicit user approval.
