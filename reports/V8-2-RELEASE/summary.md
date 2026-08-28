# V8.2 release productization evidence

## Verdict

PASS. `procedural-animation-toolkit(v8.2)` is a lean canonical release on
`codex/v8-2-release`. It contains one required iteration-b reproduction base,
one approved V8.2 GLB, reusable configuration/solver/verifier scripts,
authoritative pass evidence, and two bounded review MP4s. No rejected
candidate, cache, duplicate rebuilt artifact, or unapproved V8.1 package is
included.

## Reproduction

The clean-output build regenerated SHA-256
`a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`,
exactly matching the approved artifact. The snapshot verifier passed base and
candidate hashes, GLB JSON equality, non-empty approved change set, and the
two RESPIN clips' rotation-accessor allowlist.

The reusable contract is gain `0.3984375` applied in the official
world-relative rotation-vector basis, with deterministic neck cancellation.
It preserves root, pelvis, lower-body, tail, translation, non-walk, timeline,
and GLB-structure data from the included base.

## Quality and provenance

- Official Candidate-A evidence: PASS.
- Structural/mechanical and iteration-38 inherited locomotion evidence: PASS.
- Package size: 88 MB; largest files are the 43 MB base and 43 MB approved
  GLB, each below the 100 MB cap.
- Side review: 960x540, 24 fps, 240 frames, 10.000 seconds.
- Three-quarter comparison: 1920x540, 24 fps, 240 frames, 10.000 seconds.
- V8.1 source provenance SHA:
  `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`.

Exact package paths and hashes are in
`procedural-animation-toolkit(v8.2)/RELEASE_MANIFEST.json`; commands are in
`commands.log`. No merge or push is part of this release handoff.
