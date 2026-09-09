# Adult V10 load-acceptance diagnostic

Frozen implementation `94c81e7e3bb00e2e6057fd1babb183adb70ff9e3`
adds one opt-in, support-timed pelvis compression and matched trunk response.
The successor performance profile and V10 recipe are versioned but unselected;
existing V9 inputs, candidate matrices, emitters, defaults and thresholds remain
unchanged. Both independent code reviews found P0/P1=0.

The authored comparison uses `0.01 body height` peak pelvis compression and
`0.35 degrees` peak trunk response over the existing 1.23-second
sole-support-midpoint interval. At V9 body height this is `22.841756 mm` and a
calculated peak added vertical acceleration of `0.362352 m/s²`. These are
kinematic art-direction inputs, not measured load, COM, ground force, work,
muscle capacity or biological response.

## Reopened candidate evidence

The immutable package at
`out/tarbosaurus-adult-walk-load-acceptance-v10-94c81e7` has manifest SHA-256
`e3e9923526ced4e2fd08b5f4ffaa455edb78ce66020c3c3f369e6336d5f0aff7`.
Root reopened it with integrity `PASS` and technical status `BLOCKED`.
Contact, articulation, extension, solver feasibility and rotation-rate checks
pass in both modes, and interior foot clearance is preserved. The exact LINEAR
loop reaches `3.965012792580725 mm/s` against the unchanged `1 mm/s` limit,
compared with V9's `3.23101227406632 mm/s`; this candidate does not improve or
pass exact continuity.

The source-bound emitted audit preserves the unchanged 297-row, 2.46-second
plan contract, a `22.841036 mm` reopened peak pelvis displacement, approximately
`0.35 degrees` reopened chest rotation at both double-support landmarks, and
near-zero added displacement at both sole-support landmarks. It grants no
full-surface pressure, mass-physics or force authority.

Root inspected all 148 front/side frames and paired same-size double-support,
sole-support and control stills. Both comparison pairs passed scrub, frame
step, 1x play, pause and restart-to-end browser controls. No P0/P1 visual
regression was found; the added compression remains restrained. This completes
the recorded frame and control review, while perceptual weight acceptance stays
open. The implementation is accepted only as an unselected diagnostic. It has
no Unity, biological or production approval.

## Retained evidence

- `analyze.py` SHA-256 `8f18d8b6888bf7215fdd353672905a2f4df7571c507ec9d49e49556613c03ca1`
- `result.json` SHA-256 `de5947e1c4bf9cac3be027c59c0cbf923185c96e83f5ed385b66b8dd4219d9bf`
- Root R1 review SHA-256 `c07bfe1f8e3601676d0e9271dca83358868a3524e5fd76721f04cbf673fc52c3`
- Reviewer 2 R1 review SHA-256 `1287b681090cd023f3b9af47ec24f7aa42409c443df277a6b79b2efd0ec311f0`
- Root frame review SHA-256 `45cbad3d354da12e77d3305910acb0073ab59d5e80263655950b9585dc689880`
- Root browser-control receipt SHA-256 `c1f49a442b827f02b207665484cd0b5d168a3aa0d6a82e5ae493457d4239fb0e`

The copied audit and reviews are byte-identical to the task-storage receipts.
The final combined integration suite passed 969 tests plus 21 subtests in
795.48 seconds at exact head `4e41689671bb9787c743c72334bcd61334fd5aac`;
its source-bound receipt is retained in
`reports/V9-CLOSED-DIAGNOSTICS-83AA5E5-001/`.
