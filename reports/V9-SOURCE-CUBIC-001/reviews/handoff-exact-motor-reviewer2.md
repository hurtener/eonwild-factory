# Exact serialized handoff motor — independent narrow review

**Verdict: PASS. No P0, P1, or local P2 finding.**

Reviewed the exact clean head `60426de40279e81291b3e0affbf9bb465066b267`
(tree `3c843b439bbd604e4055f0e597ef6330bc8b4621`) against parent
`f9ca924bcc79943d2d2b7eeab28bef8763c18ec4`. The review was limited to the
three changed files: `src/eonwild_motion/factory/handoff.py`,
`tests/test_emitted_handoff.py`, and `tests/test_exact_emitted_tangent.py`.
The worktree was clean. I made no edits.

The new motor is computed as the exact serialized root world-translation
tangent in `root_motion.glb` minus the corresponding tangent in
`in_place.glb`, at the declared one-sided endpoint. The same exact vector is
then added once to in-place node and skinned-point velocities. This removes the
old adjacent-plan-slope assumption and remains correct for LINEAR tracks, where
the shared endpoint evaluator supplies the segment slope.

The helper fail-closes on a missing/ambiguous endpoint, missing root, multiple
clips, nonfinite motor, and disagreement between the two modes' complete node
topology, native timeline, root name/index, or serialized interpolation set.
Each package's normalized forward/up axes remain bound through
`require_runtime_axes`; the handoff path separately retains the locked recipe,
rig, contact, gait, phase, topology, and manifest checks. CUBICSPLINE evidence
now reports the actual serialized interpolation classification rather than the
former hard-coded LINEAR label.

Independent focused execution:

```text
PYTHONPATH=src:tests .venv/bin/python -m pytest -q \
  tests/test_emitted_handoff.py tests/test_exact_emitted_tangent.py
72 passed in 26.81s
```

The focused cases include unequal CUBICSPLINE endpoint tangents despite equal
two-key displacement, exact start and terminal motor recovery, unchanged
LINEAR behavior, mode-timeline rejection, and applying a supplied exact motor
instead of a plan slope. `git diff --check` passed. The author's retained
receipt is
`audits/source-cubic-handoff-exact-motor/receipt.json`, SHA-256
`632dbda2ba3c9a9b099546d5a36bef2d24c4ed930343f38e70a80039f5702db9`.

This review establishes the bounded serialized-motor and handoff-evidence
contract. It does not reopen the closed emitter, Blender adapter, source-law,
or broader package-verification stages, and it does not add a visual or
production approval.
