# C57 B — running-entry width correction

The user flagged wider legs than the approved C51 run in C57. Phase-matched
trunk-local replay confirms peak extra foot separation of 13.41 cm and extra
knee separation of 10.56 cm in the first running second. Settled running differs
by only 3.6 mm mean foot width. C57 is changes-requested, not approved.

## Cause and shared correction

The inherited C2 orientation correction carried outgoing angular derivatives
for a full second. This produced a torso-yaw excursion around 8.8 degrees where
the approved running reference had about 2.3 degrees. Feet held in their world
support lanes consequently spread relative to the twisted torso, and leg IK
compensated at the hips and knees. The width artifact exists in the seed before
finite optimization; it was not a changed approved running clip.

The shared handoff now chooses the longest angular reconciliation duration
that fits an envelope drawn from the outgoing orientation and incoming reference.
A 5% envelope margin is a numerical continuity allowance, explicitly authored,
not a biological ROM or strength claim. Position, velocity and acceleration
are still inherited exactly at the analytic start; the correction ends C2.
Translation retains its existing state carry. Supporting foot anchors are not
pulled inward. Later IK and finite optimization still require final auditing.

For entry, the seed selects ~0.452 s for yaw/roll and ~0.672 s for pitch,
rather than one second for every region. All other body and limb articulation
retains its previous reconciliation. Each duration and any unresolved envelope
excess are reported. The policy is shared across handoffs, with no animal/gait
name branch. Physical limits, model, contacts, capacities and acceptance remain
unchanged. The C57 tail search radius is retained to avoid its rejected dip.

## Scope and reproduction

Factory source: 5305103. Research directory:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c57b-running-handoff`.
Existing review branches remain codex/moco-c52-walk-turn and
codex/moco-c52-walk-turn-review. No main merge.

The same 27.8125-second sequence is used: start/walk, run, brake, retreat,
forward restart, stop. This is an offline warm-reference integration experiment,
not new predictive gaits, production admission or an arbitrary-state gameplay
controller. Preserve C51, C52 B H, C56 and the prior C57 recordings.

Recipe `sequence-plan.json` generates connected-a; `finite-settings.json`
refines it to connected-b using the saved C57 I coefficient initializer.
Three bounded evaluations are permitted; reaching the limit is not convergence.
Final replay, reopened skin checks and side/quarter media must be saved together.
Pause for user review. No automatic approval.

## Final B result

Phase-matched trunk-local separation, first running second (4.75–5.75 s):

| Peak extra separation over C51 | C57 I | C57 B |
| --- | ---: | ---: |
| Feet (toe origins) | 13.41 cm | 2.08 cm |
| Knees (shin origins) | 10.56 cm | 5.78 cm |
| Ankles (metatarsal origins) | 9.95 cm | 0.99 cm |

The knee maximum now occurs at the inherited walking boundary (4.75 s).
Settled running retains approximately 3.6 mm mean extra foot separation and
1.60 cm peak extra separation, essentially identical to C57 I. These are
same-model replay comparisons, not pixel measurements or new acceptance limits.

All sampled coordinate bounds and reopened emitted knee/ankle limits pass.
Minimum skin-floor distance is -8.20 mm (previous -8.20 mm).
Ankle peak rates are 562/638 degrees/s (previous 594/625), so this correction
does not claim to solve all transition sharpness.

Full-clip normalized root residual RMS improves 0.45206 → 0.43659.
Peak normalized command worsens 16.5581 → 17.5259. Physical acceptance is still
FAILING; there is no full Moco convergence, independent forward stability, or
arbitrary-state runtime transfer. The refinement stopped at its three-evaluation
limit; it did not converge. Do not reinterpret visual review as physical approval.

Final GLB SHA256:
d78d38c64e340fc476d4c109978d60dbc85e6c71eeab01c20e99b7cdcb640b84.
Unchanged model SHA256:
2d233dc6eea15a87a24f7246afe6557d278330003ca9cc4054394d744d77cfa8.

Twenty-six focused handoff, finite-coordination, retreat, pad/contact, path
and turn-plan tests pass. Unity standalone stage build succeeded.
Final review media and every-frame inspection receipt are archived under
game/Evidence/moco-c57b-running-handoff in the principal Eonwild repository.
User review remains PENDING; stop at this bounded checkpoint.

## Visual checkpoint

Side and quarter plain-stage captures each contain 668 frames at 24 fps,
27.833 s encoded duration, with 27.8125 s source motion (no time scaling).
All frames were inspected chronologically through contact sheets; side frame
120 and quarter frames 124/132 were also enlarged. This is framewise inspection,
not a claim of direct video perception. No new pose snap or tail collapse was
observed; fast ankle articulation around transitions remains a review caveat.

Saved videos, relative to the principal repository:
- game/Evidence/moco-c57b-running-handoff/review-side/tarbo-c57b-b-side.mp4
- game/Evidence/moco-c57b-running-handoff/review-quarter/tarbo-c57b-b-quarter.mp4

The most relevant running-entry interval is approximately 4.75–5.75 seconds.
See execution.json for exact commands and input/reference locations, and
connected-b-width.json for same-phase comparisons. PENDING user review.
