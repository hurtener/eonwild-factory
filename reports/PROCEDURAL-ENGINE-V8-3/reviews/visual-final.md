# V8.3 independent visual review — exact commit `c2701d0`

## Verdict

**P0 = 0, P1 = 2, P2 = 0 — NOT YET SUITABLE AS A USER-APPROVAL CANDIDATE.**

This is a visual-evidence verdict only. It does not dispute the working-only
machine result, approve a release, or authorize promotion.

## Evidence reviewed

- Exact `c2701d09420630de8634c1a55c6c1c503a7b8f5f` at `HEAD`.
- The synchronized V8.2-left/V8.3-right side, front, and fixed
  front-three-quarter H.264 comparisons: each is 960 x 540, 24 fps, 240
  frames, and 10.000 seconds.
- Every required phase pair: nine full-body crops and nine foot crops
  (contact, load acceptance, midstance, rocker onset, rear-extension peak,
  release, passive lag, receiving, and swing pass).
- The review page source and the revised V8.3 evaluator contract. The machine
  evidence was cross-checked for scope and media identity, but did not replace
  the perceptual findings below.

## What reads well

- **Framing and comparability:** all three comparison views keep both complete
  bodies in frame with a stable, matched camera. Front is the useful view for
  the support-side shift; side remains useful for stride, tail line, and toe
  order; three-quarter confirms that the change is not an obvious camera-only
  artifact.
- **Body response:** V8.3 reads as a restrained load-side pelvis settle with
  chest and tail participation, not a head-led lean or a high-frequency torso
  wobble. The tail follows as a smooth whole-body response rather than a whip.
  The head line remains visually quiet.
- **Lower body:** the paired phase crops preserve the approved leg timing and
  look cohesive through loading, rear extension, rocker, passive lag,
  receiving, and swing. I found no new visible knee split, foot pop, or
  apparent change in toe order between the left and right panes. This supports
  the intended narrow overlay; it is not a replacement for the contact gate.
- **Page truthfulness:** the page clearly labels V8.3 as working, states that
  visual approval is pending, names V8.2 as the approved baseline, and states
  the remaining independent review/user-approval boundary. It does not claim
  promotion.

## P1 — browser playback has a visible media-loop pop

Every comparison is marked `loop` in the review page, but each MP4 is exactly
10.000 seconds while the guarded native walk loop is 4.069565296 seconds.
That is not an integral number of walk cycles. Direct first-versus-last-frame
inspection shows materially different gait poses in **side, front, and
three-quarter**: stance/leg and tail positions at encoded frame 239 do not
match frame 0. The page therefore jumps when its media loops, even if the GLB
seam itself is separately valid.

This is material because the page uses those looping videos as the primary
native-speed review surface. Re-render the exact locked candidate/baseline
comparison to an integer number of native cycles (or make the page playback
non-looping) and independently re-check the media seam. Do not treat the
underlying GLB seam metric as proof that the browser MP4 seam is acceptable.

## P1 — contact quality is not visually judgeable from the supplied media

The full-body and foot crops use a uniform dark field without a readable floor
edge, contact shadow, or other stationary ground reference. The feet can be
compared pane-to-pane, but slide, hover, penetration, and toe-ground transfer
cannot be judged visually against the environment. The final-skinned witness
numbers are valuable machine evidence, but they cannot make an absent visual
floor reference perceptible.

Re-render the same exact artifacts and locked cameras with a neutral,
non-reflective ground plane plus readable contact shadow/floor line. Preserve
the current framing, labels, synchronized clock, and crop phases. This is an
evidence-media correction; it does not request an engine, rig, or motion
change.

## Approval boundary

Once both P1 evidence defects are corrected, repeat the narrow three-view
visual review. If the re-render still shows the present restrained pelvis →
chest/tail response, quiet head, and unchanged-looking lower-body phases, it
would be appropriate to present as a **user-approval candidate only**. Stable
promotion still requires the separately required technical review and explicit
user approval.
