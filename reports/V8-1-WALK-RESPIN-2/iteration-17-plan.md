# V8.1 Walk Respin 2 — iteration 17 toe-contact correction plan

## Scope

Replace only the rejected iteration-16 walk candidate in an isolated new
iteration. Preserve the accepted V8.1 package, source profile, physical scale,
and all non-walk animations. The motion correction is a candidate-local
world-space distal-toe contact lock through startup and loaded rocker: toe tips
remain slightly weighted and fixed in world X/Z and height while the
metatarsal/heel rises, digits rotate progressively downward, then release into
brief passive free-weight motion before later receiving preparation.

Iteration 21 is rejected for an early-initiated rocker: its baked ankle onset
`.45082` precedes the measured rear-extension peak `.71311` by `.26230`
cycle. Iteration 23 is a narrow timing correction only. It preserves the
iteration-21 skinned toe-contact solve, physical scale, stride, cadence, and
all passing ground/passive/seam gates while moving actual ankle/metatarsal
rocker onset to `.04–.10` cycle before the measured rear-extension peak. It
uses a candidate-local skinned-metatarsal-height solve to defer inherited
visible rise while retaining the same world-locked distal toe witnesses;
geometry is authoritative and the ankle channel is a 1-degree cross-check.
The parent has additionally authorized a deterministic loaded-contact pivot
compensation: it is derived only from the coupled final-skinned toe/contact
solve, preserves root/pelvis/leg channels, and releases only through passive
spring decay after toe release. It is not a free authored translation curve.

## Ownership and intended files

Allowed task-owned paths (confirmed by the task boundary; factory paths are
not part of the main-repository ownership map):

- `candidates/v8.1-walk-respin-2/scripts/generate_walk_respin_2.py`
- `candidates/v8.1-walk-respin-2/scripts/validate_walk_respin_2.py`
- `candidates/v8.1-walk-respin-2/profile-overlay.json`
- `candidates/v8.1-walk-respin-2/generated/iteration-23/**`
- `showcase/v8.1-walk-respin-2/iteration-4/**`
- `reports/V8-1-WALK-RESPIN-2/**`

Read-only boundaries: `procedural-animation-toolkit(v8.1)/**`,
`showcase/v8.1/**`, prior iterations, and all accepted V8.1 media.

## Acceptance checks

1. Preserve physical reference stride `2.60 m` and root speed `4.60 km/h`,
   unless a recorded contact-lock timing change proves necessary.
2. At every dense baked frame through startup and loaded rocker, measure each
   selected distal contact point's world horizontal X/Z drift and Y error;
   fail on a sliding/popping contact patch.
3. Confirm metatarsal rise is monotonic while loaded toe-patch world position
   remains fixed; confirm increasing downward toe pose before release.
4. Confirm release follows rocker/dwell, then a brief passive free-weight
   phase with no active world-contact target, followed by measurable receiving
   preparation in exported channels.
5. Retain bilateral rocker-before-extension ordering, 15–20 loaded samples,
   toe dwell, all-key penetration/support/continuity/loop-seam gates, and
   accepted-package/source/profile hashes.
6. Produce exactly one new 10 s, 960×540, 24 fps side-view walking MP4 only
   after every gate passes; retain iterations 15, 16, and 21 as quarantined.

## Assumptions and open items

- The toe-tip patch is a game-tuning contact hypothesis, not a scientific
  claim; it is limited to the user-specified visual/kinematic correction.
- Locked dense-contact thresholds: witness X drift ≤`0.005H` and ≤2 px total,
  Z drift ≤`0.003H`, Y error ≤`0.003H`, no adjacent-frame jump >2 px, and no
  metatarsal-rise reversal >1 mm. Require 15–20 consecutive 60 Hz loaded
  rocker samples, at least five passive toe-down frames after release, and
  seam toe drift ≤1 px/orientation ≤1°. Startup begins in a stable weighted
  stance; rocker itself still begins before rear-extension peak.
- Existing 2.60 m / 4.60 km/h values remain locked unless dense contact proof
  demonstrates a small timing adjustment is necessary.
- Parent confirmation supersedes the obsolete absolute rear-extension-peak
  interval `.54–.58`: each side must measure ankle-rocker onset `.04–.10`
  cycle before the measured rear-extension peak, and that peak must remain at
  least `.02` cycle before toe release. This is not met by restoring any
  sliding foot translation.
- The iteration-16 diagnostic addendum is incorporated as P1 acceptance
  evidence: there may be no unlocked key between planted toe hold and passive
  lag, no terminal-toe transform reset, and the exported terminal pose must
  remain toe-down (at most `-4°`) for at least five consecutive passive keys
  before receiving preparation.  The validator records the actual skinned
  world witnesses, not root-subtracted positions.
- The timing correction uses `stance_fraction=.72` and
  `toe_off_window_fraction=.106`, preserving the `.614` procedural start
  while returning rear-extension timing and front reach to the accepted
  candidate-local setting. A bounded delta solve may offset inherited
  asymmetric stance IK only until the actual skinned metatarsal height reaches
  its smooth late-rocker target; exported joint constraints remain hard gates.
