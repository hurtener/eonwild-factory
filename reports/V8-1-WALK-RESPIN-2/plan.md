# V8.1 relaxed-walk respin 2 candidate

## Intent and scope

Create a second isolated, walk-only candidate from the accepted iteration-15 V8.1 respin logic. It is not a replacement for iteration 15 and must not alter `procedural-animation-toolkit(v8.1)`, `showcase/v8.1`, `candidates/v8.1-walk-respin/`, or any existing media.

User-directed target: shorten same-foot stride to 2.60 m while holding the 12 m reference-scale relaxed speed near 4.60 km/h with cadence near 0.4915 Hz. The revised late stance must begin the toe/metatarsal rocker before peak rear-leg extension, relieve extension as the metatarsal rises, retain a toe-loaded rocker for 15–20 smoothly changing exported 60 Hz samples on each side, then transition to a brief passive unloaded foot/digit lag before later precontact arming.

The final numerical lock is intentionally deferred pending `/root/v8_1_walk_reference` addendum. No candidate GLB or MP4 will be generated before that lock.

## Immutable boundaries and ownership

- Read-only: `procedural-animation-toolkit(v8.1)/`, including `validated_result/`, canonical profile, package manifests, and `showcase/v8.1/`.
- Read-only prior candidate: `candidates/v8.1-walk-respin/` and `showcase/v8.1-walk-respin/`.
- Candidate-owned: `candidates/v8.1-walk-respin-2/**`, `showcase/v8.1-walk-respin-2/**`, and `reports/V8-1-WALK-RESPIN-2/**`.

The factory has no local `config/ownership.yml` or workstream assignment for this isolated candidate; all additions are confined to the candidate-owned paths above.

## Planned implementation

1. Start from the accepted iteration-15 profile/solver conventions and use the canonical V8.1 source GLB read-only.
2. Apply only a candidate-owned profile/solver overlay for the shorter stride/cadence and phase-continuous late-stance rocker.
3. Solve actual skinned weighted distal-toe vertices at each baked key. The toe-root correction must be bounded, continuous, bilateral, and released to a damped passive lag—not held rigid—before precontact arm.
4. Keep the explicit `RESPIN_REFERENCE_SCALE_ROOT` wrapper at 12 m physical scale; no second scaling or vertex/bone bake.
5. Generate only the root-motion/in-place relaxed-walk pair needed for validation and, after all gates pass, exactly one 10.000 s side-view 24 fps MP4.

## Acceptance checks

1. Fail-closed proof that accepted V8.1 and iteration-15 candidate/source/profile hashes remain unchanged.
2. Baked stride and root speed measure 2.60 m and 4.5–4.8 km/h at the explicit 12 m scale; cadence is measured, not asserted.
   The front-reach lower bounds are derived from respin-1 rather than copied from its 2.75 m stride: `2.60 / 2.75 = 0.94545`, so the provisional targets are 1.139 m left and 1.204 m right (94.5% of respin-1's measured 1.205 m/1.274 m extrema), subject to the rocker’s measured rear-extension relief.
3. At every exported 60 Hz key, for each side: `rocker onset phase < rear-leg maximum-extension phase`; rear extension decreases as metatarsal height rises; 15–20 consecutive toe-loaded rocker samples occur; then toe release, passive damped lag, and later precontact arming occur in order.
4. Rocker/toe channels are phase-continuous, loop-seam continuous, bounded in angle/velocity/acceleration, and free of discrete keys/pops.
5. Every baked key of both clips passes selected-sole and toe-patch no-penetration, hover/support, and joint-continuity gates.
6. The final MP4 is exactly 10.000 s, 24 fps, 960x540, side view, and is the only delivery media in its final iteration directory.

## Assumptions and blockers

- Reference scale remains 12 m nose-to-tail and 2.75 m hip height.
- The requested cadence estimate is approximately `1.27875 / 2.60 = 0.49183 Hz`; final cadence, phase intervals, lag damping, and precontact timing await the reference addendum.
- “Passive lag” means dynamically eased toe/foot follow-through after unloading, not a rigid hold, and it must be measurable from the exported channels.
## Completion update

Iteration 15 was superseded by P1 corrective iteration 16. Iteration 16
preserves accepted V8.1 and emits only the requested walk-only review MP4. See
`summary.md` for the all-key proof and `command-log.md` for reproducible
commands/tool versions.

## P1 corrective iteration

Iteration 15 and its MP4 are quarantined. The replacement must remove all
active foot translations from phase `.74-.80`, integrate actual toe-root and
ankle rotations forward from release position/velocity with only spring and
damping mechanics, then derive passive and receiving-arm evidence from those
exported channels before emitting a new walk-only MP4.

## Iteration 17 rejection and correction

Iteration 16 and its MP4 are quarantined after visual review found vertical
and longitudinal front-toe contact motion during startup/early toe-off. The
new detailed plan is `iteration-17-plan.md`; no final contact thresholds are
assumed pending the visual diagnostic handoff.

## Iteration 37 causal-release correction

Iteration 36 proved the late visible metatarsal onset, coupled final-skinned
toe lock, all-key ground support, terminal toe-down, and passive energy
behaviour. Its preserved shin/pelvis landmark peaks at `~.754`, while the old
fixed release is `~.762`; that does not satisfy the required peak-before-
release separation. Retain the iteration-36 coupled solve and contact
thresholds, extend loaded contact to `.78`, and run the existing homogeneous
passive spring from `.78` to `.85`. Receiving preparation is explicitly later
than `.85` and is measured from exported channels.

Only the candidate generator, candidate validator, candidate phase overlay,
and this report are owned by this correction. No accepted V8.1 path, prior
media, root/pelvis/leg/stride channel, or unrelated animation may change.
Fail-closed acceptance keeps all existing contact, ground, continuity,
physical-scale, and immutable-hash checks; final skinned onset must lead the
preserved shin/pelvis peak by `.04-.10`, peak must lead release by `>=.02`,
and loaded samples are counted from the final skinned onset rather than the
diagnostic ankle channel. Render only after the full authoritative pass.

Iteration 37 showed that extending the contact interval must not reuse the
later procedural metatarsal endpoint: it increased the final-skinned witness
drift despite preserving ground clearance. Iteration 38 therefore preserves
the proven `.76` visible-rise endpoint, holds the coupled toe-lock solution
through `.78`, and defines release from the first exported homogeneous
passive key (not the intentionally rising broad toe-patch quantile).

## Completion

Iteration 38 passed every authoritative candidate gate and produced the sole
new review MP4 in `showcase/v8.1-walk-respin-2/iteration-4/`. The remaining
decision is user visual approval; no accepted V8.1 file, other animation, or
prior candidate media was changed.
