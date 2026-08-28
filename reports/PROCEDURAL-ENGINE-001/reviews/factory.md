# PROCEDURAL-ENGINE-001 — independent factory review

## Scope

Reviewed exact commit `a0e88479f16a6b72d66eb9e435a35f2e49439191` in
`/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip`. This is a
read-only architecture, command-path, and rendered-output review. No engine,
profile, artifact, or media file was changed.

## Verdict

**P0: 0.  P1: 1.  P2: 0.  HOLD for the P1 below.**

The implementation is a coherent first vertical slice, not a manual GLB edit
or a relocated V8.2 script. `eonwild-motion` has a single installed command
surface; it separates schema-validated semantic rig/family/species/motion/layer
data from the GLB and math primitives, a registered layer implementation, and
the build/validate/render/compare/promote orchestration. The source package
does not import the legacy toolkit, and a source scan found no release-specific
bone, clip, species, or approved-artifact literals in `src/eonwild_motion`.
The one-morphology family claim is appropriately labelled provisional.

The external-work-root guard is real: an attempted build with an in-repository
work root failed before creating it. Build output, requests, Blender logs,
validation, comparison, and render stayed below an external temporary root.
The legacy folders are explicitly classified frozen migration sources.

The five commands do bounded, non-placeholder work:

- `build` verifies every locked input, applies only declared semantic rotation
  channels/accessors, then requires the exact approved GLB SHA.
- `validate` checks package inventory, hierarchy, accessor layout, timeline,
  glTF validation, and undeclared-byte changes.
- `compare` emits the technical baseline/candidate difference report rather
  than accepting image-only output.
- `render` invokes Blender with `--python-exit-code 1`, imports the generated
  GLB, selects the declared clip/frame, calculates mesh bounds, and writes a
  fixed-camera PNG.
- `promote` accepts only a passing clean build at the same Git head, validates
  independent approvals, re-validates the artifact, rejects overwrite, stages
  a content-addressed copy, and atomically renames its destination last.

The retained negative suite exercises hierarchy, interpolation, timeline,
accessor layout, package pollution, zero motion bounds, dirty locks, changed
artifact bytes, and promotion overwrite/dirty-source failures. It passed all
19 tests in 23.029 seconds during this review.

## Reproduction evidence

Using one new external temporary work root, the reviewed CLI produced:

- build: approved GLB SHA
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`;
- validation: 0 glTF errors, two declared warnings, 67 rotation channels and
  245 samples for each declared walk clip, and zero undeclared byte changes;
- compare: JSON-equivalent GLB structure and zero changes outside the declared
  chest/neck/head rotation accessors;
- render: a genuine Blender 5.2.0 LTS PNG at 640x360;
- source status/diff check: clean after the non-promotion commands.

The rendered frame is full-body, with head, both feet, torso, and tail in
frame and readable texture/lighting. It is useful fixed-camera evidence for
the profile’s declared frame, although it is deliberately a still rather than
a locomotion playback review.

## P1 — asserted pinned render hash is not reproducible

`reports/PROCEDURAL-ENGINE-001/evidence.json` and `summary.md` assert the
render SHA-256
`e6ed5469d8a095b12c3ec073ecac2d710593861305ca91fb0d8f15f517089ebd`, but
the reviewed render command produced
`e3fa4acadb435a07792d9f39b61fd03759d9269276bc0d163e55e6131d5c78a5`; an
immediate second identical invocation produced
`c491a806b197b7bbf6bdf2ceae5b2a434c47c8e1e369eb08a2e35c1c61de252b`.

This is not a visual nondeterminism: decoding the two review PNGs to RGBA gave
the same 921,600 pixel bytes and zero changed pixels. The PNG container embeds
the wall-clock `tEXtDate` and measured `tEXtRenderTime` chunks, so the raw
file SHA changes every run. The asserted evidence hash therefore cannot serve
as a pinned/reproducible media identity, and the committed repository contains
the hash record but not the corresponding render file for inspection.

This blocks release-level acceptance of the current media-evidence claim. Fix
by making the render artifact byte-stable before hashing (for example,
normalizing/removing volatile PNG metadata) or by declaring and recording a
canonical decoded-pixel/content hash alongside non-authoritative container
metadata. Then commit the actual pinned media/evidence record and add a
two-render equality test for the chosen identity.

## Follow-up boundary

No P2 was opened. A multi-frame/video comparison and browsable editorial page
are documented deferred scope, not a defect in this first technical slice; a
future release must not describe a single fixed frame as locomotion approval.

## Round-2 narrow re-pin — `8f9fc4538454492d695059172b96e8bd6e192eb6`

**P0: 0. P1: 0. P2: 0. PASS.** The sole prior P1 is closed.

I reproduced two independent build-and-render runs under one new external
temporary work root. Both generated candidate render files were byte-identical
to each other and to the now-committed
`reports/PROCEDURAL-ENGINE-001/media/v8-2-fixed-camera-canonical.png`:

- canonical PNG file SHA-256:
  `0b1494dd526f4eeb8312fa28ab61310163f9a508f229c26e98c8db8a479b9202`;
- decoded-pixel SHA-256:
  `5ca028e49545863349b16961b53bf18ca11bfcaa1d34fc4d1a19f185ad98e576`;
- 640x360 RGBA; canonicalization
  `decoded-scanlines-filter0-zlib9@1`.

The regenerated file contains only the canonical `IHDR`, `IDAT`, and `IEND`
PNG chunks: no date, render-duration, EXIF, or other volatile metadata remains.
The committed media hash, byte count (120,133), and pixel hash match
`evidence.json`. The reviewed image remains full-body and usable: head, body,
both feet, and tail are entirely in frame at the declared orthographic camera.

The fresh `compare` command generated `review/index.html` plus relative
`media/baseline.png` and `media/candidate.png`. Its fixed-camera evidence is
browsable at one responsive static page; both images use the same render set,
and the page visibly and structurally states: “Technical evidence only. This
page does not grant visual approval.” It does not claim that this static
comparison is a motion/visual approval.

No P0/P1 command-path regression was found in the narrow scope: the new build
continues to require approved artifact parity, writes its canonical render and
comparison evidence outside the repository, and the compare report preserves
the structural/accessor/contact gates while binding its media and HTML review
to the run. The retained 21-test suite reports no failures or skips; the
independent command reproduction above additionally verifies the specific
prior hash failure directly.
