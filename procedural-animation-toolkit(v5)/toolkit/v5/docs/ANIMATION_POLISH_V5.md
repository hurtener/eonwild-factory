# Clip-Wide Motion Polish

V5 polishing is not “smooth everything.” It is a selective signal-processing stage.

## Quaternion method

1. Enforce quaternion sign continuity.
2. Express each sample as a relative rotation from the first sample.
3. Convert relative rotations to tangent-space rotation vectors.
4. Apply a zero-phase Savitzky–Golay filter.
5. Use cyclic padding for loops.
6. Reconstruct quaternions and restore exact endpoints.

## Protected content

The following remain untouched by generic filtering:

- root motion;
- thigh, shin, ankle, foot, and toe chains;
- jaw action tracks;
- any future contact or marker-critical channel.

## Added detail

V5 adds small causal layers to already-valid tracks: impact head/neck response, chest twist, delayed distal-tail movement, idle frequency separation, feeding response, bite recoil, and roar display motion. Amplitudes are deliberately small so they enrich rather than overwrite the primary action.
