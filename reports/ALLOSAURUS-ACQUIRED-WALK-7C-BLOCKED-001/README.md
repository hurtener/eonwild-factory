# Allosaurus acquired-reference walk: emitted 7c checkpoint

## Status

The exact public factory compile at implementation head
`7c6272359f14d5f67a8b9de8b6079747e1a1cf13` (tree
`fd7975cab4081315b79d128a690e4d110e340ff3`) emitted both CUBICSPLINE GLBs,
but the candidate is **TECHNICALLY BLOCKED**. It is retained at
`ARC/out/allosaurus-acquired-reference-walk-007-release-7c62723/walk`.
Integrity reopens as `PASS` after the separately reviewed metadata inventory
fix; that fix does not change, rebind, or waive any motion gate.

This is not an accepted Allosaurus walk and does not establish two fully
animated animals. Visual review, continuous playback acceptance, Unity parity,
anatomical or biological approval, and production promotion remain absent.
The licensed raw reference and measured capsule remain private, ignored inputs
outside Git; this report retains only hashes and compact derived evidence.

## Exact blockers

The final emitted package reports:

- target residual `0.0010000027150181058 m` against the unchanged `0.001 m`
  limit. The excess is `2.7150181058 nm`; exact retained-package replay measures
  about `0.458 µm` of float32 transform-serialization displacement relative to
  the source query, so the strict failure remains authoritative while its
  numerical source is diagnosed.
- solved foot-pitch rate `750.1430087784727°/s` against `600°/s`.
- serialized node rotation rate `7620.683907817504°/s` against `1200°/s` at
  `Bone_028` / node 31 over `[1.0305405855178833,
  1.0388513803482056] s`. The validator labels this a conservative normalized
  Hermite interval bound. Root sampled the normalized curve at 1,001 points
  and observed `7522.320602821408°/s` near the interval endpoint. Independent
  source replay observes `7522.320501°/s` from the matching one-sided source
  tangent, while emitted playback observes `7522.320603°/s`. The quaternion
  differs by `5.4031°` at key minus `0.001 s` but is effectively stationary
  across key minus `0.0005 s`, the key, and the positive-side probes (the
  outgoing rate is about `0.000193°/s`). This localizes a source
  branch or switch inside the left stencil rather than CUBIC interpolation
  amplification; the exact source-law cause is still being traced.

Unreachable extension (`0.0009999111963139296 m`) and the scalar articulation
violation (`0°`) pass their existing gates. No threshold was changed.

## Inspection and adjacent work

Root inspected five emitted side poses and five three-quarter rate-witness
poses. The foot shape and posterior thigh attachment are visibly improved over
the earlier rejected diagnostic, but the stills cannot establish smoothness or
contact timing. The package is blocked, so no full native review or acceptance
render was produced.

The acquired transition seam at `45c50cb7a48219ee2242e3918bfaa1e039883812`
has two closed source-bound reviews. It remains non-emitting evidence only.
A later integration replay exposed a grounded-binding compatibility defect;
the narrow fix at `655bd1d6048147cf1e1aa00d03512b44c2f42461`
restores the archived 7c grounded binding while retaining the transition-only
binding fields and substitution guard. Root and reviewer 2 closed that exact
fix, and the retained 7c package again verifies integrity `PASS` with its
unchanged technical `BLOCKED` status. No transition package or join is claimed
here.

The separate Allosaurus fast configuration at
`09404148dca7111e6fb052ce78bcc4eb2a4823f5` passed 283 sampled, non-emitting
source queries under existing limits. Its public compile is still running and
has no emitted acceptance in this checkpoint.

## Validation boundaries

- Exact 7c local factory suite: 1,202 tests plus 21 subtests passed in 411.06 s.
- Hosted Tarbosaurus shared-set run at older head `a80150e`: walk, fast walk,
  start, stop, and both declared joins passed. Its packages still say visual
  `PENDING`, Unity `NOT_RUN`, and production false.
- Current 7c hosted CI was pending when this checkpoint was written. The older
  hosted result is useful coverage, not current-head or all-catalog green
  status.
- Ten emitted Allosaurus stills were inspected; native-speed playback and Unity
  were not run for this package.

## External evidence inventory

All `ARC/...` paths resolve beneath the task storage root
`/Volumes/m2-extended-disk/Repos/eonwild-task-storage/01a07d0e-00b8-7a51-9095-c2da82025521`.

| Evidence | External path | SHA-256 |
|---|---|---|
| Compile/package receipt | `ARC/audits/allosaurus-acquired-reference-release-7c62723-001/receipt.json` | `52bed23b0b4000392e0c53e6ae62a89968b23ca58cfe4bd029a3b953fc028cc6` |
| Package validation | `ARC/out/allosaurus-acquired-reference-walk-007-release-7c62723/walk/validation.json` | `fb4ca7be0e790049060e27e09b7a4e38155d4c9e11227ed9531cb94275c5044c` |
| Emitted-rate root replay | `ARC/audits/allosaurus-emitted-rate-root-7c62723-001/result.json` | `00412ff0fdcbae8ce37304ad868869f85ed11f686fbc4a87243b870d4f6c3363` |
| Source-rate reviewer 2 replay | `ARC/audits/allosaurus-source-rate-witness-7c62723-001/result.json` | `f93fea04c8fd8bb692250b82213eb321b25da84a7b0173e4e2b7f54108a8e4b9` |
| Residual float32 replay | `ARC/audits/allosaurus-acquired-reference-7c-residual-replay-001/result.json` | `e85441c33d27c138ee2af2ad9562080ef873301d41304cccdeddc4ff4ce5cdf2` |
| Ten-still root review | `ARC/out/allosaurus-emitted-7c62723-blocked-stills-001/root-still-review.json` | `a59e7d38fa27f62a5a331b70adac776c07644ae3e33187e51454702c33d2cbf2` |
| Exact 7c full suite | `ARC/audits/contracts-7c62723-root-002/receipt.json` | `aa635b30125db4d66fd343136f5f6318bf9102bd035f879e167691343ce30b8e` |
| Tarbo hosted a801 run | `ARC/audits/shared-ci-a80150e-success-root/receipt.json` | `d9af116ba224b040693fb2d58f33590381a788742f1aca02dae58b3993f2db73` |
| Transition root review | `ARC/audits/acquired-transition-root-45c50cb/review.json` | `eb78242e3d107f502a6522f0e9b43e56f9065f1be8177f3350f8033a962300c5` |
| Transition reviewer 2 | `ARC/audits/allosaurus-acquired-transition-reviewer2-45c50cb/README.md` | `139c35988410b17c18ee611878c35fc6338347eaa77f6d40bc06d29bcb1c950c` |
| Legacy binding closure, root | `ARC/audits/legacy-authored-binding-root-655bd1d/review.json` | `7e8c15b01bc76642861290f2afc59c51a39278d83658aef75f63389c27409e1e` |
| Legacy binding closure, reviewer 2 | `ARC/audits/legacy-authored-binding-reviewer2-655bd1d/README.md` | `054129d1472d9b60c2e5aaf2188d638ac10621c25af5a65596b6a3d7fec3eb49` |
| Metadata postfix | `ARC/audits/acquired-package-metadata-postfix-20229be/receipt.json` | `3b683a7c95e537d72c144b58639ea66c9faab4ab24dd9da3bb4e1a5f34645de2` |
| Metadata reviewer 2 | `ARC/audits/authored-material-metadata-reviewer2-20229be/README.md` | `1cef0e2c4f0461d5cd658b13981b4edca8d1fe093392e848ab150a6b0253cde8` |
