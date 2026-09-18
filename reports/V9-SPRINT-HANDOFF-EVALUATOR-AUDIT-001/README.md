# Sprint handoff evaluator audit

This bounded audit preserves two exact native-time sprint handoff diagnostics
and an adversarial examination of the velocity estimator. It does not approve a
motion, replace an evaluator or relax a gate.

## Result

Both diagnostic trios are `BLOCKED`. Every start, steady and stop package passed
its individual integrity and technical checks. Every root-motion and in-place
join exceeded the unchanged `0.001 m/s` world-space linear-velocity limit.
Visual review remains `PENDING`, Unity validation remains `NOT_RUN`, and
`production_approved` remains false.

| Interface rate | Start root / in-place (m/s) | Stop root / in-place (m/s) |
| --- | --- | --- |
| 480 Hz | 0.001412795 / 0.001493701 | 0.001202134 / 0.001199715 |
| 960 Hz | 0.001759369 / 0.001757259 | 0.001768069 / 0.001767965 |

The 960 Hz result does not converge below the gate. No additional density sweep
or motion shaping was accepted from this investigation.

The two result files preserve the complete package and handoff summaries:

- `fixed480-results.json`: SHA-256
  `d9dcf249372b78bee0d6fa3975badd874330463f55dbaf9de83fcd29a79446e5`
- `fixed960-results.json`: SHA-256
  `d03cb2a7084ad57e30e08b4f0bfb9fb0928c6f8b24d37cf31dad2ebafc2086ce`

All six package locks contain an identical nonempty 87-entry `engine_files` map.
The SHA-256 of its canonical compact, key-sorted JSON encoding is
`fdef5b5b2fd0a44755ab1649e07f93467c9d0b65d8a9b6ed8dccf6f98b355e40`.
The map matches the interface implementation at commit `747683b`. The result
files' `source_sha` is `65276b6f27f6ab1a0eba0d81d9ca147dcbb9307b`, because the diagnostic checkout
had uncommitted interface changes when it generated them. That Git field alone
is therefore not an adequate source identity for this evidence; the package
locks and their file hashes are authoritative.

## Estimator investigation

The archived `evaluator-adversarial.py` reproduces the current three-point
one-sided quadratic estimator on the exact float32 timestamps and emitted world
transforms from the 480 Hz trio. Its SHA-256 is
`1cec0ada7f14681b3cd9b384f17a1e574f7dadc15a8a39df558d8cb81409a034`.

The probe constructs analytic translation and rotation controls and a smooth,
periodic four-metre tail point driven by a five-degree third harmonic. The
analytic trajectory has the same derivative on both sides of the declared
interface and a peak angular speed of about `196.69 degrees/s`. With float32
emission, the current estimator reports false world-velocity mismatches of
`0.001386855 m/s` at start and `0.001377962 m/s` at stop. A five-point quartic
estimate lowers those synthetic values to `0.000847670 m/s` and
`0.000550186 m/s`.

That synthetic improvement does not transfer safely to the emitted packages.
On the real trio, the quartic estimate increases the maximum start mismatch to
`0.002104168 / 0.002558871 m/s` and the stop mismatch to
`0.006603930 / 0.006601147 m/s` for root motion / in place. Other tested cubic
and least-squares alternatives also regress the real witness. The five-point
windows reach irregular or coarser samples outside the two dense interface
neighbours, and the quartic derivative weights have an L1 norm as high as
`5119.994/s`, compared with about `1920.002/s` for the current estimate. This
amplifies float32 transform noise.

Adversarial velocity jumps show a second failure mode. Depending on jump
direction and existing estimator bias, both the current and quartic estimators
can report a real `0.00125 m/s` discontinuity below the `0.001 m/s` threshold.
Their minimum reported values are respectively `0.000918985 / 0.000923915 m/s`
and `0.000072457 / 0.000346638 m/s` at start / stop. Both detect all tested
directions for jumps from `0.002` through `0.005 m/s`.

The counterexample establishes that the current finite-window check can produce
a small false mismatch on a smooth trajectory. It does not establish a safe
replacement. The alternatives examined here either amplify real emitted error
or can conceal a small genuine discontinuity more severely. The evaluator and
the `0.001 m/s` gate therefore remain unchanged, and the recorded joins remain
truthfully `BLOCKED`.

## Reproduction record

The original report is excluded from Git with other `out/` artifacts. A host
rerun that changed only the output path produced the same report bytes:

- original report SHA-256:
  `016ec2412d8ead045c42334528114c089133b633f666e2b58431185e64a83f86`
- host report:
  `out/continuation-handoff-evaluator-audit-001/host-report.json`, SHA-256
  `016ec2412d8ead045c42334528114c089133b633f666e2b58431185e64a83f86`
- host script:
  `out/continuation-handoff-evaluator-audit-001/source-original.py`, SHA-256
  `1cec0ada7f14681b3cd9b384f17a1e574f7dadc15a8a39df558d8cb81409a034`
- host reproduction receipt:
  `out/continuation-handoff-evaluator-audit-001/host-reproduction.json`, SHA-256
  `a70f5121554199160e9da91cc93e053365b9a0a69cf6c25ec15f8dcec369aba9`

The archived probe intentionally preserves the exact host paths used for the
reproduction. To repeat it elsewhere, provide the same 480 Hz package layout
and update its repository and package-root constants; such an edit creates a
different probe hash and must be recorded as a new reproduction.
