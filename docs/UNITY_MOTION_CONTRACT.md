# Unity motion consumer boundary

Decision: Python remains the offline motion factory. Unity is the intended
consumer. This document is an implementation contract, not a claim that Unity
runtime integration or mobile performance has been validated.

## Consolidated animal profile

See [animal embodiment v1](ANIMAL_EMBODIMENT_CONTRACT.md). The current mini-world consumer loads a versioned profile exported from `catalog/embodiment/`, replacing independently editable Unity arm/jaw settings and embedded clip intervals. Explicit local angular axes and Python reference vectors bind the secondary layer across adapters. This does not certify every Unity parity requirement below.

## Transport

Each candidate contains root-motion and in-place GLBs, an exact input lock,
recipe, motion plan, final receipts, and `runtime.json`. Blender can generate
an FBX transport candidate through tools/render_candidate.py. Generic rigs
are the intended Unity path; semantic family/rig adaptation remains ours.

Packages produced from a shared motion set also bind `motion-set.json`,
`motion-baseline.json`, and `motion-intent.json`. Connected clips must carry the
same baseline identity and snapshot hash even when their gait-derived effective
response values differ. Unity may select a motion by its resolved recipe id,
but it must not replace the package's animal, frame, contact, articulation,
neutral-pose, body-response, or solve-policy bindings per clip.

Keep the master source and full rig. Do not enforce an arbitrary bone cap or
reduce articulation before profiling. Export transport separately from the
source motion; bind its hash to the source package, renderer/exporter version
and import settings. Future animation-only clips should share one geometry
asset in the Unity project rather than duplicating textures per motion.

## Coordinate and time contract

Units are metres and seconds. Factory geometry explicitly declares forward
and up axes; do not assume every historical GLB has the same forward vector.
Factory data are right-handed. The engine adapter must define and test the
handedness conversion for position, orientation, angular quantities, contact
frames and event payloads. A visible model facing forward is insufficient.

Normalize imported actor scale to one or explicitly recalibrate distance,
velocity and contacts. Verify the root bone selection on the Generic avatar.
Sample factory poses at known seconds and compare Unity world-space landmarks
before and after compression. The current FBX exporter has not passed this test.

## One movement owner

The runtime motor resolves permitted world movement. Select either applied
root motion or a motor reconciled with nominal animation travel. Never apply
both displacements. Preserve speed/stride/cadence consistency and contact phase
when accelerating or blending. Physics and animation cannot independently
write the same root transform.

Use bounded terrain/contact correction for the active animal. Do not port the
entire offline numerical solver into every mobile actor. Near/mid/far fidelity
must be measured, with persistent semantic state maintained through changes.

## Interaction authority

`L_FOOT_CONTACT` and other track entries are animation cues. The world confirms
surface contact. Similarly, a bite/grip window permits an interaction but does
not assert damage, food acquisition or tear success. World state owns target
resistance, yield and release; animation responds. Do not bake unconditional
gameplay outcomes into timestamps.

Initial contacts are state, not landing impacts at spawn. Runtime must define
exactly-once event delivery across loop wrap, pause, seeking and interruption.
A transition carries support foot, contact anchors, phase, velocity, target and
grip state; an arbitrary crossfade does not guarantee those constraints.

### Dynamic movement state

Do not require a canonical beginning or ending stance. A displaced animal must
be able to change intent without first returning to an authored rest pose.
Carry its articulated local pose, world body center and root orientation,
heading, linear/angular velocity, and each foot's world pose, velocity and
observed support state. Units remain metres, seconds and explicitly declared
angular units (the current Unity review adapter uses degrees/second).

The outgoing movement relinquishes root ownership before the incoming adapter
adopts this state. Select a compatible support phase; preserve inherited
placements until release; reconcile reach at the body before solving the legs.
Future running and collision recovery consume the same handoff state, but each
behavior still owns contact choreography. Clip contact tracks are planned cues;
world-confirmed contacts and gameplay outcomes remain world authority.

Checkpoint 28 in principal Eonwild implements a grounded review adapter over
immutable approved clips, including actual-state adoption and decaying pose/
velocity offsets. Its runtime corrections require new review and measurements;
old source contact receipts do not certify the adjusted runtime output.
Airborne/hit-to-run transfer and full material contact/force parity remain open.

## First consumer acceptance scene

- Flat floor, slope, obstacle, food target and controllable resistance.
- Root motion and reconciled in-place modes tested independently.
- One complete start/walk/run/stop sequence, then feeding contact handoff.
- Export/import parity for root, hips, feet, mouth and tail landmarks.
- No double displacement, mirrored turns, foot skating or duplicated events.
- Native-speed multi-view recording from the actual Unity runtime.
- Target-device profiling before mobile budget claims.

Unity engine/package versions should be pinned in the consumer project when
that scene is created. No untested Unity project is included merely to make
this factory PR appear more complete.
