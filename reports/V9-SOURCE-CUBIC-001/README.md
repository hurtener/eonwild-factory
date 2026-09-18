# Source-derived CUBICSPLINE diagnostic

Frozen publication source `60426de40279e81291b3e0affbf9bb465066b267`
stacks the reviewed all-key source-derived CUBICSPLINE emitter, task-owned
exact Blender playback adapter, and exact serialized handoff motor reader on
published base `170617beda89b1836aabebd983b7891549e03d65`. The emitter remains
opt-in; existing LINEAR defaults and packages are unchanged.

The emitter evaluates the existing bound source motion at every serialized key,
uses independently evaluated 1 ms one-sided endpoint stencils with a 0.5 ms
convergence check, emits glTF Hermite tangents in seconds, and reopens the exact
serialized curves through TRS, FK, and LBS consumers. Quaternion values and
tangent signs are kept consistent, and the emitted Hermite quaternion is
normalized during playback. Existing contact,
extension, articulation, loop, and 1200 degree/s rotation-rate limits remain
unchanged. Numerical tangents remain estimates; no analytic derivative, branch,
global-C1, biological, or physical authority is claimed.

All emitter and adapter R1/R2 findings are closed. The final narrow reviews
report no P0/P1 findings. The combined source-equivalence receipt proves the
11 emitter paths match reviewed `7cc9886` and every adapter path matches
reviewed `527d274`. The corrected full suite passed 988 tests plus 21 subtests
in 836.73 seconds at combined source `f9ca924`; the later handoff-only commit
passed 72 focused tests at `60426de`, with both narrow reviewers reporting no
P0/P1 findings. The earlier broad invocation that collected archived toolkit
copies is excluded from acceptance.

## Actual packages

The pinned adult V9 steady cycle at exact emitter head `67a6756` is technical
PASS over 297 keys and 296 midpoints. Its package manifest is
`a96e35559ac2e2f9c8aa71b5e33f35e61bb0b92a9e41138ce0e3651efe5ae23a`;
root-motion GLB is
`5a3d7689ac2ed07ff88eaefe5333faf737da487a0be834bbeafebf895b7411dd`;
in-place GLB is
`a38a0ae1bddcd6cc81987ca655ef09b55030801d3ba1872f645d26eafe63c5e5`.
All seven recipe inputs are hash-bound. Khronos reports zero errors and four
warnings per GLB. Exact endpoint checks reach 0.277043 mm/s at world joints and
0.204859 mm/s at ordered foot material, below the unchanged 1 mm/s limit.
After a real Cycles evaluation, task-owned Blender playback stays within
2.350 µm in-place and 2.442 µm root-motion same-index skin error.

The adult V10 load-acceptance candidate compiled on combined head `f9ca924`
with technical PASS over 297 keys, 296 midpoints, and 2369 checked source
times. Its package manifest is
`80b15c5d7dba7aa294335c46e55e8e8776aa7d177507c3c7fb3f96628252153d`;
root-motion GLB is
`85f19b01805153269988865752737e368be292f8fc49d5e527dfcf5f3ec4b2a4`;
in-place GLB is
`ced935c771749922cbfa3209ec76ba9a2699ec7c928797753fb94c967c31cd97`.
The corrected reference-body audit is copied under
`evidence/reference-body-002`. Independent serialized checks reach 0.261947
mm/s at world joints and 0.203975 mm/s at ordered foot material, below the
unchanged 1 mm/s limit. Khronos reports zero errors and four warnings per GLB.
Task-owned Blender playback remains within 4.482 µm across all 59169 vertices
at 18 sampled times per mode and 2.318 µm after real Cycles evaluation. All 100
engine files and seven input bindings were checked without payload mutation.

The matching-camera review of all 296 paired V9/V10 frames is
**REVISION_REQUIRED_BODY_WEIGHT_TRANSFER**. The load pulse is slightly visible,
but the front body remains too centered and the torso silhouette near single
support appears displaced toward the raised-foot side. Technical PASS does not
supply visual or physical approval.

The actual walk-start transition compiled at `36f311e` in 2703.32 wall
seconds. It is technical PASS over 0–7.9875 s, 1034 keys, 1033 midpoints, and
8265 checked source times. Its package manifest is
`966cf6f2f1154a17ed75438c6461693e22858c16f985c81cd85e56807d1f7d08`.
The final verifier reopens it with integrity and technical PASS.

The original start-to-steady report is retained as superseded evidence. It
hardcodes a LINEAR classification and reconstructs the in-place motor from
finite-difference plan travel, so its root-motion result remains valid but its
in-place motor was approximate. At `60426de`, the reader derives the motor from
the same package's root-motion minus in-place serialized root tangents and
reports the actual interpolation. Both narrow reviews pass. The corrected
actual rerun passes both modes with identical maximum differences of 12.362932
µm/s at world nodes and 9.994949 µm/s at material points. Direct stop and
steady-to-stop join evidence remain **PENDING**.

The earlier generic walk Stage 2 package came from a dirty descendant of
`c48e746`. Its retained checkpoint binds the executed engine-file hashes; it
is not evidence of an execution of committed `c48e746`.

## Scope

The Blender adapter samples immutable CUBICSPLINE local TRS at render time
after detaching the importer's approximate AUTO actions. It does not create
native Blender cubic curves and cannot establish CUBICSPLINE-to-FBX transport.
Approved multi-clip LINEAR assets keep Blender's stock path.

These packages are unselected diagnostics. No Unity parity, browser playback
acceptance, production activation, biological validation, or physical
simulation is established. Browser control review is NOT_RUN_POLICY_BLOCKED.
V10 visual approval remains open, and corrected direct-join evidence remains
available only for start-to-steady; stop remains pending.

## Evidence inventory

- `evidence/full-suite.json`: corrected combined test acceptance.
- `evidence/source-equivalence.json`: exact reviewed-path binding.
- `evidence/adult-v9/`: package, input, endpoint, and native playback facts.
- `evidence/adult-v10/`: package, validation, checkpoint, tangent, native,
  Khronos, endpoint, and visual-verdict facts; heavy arrays/media remain on SSD.
- `evidence/walk-start/`: package, runtime, validation, checkpoint, reopen,
  and immutable original handoff facts.
- `evidence/handoff-exact-motor/`: frozen implementation and corrected actual
  start-to-steady rerun receipts.
- `evidence/reference-body-002/`: corrected reference-body audit.
- `reviews/`: independent emitter, Blender adapter, and exact-motor handoff
  review reports.
