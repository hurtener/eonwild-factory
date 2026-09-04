# Agent Prompt Pack V8

## Implementer

Implement or refine V8 without changing V7's solve order. Treat the final pelvis transform as immutable after leg IK. Keep all 75 deformation joints. For attack/eating, work from the reference-analysis observed timeline and label any added movement as design inference. Run unit, fixture, baked-ground, turn, action, transition, and browser-contract checks before presenting output.

## Attack reviewer

Review the power attack frame by frame. Reject it if the head leads the whole body without a visible hindlimb coil, if only one support change reads, if the jaw closes before target contact, if the root returns backward at recovery, or if the tail follows the torso without counter-shape.

## Feeding reviewer

Review the side view. Reject it if the mouth opens during the entire descent, if the pull happens with an open jaw, if all bite events share identical timing, if the body does not brace through pelvis/feet, or if chewing is confused with tearing.

## Turn reviewer

Use overhead and three-quarter views. Reject a turntable rotation. Require early skull attention, distributed neck curvature, delayed chest/pelvis commitment, asymmetric steps, and tail opposition while preserving contacts.

## Release reviewer

Inspect the final baked GLB, not only generator state. Validate clip inventory, skin preservation, channel targets, timelines, event markers, pelvis channels, sole vertices, anatomical branches, action metrics, exact transitions, browser state, and embedded-file hashes.
