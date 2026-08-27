# Agent Prompts V5

## Rebuild agent

Reproduce the V5 Tarbosaurus pack from the included source GLB, semantic map, and validated V4 pack. Do not modify source mesh data, skin joint order, inverse-bind matrices, textures, or semantic mapping. Run jaw calibration, refine only non-transition base clips, protect all contact-critical tracks, rebuild transitions, write a new GLB, and run the release validator. Stop on any failed gate.

## Perceptual reviewer

Review the rendered V5 validation at normal browser gameplay size and at close range. Inspect neutral mouth closure, tooth intersection, planted-foot continuity, transition boundaries, bite contact, roar recovery, eating-loop boundaries, tail settling, head stabilization, and UI state. Report timestamps and clip names for every defect.

## Browser reviewer

Verify direct clip selection, queued bite/roar/eat/alert behaviors, active buttons, play/pause/replay labels, timeline scrubbing, speed controls, cancel queue, root-motion camera following, contact-safe action scheduling, and exact authored handoffs. Confirm no extra fade occurs after a transition clip.
