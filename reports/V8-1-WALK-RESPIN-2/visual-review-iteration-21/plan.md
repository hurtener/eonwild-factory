# Iteration-21 visual-review plan

## Task

Perform an independent, read-only visual review of the iteration-3 MP4 for the iteration-21 walk respin. Compare native 24-fps cadence and representative phase frames against the supplied relaxed-walk reference and the five user captures, with special attention to startup, both toe-offs, loaded distal contact, rocker timing, passive toe lag, transfer, seam, and framing. This is an approval-candidate review only; it must not approve final release.

## Files to touch

- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-WALK-RESPIN-2/visual-review-iteration-21/plan.md`
- `/Volumes/m2-extended-disk/Repos/eonwild-factory/reports/V8-1-WALK-RESPIN-2/visual-review-iteration-21/visual-review.md`

No engine, GLB, showcase, or media files will be modified. The report directory is the explicitly assigned evidence ownership boundary.

## Acceptance checks

- Verify candidate and reference identity, dimensions, frame rate, duration, and hashes.
- Review the first 20 candidate frames and representative frames around both toe-offs at native 24 fps.
- Compare the same contact and mid-transfer cues against the supplied user captures and relaxed reference without treating their differing camera as metric calibration.
- Check for distal toe drift/reset, vertical pop, rocker monotonicity, toe-down passive lag, seam/startup defects, overextension, penetration/hover, posture, and framing.
- Explicitly judge the measured rocker-onset-to-rear-extension-peak lead against the requested `.04-.10` cycle intent; do not treat causal-validator ordering alone as visual approval.
- Record P0/P1/P2, approval-candidate disposition, limitations, and reproducible inspection commands.
- Scan the report for trailing whitespace and verify the requested directory contains only the report artifacts.

## Unresolved assumptions

- The reference and captures are qualitative gait/contact references; their camera, crop, lighting, and model do not provide metric screen-to-world calibration.
- Approximate frame numbers are render-frame observations, not source timestamps for the user captures.
- The exported `respin-2-validation.json` is corroborating machine evidence. It does not replace the visual timing judgment, and its top-level PASS does not enforce the upper bound of the desired rocker lead.
