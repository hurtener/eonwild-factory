# Art Direction and Visual Language

Status: **Canonical aesthetic direction**, benchmark-dependent quality targets.

## 1. Visual identity

Eonwild targets:

> **Naturalistic paleo-documentary realism, optimized aggressively underneath without advertising the compromise.**

The game should not look overtly cartoonish, toy-like, or generically “AI generated.” It also should not chase cinematic photorealism so rigidly that a solo project becomes unfinishable or unstable in a browser.

The intended result is a believable wildlife documentary brought into interactive 3D:

- credible anatomy;
- convincing mass;
- natural lighting;
- strong atmosphere;
- composed landscapes;
- restrained color;
- environmental storytelling;
- an animal that feels alive in motion.

## 2. Reference target interpretation

The floodplain herd image discussed during planning establishes a target class:

- warm low-angle directional sunlight;
- atmospheric haze;
- braided river and reflective shallow water;
- foreground vegetation framing;
- clear foreground, midground, and background depth;
- several scales of animals;
- distant herd silhouettes;
- natural earthy coloration;
- a view that implies a much larger continent.

The image itself should not be committed or redistributed unless its rights are known. The design language above can be recorded independently.

## 3. Aspirational browser-quality bands

These are planning estimates, not promises or release gates:

- carefully staged desktop-browser vista: approximately 88–93% of the reference class;
- normal high-quality desktop gameplay: approximately 80–88%;
- heavy herd/weather/vegetation scene: approximately 72–82%;
- WebGL2 fallback: approximately 65–78%;
- mobile is not a committed target.

The actual benchmark, not the percentage, decides feasibility.

## 4. Perceptual priority

Spend the visual budget in this order:

```text
hero animal
near environment and contact
mid-distance animals and landmarks
atmosphere and horizon
far environment
background population
```

A strong foreground creature can make an aggressively optimized world feel premium. A poor creature can make advanced lighting feel cheap.

## 5. Creature visual language

### Anatomy

- preserve accepted silhouette and proportion range;
- avoid movie-monster exaggeration unless documented as gameplay/art interpretation;
- make uncertain soft tissue and coloration choices coherent rather than falsely authoritative;
- use body condition, age, sex/display variation, and injury carefully when supported by scope.

### Materials

- skin, scales, keratin, feathers, eyes, mouth, and scars should have distinct physical response;
- avoid uniform plastic gloss;
- avoid noisy detail that only looks good in a still render;
- use 2K browser hero textures as the normal cap, with optional higher desktop packs later;
- variation should reuse masks and material systems rather than unique full texture sets for every pattern.

### Motion

The visual identity depends on:

- foot planting;
- weight transfer;
- breathing;
- head attention;
- tail stabilization;
- stride calibration;
- transition quality;
- terrain contact;
- species-specific posture.

Animation is art direction, not only technical implementation.

## 6. Landscape composition

The world factory should evaluate more than technical validity.

Composition dimensions:

- depth layers;
- horizon quality;
- landmark readability;
- route reveal and concealment;
- open-space ratio;
- vegetation clustering;
- silhouette diversity;
- water visibility;
- repetition;
- framing from player height;
- memorable approach and departure views.

Not every area needs key-art density. Contrast is valuable.

## 7. Vegetation

Use a coherent limited palette with strong ecological placement.

A visually rich area may be built from:

- several fern families;
- cycads or low broad-leaf forms;
- a small number of tree silhouettes;
- shrubs and ground cover;
- logs, branches, mud, rock, and debris.

Variation comes from:

- clustering;
- scale and rotation;
- moisture/canopy/slope rules;
- color variation within limits;
- life-stage/damage variants;
- foreground geometry and distant impostors.

Avoid:

- even spacing;
- identical rotations;
- biome “paint buckets” with hard boundaries;
- excessive alpha overdraw;
- one unique high-cost asset per plant.

## 8. Terrain and substrate

Terrain should communicate ecology through:

- mud and wetness;
- sand and river deposits;
- exposed roots;
- dry cracking;
- vegetation density;
- tracks and disturbance;
- slope and erosion;
- water history.

Use layered materials, macro variation, detail normals, wetness masks, and selective decals. The player should read where animals and water have been.

## 9. Water

Water needs to communicate:

- depth;
- flow;
- safety;
- drought/flood state;
- shoreline transition;
- contact with animals.

High-quality targets:

- Fresnel and environment reflection;
- animated normals/flow;
- depth coloration;
- shoreline foam or sediment;
- local ripples/splashes;
- restrained reflection cost.

Perfect ray-traced reflection is not required. Perceptual coherence is.

## 10. Lighting and atmosphere

Preferred scene grammar:

- one dominant directional sun;
- image-based or hemispheric ambient light;
- strong atmospheric perspective;
- fog used for depth, not to hide unfinished work;
- warm/cool balance between sun and shadow;
- controlled bloom/AO/color grading;
- limited dynamic lights.

Dense forest and indoor-like GI are not the main visual target. Broad natural environments allow convincing approximation.

## 11. Vista tiers

### Vista areas

Roughly 10–15% of the authored landscape may receive maximum composition investment:

- crossings;
- overlooks;
- refuges;
- herd concentrations;
- waterholes;
- storm fronts;
- major landmarks.

### Normal roaming areas

The majority should remain attractive, legible, and ecologically coherent without maximum effect density.

### Quiet wilderness

Simpler areas provide:

- scale;
- anticipation;
- rest;
- contrast;
- lower rendering cost.

Quiet must feel intentional, not empty or procedurally abandoned.

## 12. Quality profiles

### Low/WebGL2 fallback

- shorter foliage/shadow range;
- simplified water;
- lower actor representation;
- reduced post effects;
- same gameplay and world connectivity.

### Standard

- normal foliage density;
- good primary shadows;
- standard water;
- restrained AO/post effects;
- normal animal LOD ranges.

### High

- denser vegetation;
- longer shadow/LOD range;
- enhanced water and atmosphere;
- more visible herd members;
- stronger post-processing within frame budget.

### Cinematic/WebGPU enhancement

- optional compute/GPU-driven features;
- best vegetation and distant density;
- enhanced reflections or atmospheric effects;
- not required for core play.

## 13. AI-generated asset quality risks

Reject or rework:

- mushy anatomy;
- inconsistent material language;
- excessive random microdetail;
- texture seams;
- broken symmetry;
- melted mouth/eyes/toes;
- impossible feather/skin boundaries;
- unrelated styles between species;
- generated props with no ecological placement logic.

The factory should scale shared direction, not generate unrelated pretty objects.

## 14. Perceptual review

Automated video/image review should inspect:

- foot sliding;
- robotic turning;
- deformation;
- LOD popping;
- terrain seams;
- vegetation repetition;
- composition;
- visible streaming;
- material failure;
- regression against an approved baseline.

A model review supplements deterministic metrics and human art direction. It does not make final taste decisions alone.

## 15. Art-direction success

The visual language is working when:

- a gameplay screenshot resembles a natural-history scene rather than a game arena;
- creatures belong to the same world;
- movement improves, not destroys, the still-frame illusion;
- the player can read ecology through the landscape;
- vistas feel large despite aggressive LOD;
- the standard profile remains stable;
- players remember animals and places, not rendering tricks.
