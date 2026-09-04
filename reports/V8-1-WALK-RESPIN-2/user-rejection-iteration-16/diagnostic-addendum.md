# Iteration-16 user-rejection frame diagnostic

**Verdict: P1 FAIL — not an approval candidate.** The causal validator's PASS is insufficient: it verifies vertical/contact ordering but does not enforce that the loaded distal toe patch stays fixed in the world. The rejected motion has a direct world-space planted-toe slip followed by a one-sample reset/pop. No P0 catastrophic body break was found. P2 readability limitations remain in the dark-floor side render.

## Scope and evidence

- Candidate MP4: `/Volumes/m2-extended-disk/Repos/eonwild-factory/showcase/v8.1-walk-respin-2/iteration-2/walk-relaxed-v8-1-respin-side.mp4`
  - SHA-256: `c973ebfa6d2411a1c660627608cae42f7c2761ef16b0ce950cc6af6604757ed6`
  - 960x540, 24 fps, 240 frames, 10.000 s.
- Candidate GLB: `/Volumes/m2-extended-disk/Repos/eonwild-factory/candidates/v8.1-walk-respin-2/generated/iteration-16/tarbosaurus_procedural_v8_1_walk_respin.glb`
  - SHA-256: `8d878d7a6cbecfc1cfd5193b3889b640e82f445df4583d38c1c146d371f63d2c`.
- Five supplied captures were inspected directly. Approximate normalized body-crop nearest frames are `[109, 211, 2, 13, 16]` in capture order; these are not timestamps. The captures visibly show the same full-body side presentation, but the dark floor and overlapping feet prevent them from being a reliable toe-tip tracker by themselves.
- Exact candidate startup/release frames inspected: 12, 16, 20, 24, 28, 32, 34–40; the 60-Hz GLB action was inspected in world coordinates. `H = 2.756361830 m`.

## Findings

### P1 root cause: loaded toe patch translates, then snaps back

Use the generator forward axis F and fixed ground/world coordinates; do not subtract the root translation when judging whether a planted foot is stationary. The terminal toe mesh moves approximately half a metre during the interval that is supposed to be loaded:

| side | rocker onset | rear peak | release | loaded terminal-toe F motion | release reset |
|---|---:|---:|---:|---:|---:|
| L | phase .467213, key 57, video ~24 | .557377, key 68, ~28 | .704918, key 86, ~35 | `+0.488 m` (`~0.177 H`) | key 87→88: `-0.489 m` F, `+0.021 m` U |
| R | phase .467213, key 118, video ~48 | .557377, key 129, ~52 | .704918, key 147, ~60 | `+0.482 m` direct tip (`~0.175 H`); terminal centroid `~+0.490 m` | key 148→149: `-0.484 m` F, `+0.051 m` U |

The one-sample mesh jumps are approximately `[-0.026, +0.021, -0.489] m` (L) and `[-0.019, +0.051, -0.484] m` (R) in the measured `[L,U,F]` display basis. At 24 fps the corresponding visible transitions are approximately L frame 35→36 and R frame 60→61; the same phase repeats about one gait cycle later. A fixed-render color-mask witness corroborates the R failure: the moving lower-foot component shifts about 25 px (bbox left edge about 28 px) from frame 48 to 60, then returns about 20 px at frame 61. This is a screen-space witness, not a camera-metric claim.

**Interpretation:** the terminal toe chains are still being translated by the stride/foot transform while toe-loaded, and a discrete key/reset sends them backward at release. This is the P1 defect. The validator passes because it checks ground proximity and causal phase order, not horizontal/lateral planted-toe lock or one-sample continuity.

### Metatarsal/ankle rocker is not the primary failure

The foot-pivot U rise itself is smooth over the sampled rocker interval: L rises about `+0.0241 m` (`0.00875 H`) and R about `+0.0232 m` (`0.00843 H`), with no greater-than-1-mm U sign reversal found before release. Thus the correction must not remove progressive rocker. The toe witness still fails both continuity and strict planted-U bounds because the terminal mesh itself jumps upward by about 21 mm (L) and 51 mm (R) at reset.

