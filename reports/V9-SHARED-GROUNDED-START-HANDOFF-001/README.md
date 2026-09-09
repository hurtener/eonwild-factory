# Shared grounded walk-start and handoff checkpoint

The full start package generated at `f6e3e19d86a93c70a9bff4b9e59b293254a73aa3`
passes its recorded technical gates. It contains 1,034 emitted keys over
7.9875001907 seconds. Solved foot pitch peaks at 284.920421 degrees/s below the
unchanged 600-degree/s limit; articulation violations and unreachable extension
are zero. This does not approve the complete start/steady/stop sequence.

## Actual package join

The first public handoff attempt under `215588c` rejected before comparing
boundaries because it compared the exported animal-scaled floor with the raw
source contact profile. The fix at `1f783f87d3604b7a2fe6ae5acb1998569ed6582f`
resolves the locked animal/source through the existing calibration contract and
uses the compiler's existing contact-profile scaling operation. Strict floor
equality and all join tolerances remain unchanged; absent-animal legacy inputs
retain their previous behavior. No exported animation or contact plane was edited.

Both bounded code reviews closed with no P0/P1 findings. Root's focused handoff
and tangent checks passed 76 tests. The author's replay of the exact start and
matching steady package passes in root-motion and in-place modes. The independent
root replay is still running at this report checkpoint. The matching steady
manifest is `a8bcf3dd5c6c9a29e25fab41313f2830c215f3fa2f85b657d72002e0d00ef48f`;
the start manifest is `8dea3f8bc07f42528bb5bf36c390aa03475c5bb0f716c70daf0798655aaf0193`.
The previous V10 media is not substituted for this same-generator steady package.

## Native inspection

Root inspected all 240 side frames at native 30 fps and eight exact-time oblique
stills. The 960-by-540, eight-second film decodes completely. Short steps open
progressively toward the steady gait, and the forward head posture is retained.
The first recovery has low visible clearance, and the known proximal thigh
crease remains apparent. These are open review concerns. No whole-body visual
approval or browser/native-speed playback is claimed from the frame inspection.

Media remains on external storage under
`out/shared-grounded-start-native-f6e3e19-001`. Compact render receipts, media
hashes, exact coverage and findings are retained here. The stop export and
complete connected films remain pending. Unity is NOT_RUN; biological and
production approval are absent. The rejected sprint prototype is unrelated to
this working walking baseline.
