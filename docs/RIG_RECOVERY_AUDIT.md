# Adult recovery rig audit

This audit asks whether the compressed ankle and dead-weight foot visible in the
adult-walk recovery candidate are explained by a concrete defect in the bound
GLB rig. It covers runtime joint origins, hierarchy, inverse-bind matrices,
skin influences and evaluated mesh deformation. It does not validate fossil
anatomy, infer specimen-specific joint centers, approve the candidate, or prove
that the rig has no defect outside the measured scope.

The immutable admitted source is
`assets/sha256/044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6.glb`
with SHA-256
`044a8be907eb650fa71c613f19655eb10a0dd23c1d6bce86dfef93cd8d9575f6`.
The inspected candidate was
`adult-walk-v2-chain-meta45-pad50-toe35-clearance25`; its root-motion GLB has
SHA-256
`fb122e4aa51f56926adda52ea3750bb2944ee6276fe7daf4a9d2d93d1fb14473`
and its manifest has SHA-256
`250c54f49f5338bab29c4232b17833c874168394c18c61cd9ef3ba038bd8ae7f`.
The bound contact profile has SHA-256
`fef6279c1e7653ae6c7c485c3f934fd647410a726acb59393312b72af754a89f`.

## Corrected Blender diagnostics

The first neutral overlay was invalid for joint-placement interpretation.
Removing `armature.animation_data.action` after importing the animated GLB left
evaluated frame-zero pose transforms in Blender. The resulting yellow pose-bone
heads did not represent the GLB default node transforms. The corrected neutral
view imports a diagnostic copy with the `animations` JSON member removed before
import. Its nodes, skins, meshes, accessors, buffer views, buffers and BIN bytes
are unchanged. In that import, and at the two animated native samples, Blender
pose-bone heads agree with factory-evaluated GLB node origins within
`1.220077e-6 m`.

The first camera fit also cropped stance feet and toe tips. The corrected
renderer includes all toe-chain endpoints when deriving the shared camera and
uses `world_to_camera_view` to require every selected hip-to-toe influenced
vertex and joint endpoint to remain inside a four-percent image border. Blender
edit-bone tails and roll are excluded from the evidence; the yellow marks are
pose-bone heads only, while pink and blue identify the left and right runtime
GLB origins.

The rejected methods and corrections are recorded in
[method-history.json](../out/continuation-adult-rig-audit-001/method-history.json),
SHA-256
`fce8c55114103be0ea407b0aef3b19b90e86e91ebae464bf2074647175631cf6`.
The final six-view montage is
[full-leg-comparison.png](../out/continuation-adult-rig-audit-001/full-leg-comparison.png),
SHA-256
`ba3ab20b238f7ab729f3e39f530b917d0f69968dcb6a6ded20e51b7cd4d7d58e`.
The individual image identities are:

| Native state | Opaque SHA-256 | Overlay SHA-256 |
| --- | --- | --- |
| Neutral | `a275992ffa887855c0b995c51e82223c6b225406ac8be4af0f927ef6e56f3400` | `fadd4f2eb23bb1bbc2a90e9fcecdf756c6e944dd669f5b3a05439ef623ddcf7e` |
| Right recovery, `t = 0.8061486486 s` | `4e0abea650218b493cdf1c97debc8cf363773a7bba27b70f865221c72c4f4671` | `8b745b0192e7f3306a0b9b7d3dab91719b3918ea4cfbfca029ddfe386e52a8fd` |
| Left recovery, `t = 2.0361486486 s` | `ab80c30d623ca46d93a783625b1bf598a7291e44b3c4e111f095e6f2fe1b9af6` | `0208cf1356038d3afd0d23ceffb0d523819fbe8aecc55362c4eead372404b2a6` |

Its render receipt is
[joint-overlay-render-v2.json](../out/continuation-adult-rig-audit-001/joint-overlay-render-v2.json),
SHA-256
`746783ecd5c6a58bb82be4bb6dd11a3f37b1bc7de61b0ffdcc35fb2e5bf64f96`.
The
[artifact-integrity and camera-coverage receipt](../out/continuation-adult-rig-audit-001/verification.json)
has SHA-256
`7c989cdc73d8bfc8c320c93cf16c45e6f93f704c9345b5cf44afb6c1a463537d`.

## Structural and skin findings

The package preserves source topology, node names and parents, skin-joint
indices, POSITION, JOINTS, WEIGHTS and all 75 inverse-bind matrices exactly.
The only geometry transform difference is the declared active-scene-root scale
for the animal instance, `0.8595555358917822`, with zero measured residual.
The inverse-bind matrices are finite affine transforms: the maximum linear
condition number is `1.000000867`, the minimum absolute determinant is
`0.999999306`, and the affine last-row residual is zero.

Both semantic contact chains are direct parent chains, and each toe chain is
directly parented through its declared MTP/pad root. Left-versus-right bind-pose
segment lengths differ by at most `1.115139e-7 m`. Neutral skin samples around
both knee, intertarsal-ankle and MTP blend zones bracket their runtime pivot on
the declared forward, up and lateral axes. Bilateral leg weights occur in
proximal/body material, but neither leg's intertarsal nor MTP blend zone has any
opposite-leg influence.

At matched recovery phase `u = 0.546586`, both knees reach approximately
`65 degrees` interior. The left intertarsal ankle reaches `71.59 degrees` and
its MTP blend-radius retention is `0.90788`; the right reaches `91.25 degrees`
and `0.93828`. The larger visible left collapse therefore tracks a more folded
emitted pose and ordinary linear-blend skin compression. This is descriptive
correlation, not a biological range-of-motion claim. Axis bracketing likewise
does not prove that the modeled centers match a fossil specimen or living
tissue anatomy.

The reproducible integrity report is
[rig-integrity.json](../out/continuation-adult-rig-audit-001/rig-integrity.json),
SHA-256
`5ffe46a6e8413a38591fd0de17fccd890270d4e915087e771a82276d38aa48c5`.
The root host copied the evidence into
`out/continuation-adult-rig-audit-001`, inspected all six corrected views plus
the individual neutral and right-recovery overlays, and independently reran the
integrity script. The reproduced JSON was byte-identical at the same SHA-256.
The host review receipt has SHA-256
`fe29fbfc091d32dcb25ae666dc29b1ad26b865f3cda25d390336f131fdf248ec`.

## Decision boundary

No source rig or engine edit is justified by this audit alone. The next useful
comparison is an open-ankle motion candidate using the same source rig. If its
less-folded pose removes the abnormal skin collapse, the motion target explains
the present artifact. If comparable deformation persists at the more open
angles, joint-center placement, local axes and weights should be audited again
against that controlled result.

The user explicitly authorizes a Blender rig correction when evidence shows it
is needed. That authorization remains active. This audit records only that the
current measurements do not yet identify a concrete source defect; it does not
rule out a future versioned rig correction supported by stronger evidence.
