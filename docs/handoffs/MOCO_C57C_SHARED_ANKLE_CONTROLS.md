# C57 C — shared contact and ankle coordination

User request: reduce occasional overextension and transition sharpness without
per-animal or per-frame fixes. C57 B is changes-requested. C57 C is a diagnostic
visual candidate; user review is PENDING. Preserve all approved source takes.

## What changed

The connected finite optimizer omitted the sustained solver's unloaded ankle
acceleration and loaded ankle rate/acceleration costs. Both now use one shared
`ankle_support_residual`. Its existing weights, bounds and mechanics are retained.
An initial six-evaluation refinement with that correction barely changed the
visible ankle problem, so it is archived as unselected experiment A.

The connected pose seed used sequential frame-local IK with a timestep-independent
prediction cost. Applying acceleration penalties sequentially was unstable;
experiments B/C were rejected before rendering. Their outcomes remain recorded.
Final candidate D instead solves neighboring transition poses simultaneously
through `moco_contact_coordination.coordinate_contacts`. It minimizes the original
foot position/orientation/digit targets, existing pose preference, and acceleration
in physical time. The acceleration/contact cost ratio comes from the existing
finite-coordination recipe. It is a numerical objective, not biological data.

There are no species branches, new joint stops, edited source clips, frame-specific
angle offsets, or softened physical acceptance thresholds. The recipe selects
the existing 4.5–9.6 s transition window. The helper accepts arbitrary windows,
admitted bounds and foot targets. Transfer to another animal is NOT_RUN.

The final displayed result is a contact-constrained kinematic initializer replayed
through exact OpenSim mechanics. It is **not** a new full Moco solution, and does
not claim muscle-driven or dynamically feasible movement. The restored whole-body
cost remains available for subsequent refinement; the displayed D trajectory is
not the negligible-improvement output of experiment A.

## Measured comparison against C57 B

All values below are dense native-time final replay, not sparse optimizer samples.

| Measure | C57 B | C57 C D |
| --- | ---: | ---: |
| Entry left ankle peak speed, degrees/s | 561.8 | 452.9 |
| Entry right ankle peak speed, degrees/s | 451.2 | 405.9 |
| Braking left ankle peak speed, degrees/s | 513.3 | 459.9 |
| Braking right ankle peak speed, degrees/s | 637.8 | 528.6 |
| Braking right knee peak speed, degrees/s | 862.4 | 644.6 |
| Braking left ankle maximum angle, degrees | 105.48 | 101.99 |
| Braking right ankle maximum angle, degrees | 92.20 | 83.51 |
| Braking right knee closest to straight, degrees | -9.64 | -9.17 |
| Minimum emitted skin/floor distance, mm | -8.20 | -5.65 |
| Normalized root residual RMS | 0.43659 | 0.53260 |
| Peak normalized command | 17.5259 | 9.3549 |

Ankle RMS acceleration drops 14–26% across entry/braking. The right knee still
approaches its existing extension limit and is slightly straighter at its maximum;
do not claim the entire overextension complaint is solved. Force balance worsens
while peak command improves. Physical acceptance remains FAILING.
Maximum foot-target position error in the temporal fit is 16.62 mm; no anchor
target was moved to hide it. Reported loaded-surface slip and contact penetration
are retained in the replay audit and must not be described as a contact pass.

All sampled coordinate bounds and reopened emitted knee/ankle limits pass.
Running entry peak extra foot separation remains near the B baseline: 2.08 →
2.26 cm over approved C51. Knee separation improves 5.78 → 5.47 cm.
The bounded optimizer used six evaluations and stopped at its limit, not convergence.
Independent forward stability and arbitrary-state game transfer are NOT_RUN.

## Source, reproduction and delivery

Factory source commits: 42810ff0 (shared ankle residual) and
8b1b48cc256f59e7d3a44c0eb969da16dbde8e7c (temporal contact initializer).
Research directory:
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a087f8-b58c-7530-9fd8-e1ed39b8d526/research/moco-c57c-shared-ankle-controls`.

Use `tools/coordinate_moco_contacts.py` with C57 B `connected-b` as source,
C57 B `connected-a/foot-targets.npz`, the C51 A replay as baseline, and the saved
`finite-settings.json`. Only start/end, evaluation count, foot position weight
and acceleration weight are consumed by this initializer; other settings belong
to unselected A. Replay returned solution.sto, retarget using motion-set v15
tail12-connected and the C50 repaired source profile. Exact commands, source
hashes and input references are saved in the game evidence execution receipt.

Model SHA256 remains
2d233dc6eea15a87a24f7246afe6557d278330003ca9cc4054394d744d77cfa8.
Final GLB SHA256:
a6c22bcdb59d4d5e8fe00470bfb62c1bcc205ce1fe99369da6a5aecb9354e073.
31 focused tests pass. Unity plain-stage build succeeds. This is stage rendering,
not independent Unity mechanics parity or gameplay acceptance.

Both review videos contain the same 27.8125-second source sequence at native time,
668 frames per view at 24 fps (27.833 s encoded). All-frame inspection and its
observations are recorded separately in visual-review.json before delivery.
Evidence: principal repository `game/Evidence/moco-c57c-shared-ankle-controls`.
Branches remain `codex/moco-c52-walk-turn` and `codex/moco-c52-walk-turn-review`;
accepted main is unchanged. Pause here for user feedback.
