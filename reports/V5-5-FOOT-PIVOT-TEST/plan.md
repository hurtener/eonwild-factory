# V5.5 foot-pivot quick test

## Intent

Test the user's observation that the distal lower-leg/foot bend sits too high above the three toe branches. Move the `foot_l` and `foot_r` joint origins downward along the anatomical up axis while preserving the toe-branch origins, the undeformed mesh, every animation channel, and the frozen V5 tree.

This is an experimental V5.5 artifact, not a replacement of the accepted V5.5 release. The source V5.5 GLB remains unchanged until the user evaluates the 10-second walk film.

## Files in scope

- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/eonproc_v3/gltf_io.py`
- `procedural-animation-toolkit(v5.5)/toolkit/v5.5/scripts/adjust_v5_5_foot_pivots.py`
- `showcase/v5.5/render_v5_5_showcase.py`
- `reports/V5-5-FOOT-PIVOT-TEST/**`

## Adjustment

- Move both semantic foot pivots 75% of the vertical gap toward the centroid plane of their three toe roots.
- Do not shift either pivot fore/aft or laterally.
- Counter-adjust direct toe-child translations so their rest-world origins stay fixed.
- Recalculate only the moved foot joints' inverse-bind matrices so the undeformed skinned mesh remains unchanged.

## Acceptance checks

1. Both foot pivots move by equal vertical distance and finish above the toe-root plane.
2. Toe-root world origins remain fixed within `1e-6 m`.
3. Rest-pose skinned vertices remain fixed within `1e-6 m`.
4. Joint order, clip names, clip count, durations, and animation payload remain unchanged.
5. The frozen V5 tree remains byte-for-byte unchanged.
6. Blender imports the adjusted GLB and produces a seamless 10-second, 960x540, 24 fps H.264 walk film.
7. Representative frames receive a full-body and foot-region visual review.

## Assumptions

- The marked point corresponds to the semantic foot joint (`Bone_008` left, `Bone_012` right), which is the child endpoint of the ankle bone and parent of all three toe branches.
- This test evaluates pivot placement and resulting deformation only. It does not yet revise weights or gait curves.
