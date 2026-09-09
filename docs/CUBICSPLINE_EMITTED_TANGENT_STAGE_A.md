# CUBICSPLINE emitted-tangent Stage A

Stage A is a reader and validator only. It does not change a recipe, planned
or solved pose, key time, GLB emitter, or any acceptance threshold. Existing
LINEAR exports retain their serialized data and their adjacent-segment/shortest
SLERP evaluation.

The shared TRS reader follows [glTF 2.0 Appendix C.5](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#appendix-c-spline-interpolation): a CUBICSPLINE output contains three records per input key in `in-tangent`, `value`, `out-tangent` order, and its Hermite tangents are scaled by the key interval. Quaternion cubic results are normalized before use, as required by that appendix. Endpoint quaternion derivatives are therefore projected through that normalization before FK and LBS velocity propagation.

Contact-gauge sampling, exact endpoint/FK/LBS tangents, and local cyclic seam
validation share this reader. A malformed 3N output cannot be treated as N
ordinary keys. Unsupported interpolation, non-finite values or tangents,
non-increasing clocks, duplicate node/path channels, zero key quaternions, and
an evaluated zero cubic quaternion reject.

The normal factory per-channel rotation-rate gate still rejects CUBICSPLINE.
It measures only LINEAR shortest-SLERP key intervals and cannot bound a cubic
interval's angular extrema. Consequently no CUBICSPLINE package can receive a
complete technical pass until a later source/emitter and interval-rate/contact
stage supplies that authority. This stage does not invent zero endpoint
velocities or fit completed GLBs.

The integrated implementation, independent reviews and full-suite receipt are
preserved in
[V9-CUBICSPLINE-CONSUMER-STAGE-A-001](../reports/V9-CUBICSPLINE-CONSUMER-STAGE-A-001/README.md).
