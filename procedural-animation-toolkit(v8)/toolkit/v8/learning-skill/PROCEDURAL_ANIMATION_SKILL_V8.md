# Eonwild Procedural Animation Skill V8

## Learning objective

Build detailed heavy-animal actions from support, force, contact, resistance, and recovery—not from isolated bone rotations.

## Mental model

```text
attention chooses a target
support decides what can move
pelvis stores or redirects mass
legs create and receive force
spine transmits it
neck aims it
head/jaw contact it
tail opposes and settles it
```

## Exercise 1 — Read reference evidence

For every key frame, label only what is visible:

- support foot or uncertain support;
- pelvis height and direction;
- knee/ankle compression;
- head direction;
- jaw state;
- tail relation to body turn;
- camera cut or zoom.

Then create a separate design-inference column. Never silently promote camera-relative displacement into world-space motion.

## Exercise 2 — Build a power-attack phase graph

Create explicit phases:

1. target lock;
2. coil;
3. release;
4. first catch;
5. second drive/catch;
6. late gape;
7. snap contact;
8. clamp/tear;
9. recoil;
10. recovery.

For each phase, specify:

- root and pelvis transforms;
- left/right support loads;
- foot targets and lift;
- torso/neck/head contribution;
- jaw state;
- tail response;
- event marker.

## Exercise 3 — Make feeding non-periodic

Author three events with different timing, direction, and strength. Keep the complete loop exact, but do not make each bite a copy. Verify late gape, contact closure, braced pull, chew, swallow, and pause.

## Exercise 4 — Turn with attention first

Use a curved root path. Make the skull lead, neck curve, chest follow, pelvis commit, and tail oppose. Check the result overhead and three-quarter; side view alone hides the key relation.

## Exercise 5 — Validate the baked GLB

Reparse the exported GLB. Re-skin selected sole vertices. Measure actual world-space head/neck/chest/tail relationships. Verify transition endpoints and jaw state from the tracks that the browser will play.

## Completion criteria

The exercise passes only when:

- the real rich rig remains intact;
- contact/anatomical gates pass;
- attack/eating event timing is explicit;
- browser controls play the authored sequence without double blending;
- fixed-camera human review accepts mass, intent, and expression.
