# Learning Skill: Browser-Production Creature Animation V5

## Mission

Turn a fully rigged creature GLB into a browser-ready behavioral animation pack without reducing its deformation skeleton. Preserve anatomical constraints and ground contacts, create a separate living-neutral pose, build reusable actions, bake exact transition contracts, and validate the result numerically and perceptually.

## Core rule

Do not treat the bind pose as the neutral pose. Do not treat a transition clip as a suggestion that should receive a second crossfade. Do not smooth contact-critical tracks indiscriminately.

## Inputs

- Fully rigged GLB with skin weights and inverse-bind matrices.
- Semantic bone map.
- Creature/family profile.
- Optional locomotion reference footage.
- Existing validated animation pack when performing a contact-preserving refinement.

## Workflow

### 1. Inspect and preserve the complete rig

Count all skin joints, map semantic roles, discover hierarchy chains, and verify that generated outputs preserve joint order and inverse-bind matrices exactly.

### 2. Establish a living-neutral pose

For articulated jaws, select vertices strongly influenced by the mandible and upper skull. Divide the mouth along the forward axis into witness bins. Search jaw closure angles and choose the closest pose that retains a configured minimum gap in every usable bin. Store the calibrated angle and witness report per rig.

### 3. Protect constrained motion

Feet, toes, thigh/shin/ankle chains, root motion, and sharp action jaw beats are protected from generic filtering. Their curves are generated or preserved by the contact/anatomy solver.

### 4. Polish secondary tracks

Convert absolute quaternion tracks into tangent-space rotation vectors relative to the first sample. Apply a zero-phase Savitzky–Golay filter with cyclic padding for loops. Restore exact loop endpoints. Apply only to secondary torso, neck, head, arms, and tail tracks.

### 5. Add causal detail

Secondary movement should follow forces and behavior:

- impact response after foot contact;
- delayed distal tail response;
- chest/neck/head counter-motion;
- bite recoil after jaw contact;
- roar shake only during the display plateau;
- feeding head response tied to bite cycles;
- idle scans and weight shifts on non-identical frequencies.

### 6. Rebuild transitions

For each authored bridge, use source and target pose samples plus their neighboring samples. Build rotational `RotationSpline` curves and translation Hermite curves whose endpoint velocities match the source and target clips. Preserve exact endpoint values.

### 7. Enforce runtime semantics

- Direct arbitrary selection: one snapshot blend.
- Authored transition sequence: exact handoff, zero additional fade.
- Locomotion action request: wait for the declared planted-foot/source phase when possible.
- Preserve root continuity by offsetting the incoming root track to the currently displayed root.
- Keep UI state synchronized with playback, queue, active clip, and action status.

### 8. Validate

Required gates include neutral-mouth closure, action recovery closure, bite contact closure, transition endpoint equality, clip inventory, joint-order preservation, inverse-bind preservation, no invalid channels, browser player contract, and perceptual review from rendered tracks.

## Completion definition

A pack is complete only when the generated GLB, manifest, report, browser player, rendered fallback, tests, and reproduction scripts all refer to the same hashes and clip inventory.