### Toe-down and passive lag are not yet acceptance-safe

The toes do point downward at release: terminal pitch is about L `-6.5°` and R `-8.0°` (negative = toe-down). Immediately after the reset, however, pitch is only about `-2.0°` at phases .721311/.737705, then rises through `+0.4°` at .754098 and about `+7.1°` at .778688. Therefore the current export does not provide a clean five-sample (`~83 ms`) post-release toe-down/free-weight dwell before receiving preparation. The machine passive-lag value (`7` exported samples, about 0.117 s) does not prove toe-down posture because it measures angular decay, not the distal toe pose.

### Startup and seam

The action starts with L at phase 0 and R at phase .500. R is therefore already in its loaded/release half-cycle at startup: key 26 is phase .713115 and key 27 is .721311, with the same approximately `-0.484 m` reset around output frame ~12. The supplied captures whose approximate matches are frames 2, 13, and 16 are consistent with this startup window. Normal playback has no full-body freeze or catastrophic seam, but a clean approval cannot hide a foot reset in the first 20 frames; startup must be explicitly gated.

## Fail-closed acceptance contract for iteration 17

All gates apply to both feet and to both cycles. Any failure keeps the candidate at P1 FAIL; a validator-only PASS is not release approval.

1. **Planted toe witness (world/floor coordinates):** from rocker onset through distal release, the same distal toe patch must remain within `0.005 H = 0.0138 m` peak-to-peak in F and L, and within `0.003 H = 0.0083 m` in U. The hard adjacent-sample jump cap is `0.005 H`; target visible motion is at most 2 px at 960x540. A 0.49-m excursion or any 20+ mm one-sample U pop fails immediately.
2. **Progressive rocker:** rocker onset must be no later than phase `.48` and before rear-extension peak; metatarsal/foot-pivot U must be nondecreasing through release, with no sign reversal above 1 mm and no transform reset. Preserve the observed 15–20 loaded micro-adjustments rather than replacing them with a single step.
3. **Toe-loaded dwell and release order:** require 15–20 consecutive 60-Hz samples (`0.25–0.33 s`) with the distal patch loaded and within the planted bounds. Release only after that dwell and after the long rear stroke reaches its intended peak; target release phase remains roughly `.70–.72`.
4. **Articulation and passive lag:** at release, toes must articulate progressively, not remain rigid. Then require at least 5 consecutive 60-Hz samples (prefer 7–9) with terminal pitch `≤ -4°` toe-down and no immediate up reversal/reset, before receiving preparation near phase `.803`. A flat/toe-up pose before this window fails.
5. **Startup and loop:** either start from a neutral phase or require the first 20 rendered frames to satisfy the same planted/jump gates. Start/end corresponding body bounds must be within 1%, toe witness within `0.001 H ≈ 2.8 mm` and 1 px, and foot orientation within 1°; no hidden reset at the clip start or seam.
6. **Evidence:** rerender at 24 fps with a readable floor/foot contrast (or provide an equivalent annotated toe-witness pass) so that the world-space gate is visually auditable. A dark/merged-foot MP4 alone is P2 evidence debt, not closure of P1.

## Severity and disposition

- **P1:** planted toe drift plus one-sample backward/vertical reset; secondary P1 under the requested strict contract is insufficient post-release toe-down dwell. These block user-facing approval.
- **P2:** dark floor, foot overlap, and timestamp-free screenshot crops make direct screen tracking under-revealing; this is an evidence/readability issue, not a reason to waive the world-space failure.
- **P0:** none observed. No full-body freeze, catastrophic penetration, or unrecoverable render failure was established in the bounded frame review.

**Disposition:** iteration 16 remains rejected. Re-run the GLB/world gates and a readable 24-fps render after the toe-chain correction; do not approve based on the existing causal-validation PASS alone.
