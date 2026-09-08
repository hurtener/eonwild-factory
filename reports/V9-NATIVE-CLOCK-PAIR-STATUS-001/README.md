# Native-clock gait-pair status at 7920c59

This report records the four local transition-trio results generated from exact
source `7920c59dd354027b8784483bb208fd0e6229cd91`. All 12 package locks contain an
identical nonempty 88-entry `engine_files` map. Every mapped file byte-matches
that commit; the map's canonical compact, key-sorted JSON SHA-256 is
`7a7b6517d43faa06d8a0216625e510d6f3f83c2b8fe624ff8724fd622b9a9b44`.

All 12 individual packages pass integrity and technical validation. The direct
join outcomes are:

| Sustained gait | Start, both modes | Stop, both modes |
| --- | --- | --- |
| walk v3 | `PASS` | `PASS` |
| reverse-walk v4 | `PASS` | `PASS` |
| run v4 | `PASS` | `PASS` |
| sprint v4 | `BLOCKED` | `BLOCKED` |

Sprint uses the fixed 480 Hz interface evidence. Its start world-velocity
mismatch is `0.001412795 m/s` in root motion and `0.001493701 m/s` in place. Its
stop mismatch is `0.001202134 m/s` and `0.001199715 m/s`, respectively. These
exceed the unchanged `0.001 m/s` limit. No evaluator or gate was changed.

The adjacent `evidence.json` preserves each result, handoff and package-manifest
hash, plus the world and material velocity values for every join mode. Its host
paths point to ignored `out/` evidence and are identifiers for the retained
local artifacts; they are not runtime inputs.

An independent host recheck verified every emitted package payload hash and the
identical engine maps against the exact source. Its receipt is
`out/continuation-native-clock-7920c59-pairs/host-verification.json`, SHA-256
`2a740d9b6318b4609f2d1608d05a3a33147f2e4866aa991022b3a7c907a09198`.

The same exact head passed 136 focused tests covering articulation profiles,
emitted handoffs, transition support coordination, catalog bindings, recovery
controls and articulated contact partitioning. The host validation receipt has
SHA-256
`65be477495e6e2f7fe4cc4cc279bcf406d7b30d4b69a7397582df404b339c746`,
and its test log has SHA-256
`20bfc1e30dc363d88f17761a98eb11e518f1aa859fc1c5e18900b5f5a5f17800`.

This is a focused local exact-head record. At recording time on 2026-09-07, the
fetched remote had no commits absent from the local branch, while the local
branch was ahead; no remote-CI run exists for this source. This report also does
not claim a current full-suite pass. Native visual review is `PENDING`, Unity
validation is `NOT_RUN`, biological validation is absent, and production
approval is false. In particular, it does not accept the revised adult recovery
motion.
