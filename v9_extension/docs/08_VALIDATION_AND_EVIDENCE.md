# Validation, acceptance, and evidence requirements

## 1. Four independent acceptance dimensions

A release passes only when all four dimensions pass:

1. **Structural/reproducibility:** files, schemas, hashes, GLB structure, determinism.
2. **Mechanical:** contacts, root/velocity, joint limits, support, momentum where applicable.
3. **Perceptual:** fixed-camera motion quality, weight, animal character, transitions, deformation.
4. **Scientific honesty:** provenance, uncertainty, and correct labeling of gameplay interpretations.

A high score in one dimension cannot compensate for failure in another.

## 2. Structural and release gates

- source/config/tool hashes match;
- historical release directories are unchanged;
- exact inventory with no cache/temp/rejected content;
- all JSON/YAML schemas pass strict validation;
- semantic roles and hierarchy resolve;
- joint/skin order and rest deformation remain valid;
- expected clip and event inventory is complete;
- same deterministic inputs reproduce the declared mechanical artifact;
- all changed accessors/channels fall inside declared scope.

## 3. V8.2/V8.3 regression gates

### Compatibility walk

- exact V8.2 output SHA where using its original packaging;
- otherwise exact sampled/accessor equivalence and explicit repackaging report;
- same root trajectory, contacts, duration, sample timeline, and clip names/semantic mapping;
- no new non-walk changes.

### Balanced walk

- root path and timing stay within pinned tolerance;
- contact event times stay within tolerance;
- loaded sole/toe world drift stays below release threshold;
- no loaded-foot yaw beyond threshold;
- no penetration or loaded gap regression;
- pelvis/body change is correlated with support phase;
- joint position/rate/acceleration limits pass;
- side and 3Q review judge the result at least as convincing as V8.2.

## 4. Root-motion and in-place equivalence

For every paired view:

- normalized phase is identical;
- body-relative transforms reconstruct each other after root factorization;
- contact states/events are identical;
- support foot and transition compatibility are identical;
- only declared root/world displacement differs.

Independent solves fail this gate.

## 5. Contact gates

Per loaded phase:

```text
maximum patch translation drift
maximum patch yaw/roll/pitch drift
minimum and maximum terrain gap
penetration depth
contact-state duration
load/unload ordering
toe-off ordering
```

Render contact witnesses and support patches in a debug video. An ankle marker alone is insufficient evidence.

## 6. Joint and deformation gates

- hard joint envelopes never violated;
- preferred envelopes reported by load/action phase;
- angular velocity and acceleration remain below configured limits;
- quaternion signs are continuous;
- no knee inversion or snap-lock;
- no mouth, eye, toe, or shoulder mesh failure;
- rest-skinned and neutral-pose meshes remain within tolerance;
- contact-preserving post-process masks are enforced.

## 7. Transition gates

Check at source bridge entry and target handoff:

```text
pose error
root position/orientation error
linear/angular velocity mismatch
support/contact-state compatibility
pelvis/support bias
tail state and angular velocity
breathing/overlay state
event duplication or omission
interruptibility/commitment state
```

Run transitions from multiple source phases and both support feet where applicable.

## 8. Animation-specific gates

The detailed catalog contains release-blocking checks for every animation. Examples:

- idle: asymmetric support, no visible loop reset, no rhythmic head bob;
- walk/run: stride matches root speed, no foot slide, economical swing;
- starts/stops: measurable acceleration/braking distance and valid support steps;
- bite: load precedes drive, jaw opens before target, contact/recovery windows correct;
- miss: overextension and stabilizing step, no instant neutral reset;
- feeding/drinking: target-relative endpoint and stable support;
- lie/rise: no pelvis teleport and not simple reverse playback;
- stumble/death: visible failed recovery attempt and constrained ground contact;
- calls: inhalation, resonance, semantic posture, and post-call listening/hold.

## 9. V9 body and dynamics gates

- mass fractions sum to one within tolerance;
- local and whole-body COM are reproducible;
- inertia tensors are symmetric positive definite;
- uncertainty scenarios are seeded and reported;
- static support uses real contact patches;
- dynamic phases include COM velocity and upcoming contacts;
- takeoff impulse and ballistic **whole-body COM** trajectory are measurable;
- root is reconstructed from COM and changing pose;
- angular momentum changes only through valid external moments/contacts;
- landing velocity and negative work are absorbed continuously;
- infeasible airborne attacks select grounded fallback;
- growth parameter changes are monotonic or explicitly justified;
- tier switching preserves phase, root velocity, contacts, and tail state;
- second body fixture uses the same generic code.

## 10. Perceptual evidence suite

For each P0 animation and representative parameter sweep, produce:

```text
fixed side view
fixed three-quarter view
front/rear view when lateral behavior matters
contact-witness overlay
skeleton and joint-limit overlay
root/velocity plot
COM/support overlay when available
key phase contact sheet
baseline side-by-side comparison
```

Use fixed cameras, identical timing, neutral lighting, full feet/tail in frame, and no motion blur that hides contact.

## 11. Review rubric

Independent reviewers score and comment on:

- mass and support;
- foot/toe contact;
- force chain and absorption;
- torso/neck/head coherence;
- tail behavior;
- forelimb character;
- loop/transition continuity;
- species identity;
- target/environment interaction;
- growth/condition readability;
- absence of animation artifacts.

Any release-blocking defect yields FAIL regardless of average score.

## 12. Scientific-honesty checks

- every scientific input has provenance/status;
- gameplay hypotheses are labeled;
- exact Tarbosaurus force, speed, jump, joint, or vocal claims are not inferred from tuning values;
- V8.3 legacy balance is not called COM validation;
- resting, social, and attack interpretations are described as reconstructions where evidence is absent;
- generated audio/visual reference provenance is recorded.

## 13. Evidence filenames

```text
resolved-profile.json
rig-resolution-report.json
contact-witness-report.json
jaw-calibration-report.json
motion-plan.json
animation-manifest.json
changed-channel-report.json
mechanical-validation.json
contact-report.json
joint-limit-report.json
transition-state-report.json
capacity-feasibility-report.json
growth-sweep.json
perceptual-review.json
scientific-honesty-review.json
release-manifest.json
SHA256SUMS.txt
```
