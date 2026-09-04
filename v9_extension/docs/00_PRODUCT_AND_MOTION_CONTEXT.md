# Product and motion context for a new implementer

## 1. What Eonwild is

Eonwild is a browser-first, solo-complete ecological dinosaur survival game. The player is the animal: there are no humans, crafting trees, bases, conventional quest chains, or hero-shooter combat grammar. A life is a compressed meaningful season in which the player reads water, food, weather, calls, tracks, terrain, herds, predators, and body condition, then decides whether to migrate, hunt, avoid, investigate, feed, rest, recover, or accept risk.

The central player promise is embodiment. Before an objective appears, moving the animal must already be satisfying. Weight, acceleration, foot contact, turning, stopping, breathing, attention, tail response, terrain interaction, and injury are therefore product features—not secondary polish.

## 2. Why Tarbosaurus is the benchmark

Tarbosaurus is a demanding heavy-predatory-biped benchmark because the foreground animal exposes every weak system:

- a large head and neck affect balance and targeting;
- a long muscular tail must counter and damp body motion;
- most locomotor force and absorption comes through the hindlimbs;
- small forelimbs must remain animal-like and not become human running arms;
- turns and stops must respect high momentum and rotational inertia;
- a powerful bite must originate from support, legs, pelvis, and torso rather than a detached skull animation;
- feeding and drinking move the head far from the support region;
- growth and condition should visibly alter capability without producing a scaled-adult juvenile.

The benchmark is not permission to make every species behave like a tyrannosaur. Generic code is organized around biomechanical families and profiles; species remain distinct role packages.

## 3. Required motion character

At all times the Tarbosaurus should read as:

```text
heavy biped
horizontally balanced torso
pelvis carrying the central mass
large head/neck participating in balance
muscular tail coupled to the pelvis
hindlimbs generating and absorbing force
forelimbs held close with low-amplitude inertia
motion propagating through connected body chains
```

Substantial actions follow:

```text
anticipation
→ weight/support shift
→ force production
→ movement/contact
→ momentum continuation
→ force absorption
→ recovery
```

The forbidden alternative is an instantaneous jump from pose A to action pose B to recovery pose C.

## 4. Gameplay implications

The animation system supports several canonical product ideas:

- **Combat is physical and committed.** Large attacks have anticipation, contact windows, follow-through, vulnerability, and recovery. Instant cancellation would erase mass.
- **The predator decides whether to attack.** Acceleration, turning, stamina, target geometry, footing, injury, and recovery cost affect whether a hunt is viable.
- **Condition is communicated through the body.** Fatigue, pain, injury, alertness, and exertion alter posture, breathing, gait, acceleration, and decision envelopes rather than appearing only as bars.
- **Audio is ecological information.** Calls, footfalls, breathing, feeding, and vocal-body mechanics need standardized animation events.
- **Scientific honesty matters.** The game may interpret uncertain behavior for play, but tuned animation parameters must not be presented as exact paleobiology.
- **Browser viability matters.** Heavy solving and baking belong in the factory. Runtime applies bounded selection, interpolation, terrain/contact correction, and presentation layers.

## 5. What the factory must produce

For every accepted animation release, the factory should produce more than a GLB:

```text
resolved configuration and provenance
semantic rig-resolution report
animation specification and program version
baked root-motion and in-place views where applicable
phase/contact/event metadata
mechanical and constraint reports
fixed-camera review media
changed/unchanged channel report
release manifest and hashes
independent review record
```

An asset that only exists because an agent manually manipulated an editor is not considered scalable product content.

## 6. What not to optimize for

Do not trade the motion contract for:

- a larger clip count;
- flashy monster acting;
- high-frequency tail motion;
- permanent open mouths;
- fast input response created by cancelling committed actions;
- physics spectacle that removes authored animal intention;
- complexity that the player cannot perceive;
- exact numerical claims not supported by evidence.

The quality hierarchy is: convincing body and contact first, breadth later.

## 7. Canonical reference files

Read the copies under `references/game-design/`, especially:

- `GAME_OVERVIEW.md`
- `00-game-vision.md`
- `01-design-pillars-and-invariants.md`
- `02-player-loop-and-session-structure.md`
- `05-creatures-species-and-roles.md`
- `06-survival-senses-hunting-and-injury.md`
- `09-art-direction-and-visual-language.md`
- `10-audio-and-sensory-design.md`
