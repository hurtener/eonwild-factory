# Eonwild Game Design Bible — Consolidated v1

> Generated from the canonical modular documents in `docs/game/`. Edit the modular files, not this consolidated copy.


---

# Eonwild — Quick Product Overview

Status: **Canonical handoff reference**

## The game

Eonwild is a browser-first, solo-complete ecological dinosaur survival game. Each life represents a compressed meaningful season in a fictional prehistoric continent populated by scientifically grounded—but explicitly game-interpreted—animals.

The player is the animal. There are no humans, crafting trees, bases, or conventional quest chains. The player reads water, food, weather, herds, predators, calls, tracks, terrain, and body condition, then chooses whether to roam, migrate, hunt, evade, cooperate, rest, or take a risk.

## The player promise

- The dinosaur feels alive to control.
- The world is continuous and roamable, not a corridor.
- Ecology creates pressure instead of arbitrary errands.
- Every species is a distinct role, not a power tier.
- Solo play is complete.
- A life resolves within a meaningful session rather than demanding hours of passive growth.
- Failure matters but still contributes to Lineage.
- Scientific uncertainty is shown honestly.

## Core loop

```text
Sense → Interpret → Choose → Move → Encounter → Recover → Learn → Continue
```

## Session direction

- Diagnostic proofs: 10–15 minutes.
- Quick Expedition: working target of 12–20 minutes.
- Full Season: working target of 30–50 minutes.

The life usually moves through orientation, preparation, environmental pressure, roaming/migration, crisis, and resolution. These are ecological phases inside one continuous world, not separate levels.

## World

- One contiguous coordinate space streamed in cells.
- Biomes are blends of temperature, moisture, elevation, canopy, water, substrate, exposure, and seasonal biomass.
- Multiple routes, loops, backtracking, landmarks, detours, and quiet wilderness.
- Migration is a changing attractor driven by suitability—not a compulsory spline.
- Near animals use full simulation; mid-distance populations use group proxies; far populations remain ecological records.

## Species

Species are composed from taxonomy, morphology, biomechanical family, locomotion, ecology, capabilities, presentation, and runtime state.

Early role direction:

1. Fast non-apex herbivore/omnivore — awareness, herd, route, escape.
2. Small/medium predator — tracking, target selection, commitment, injury.
3. Defensive quadruped — position, brace, armor, route timing.
4. Large apex predator later — power balanced by food pressure, visibility, turning, and injury cost.

## Survival

Needs create choices, not chores. Feeding, hydration, stamina, temperature, rest, and injury affect routes and commitment. Combat is simple, physical, positional, and dangerous. Herbivore lives must remain interesting without attacking anything.

## Lineage

Lineage is persistent progression earned from meaningful animal behavior: migration, escape, hunting, warning, group behavior, discovery, injury recovery, environmental survival, and species mastery.

It unlocks species, knowledge, natural variants, challenges, and mastery—not universal permanent combat power. Death keeps completed event progress but loses survival/completion bonuses.

## Multiplayer

Solo is the primary contract. Private two-player same-species or compatible-role co-op is the first later target, potentially expanding to four. Browser multiplayer is expected to be host-authoritative with minimal signaling/relay infrastructure. Public PvPvE, dedicated servers, and larger sessions are future options, not launch assumptions.

## Art and sound

Visual direction: naturalistic paleo-documentary realism. Preserve the hero animal, movement, contact, atmosphere, and composition; aggressively optimize distant detail.

Audio direction: plausible bioacoustic calls, body/footstep presence, and environmental sound that communicates ecology. Avoid generic monster roars and constant orchestral scoring.

## Science and fiction

The complete assemblage is fictional and may combine species from different eras and regions. The field guide records the real period, geography, evidence, uncertainty, and the game’s chosen interpretation. Fantastic Dinosaurs is inspiration/discovery only; protected content is not a production input.

## Platform and business direction

- Desktop browser first; WebGL2 baseline and WebGPU enhancements.
- PWA and Wails/Steam desktop later.
- Mobile is not committed.
- Working commercial direction: a meaningful free browser experience plus a premium ad-free desktop edition and tasteful cosmetic/ecosystem expansions.
- No paid power, Lineage sales, loot boxes, or paid revival.

## Current development principle

Build the factory and the smallest integrated playable life before expanding the roster or continent. Progress is measured by reproducible, benchmarked, independently reviewed player experience—not asset count.


---

# Eonwild Game Design Bible

Status: **Canonical index**  
Audience: product, gameplay, world, ecology, creature, art, audio, UI, research, commercial, QA, and autonomous agents.

## 1. Purpose

The repository already contains detailed contracts for the asset factory, streaming world, biomechanical families, scientific provenance, browser runtime, quality gates, and agent orchestration. Those documents are necessary, but they mostly describe the production machine and the current milestone.

This directory owns the durable answer to:

> **What is Eonwild, what should it feel like, and what must remain true as implementation and sprint scope change?**

Handoff files should link to these documents. They should not become the only surviving source of game intent.

## 2. Product definition in one paragraph

**Eonwild** is a browser-first, solo-complete ecological dinosaur survival game in which each playable life represents a compressed, meaningful season in a dynamic prehistoric world. The player inhabits a scientifically grounded—but explicitly game-interpreted—animal, reads changes in water, food, weather, herds, predators, and terrain, then chooses whether to roam, migrate, hunt, evade, cooperate, rest, or take a risk. Natural behavior and memorable life events produce **Lineage**, unlocking additional species as distinct ecological roles rather than power tiers. Multiplayer may later amplify stories in small private groups, but the ecosystem and complete fantasy must work alone.

## 3. Canonical reading order

1. `GAME_OVERVIEW.md` for handoffs and orientation
2. `00-game-vision.md`
3. `01-design-pillars-and-invariants.md`
4. `02-player-loop-and-session-structure.md`
5. The system document relevant to the task
6. `16-open-decisions-risks-and-experiments.md`
7. Existing technical RFCs and quality gates
8. Current sprint plan and handoff

## 4. Ownership and precedence

### Product-intent ownership

The following are canonical for product intent:

- `00-game-vision.md`
- `01-design-pillars-and-invariants.md`
- accepted game-design decisions recorded through the change process

### Technical ownership

Existing JSON Schemas, machine-readable configuration, accepted ADRs, and RFCs remain authoritative for implemented contracts.

When an executable contract cannot satisfy a canonical product invariant, the agent must raise a conflict. It may not silently change the product or weaken a product invariant to preserve the current implementation.

### Milestone ownership

Sprint plans, task briefs, and handoffs may:

- select a smaller slice;
- defer systems;
- use placeholders;
- establish temporary benchmark values.

They may not permanently redefine Eonwild without a reviewed game-design change.

## 5. Document map

| Document | Owns |
|---|---|
| `00-game-vision` | Identity, audience, fantasy, emotional promise, positioning |
| `01-design-pillars` | Non-negotiable experience principles and anti-goals |
| `02-player-loop` | Moment-to-moment loop, life structure, failure, replay |
| `03-world` | Continent, roaming, map topology, environmental characters |
| `04-ecology` | Resource suitability, migration, AI fidelity, ecological events |
| `05-creatures` | Species roles, body families, roster strategy, ontogeny |
| `06-survival` | Needs, senses, hunting, combat, injury, herbivore depth |
| `07-lineage` | Meta-progression, unlocks, mastery, anti-grind rules |
| `08-modes` | Solo, private multiplayer, social interaction, future public play |
| `09-art-direction` | Naturalistic documentary visual language and quality hierarchy |
| `10-audio` | Bioacoustics, environmental sound, sensory communication |
| `11-ui-ux` | HUD, onboarding, field guide, controls, accessibility |
| `12-science-setting` | Fictional ecosystem, scientific honesty, world fiction |
| `13-platform-business` | Browser/desktop strategy and monetization principles |
| `14-roadmap` | Product-stage scope and content growth |
| `15-player-stories` | Concrete examples showing the intended game |
| `16-open-decisions` | Unresolved choices, risks, and experiments |
| `17-glossary` | Shared vocabulary |
| `18-review-checklist` | Gate for new feature proposals and sprint changes |

## 6. Change policy

A material game-design change requires:

1. A proposal using `templates/GAME_DESIGN_CHANGE_PROPOSAL.md`.
2. The player problem or evidence motivating it.
3. Conflicts with canonical pillars.
4. Alternatives considered.
5. A validation plan.
6. Human product-owner acceptance.

Autonomous agents may propose a change. They may not declare it canonical.


---

# Eonwild — Game Vision

Status: **Canonical**, except fields explicitly labeled working direction.

## 1. Name and working expression

**Title:** Eonwild  
**Working tagline:** *Live the age. Follow the wild.*

The name combines deep time with living wilderness. It does not lock the game to one geological period, one continent, or one famous species. It leaves room for future ecosystems and prehistoric animals while preserving the core identity: inhabiting a wild animal in a world shaped by ecology rather than human objectives.

## 2. One-sentence pitch

> Live one dangerous season as a dinosaur in a changing prehistoric ecosystem, reading the world to migrate, feed, hunt, evade, cooperate, and leave a Lineage.

## 3. Expanded pitch

Eonwild is a natural-history survival experience built around **animal embodiment, ecological causality, and short meaningful lives**. A player does not arrive as a human character, craft tools, build a base, or clear a conventional quest log. The player is the animal.

Water recedes. Vegetation quality changes. Herd calls move across the valley. A storm makes one crossing dangerous. Predators follow concentrations of prey. Injury can turn a direct route into a fatal mistake. The player senses these changes, interprets them, and decides what kind of life to live.

Each species changes the game. A small cursorial herbivore survives through attention, endurance, cover, and route knowledge. A small predator survives through tracking, timing, target selection, and knowing when to abandon a hunt. A heavily armored herbivore survives through position, patience, and defensive commitment. A large predator gains force and reach but pays for it with enormous food pressure, visibility, slow recovery, and costly injury.

A life ends in survival, death, or a completed seasonal objective. Either way, meaningful animal behavior contributes to **Lineage**, which opens new ecological roles and knowledge rather than universal permanent power.

## 4. Genre identity

Internal genre description:

> **Solo-first ecological dinosaur survival roguelite with optional small-group multiplayer.**

Alternative public phrasing may avoid the word “roguelite” when it creates the wrong expectation of rooms, loot, or combat builds. The structural meaning is:

- repeatable lives;
- changing seeded conditions;
- meaningful failure;
- partial persistent progression;
- species unlocks and mastery;
- replay through systems rather than authored quest repetition.

## 5. Player fantasy

The player should feel:

- **embodied** — “This animal has weight, momentum, senses, limits, and a body.”
- **observant** — “The world is telling me what is happening.”
- **free** — “I can choose a route, detour, wait, explore, or ignore the obvious pressure.”
- **vulnerable** — “A bad decision or injury matters.”
- **capable** — “Learning the species and ecosystem makes me better, not merely stronger stats.”
- **connected** — “Other animals and the environment are part of one causal system.”
- **awe-struck** — “The landscape and animals feel larger than me and older than civilization.”
- **story-bearing** — “I can retell what happened during this life.”

## 6. Target audience

Primary audiences:

- Players attracted to dinosaur survival but discouraged by multi-hour growth loss, dependence on populated servers, or excessive PvP grind.
- Animal-simulation players who value behavior, ecology, family/group dynamics, and naturalistic environments.
- Players who enjoy systemic survival, exploration, and roguelite replay without crafting-heavy complexity.
- Dinosaur and natural-history enthusiasts who value credible reconstruction and honest uncertainty.
- Browser and indie players willing to trade the absolute rendering ceiling for immediate access and frequent iteration.

Eonwild is not designed primarily for:

- ranked competitive PvP players;
- base-building and crafting progression players;
- players seeking a combo-action dinosaur fighting game;
- players who require a human-led narrative campaign;
- players who want every species to be balanced around equal combat effectiveness.

## 7. Emotional arc of a life

A strong life tends to move through:

1. **Orientation** — Where am I? What condition am I in? What is nearby?
2. **Belonging or isolation** — Is there a herd, pack, territory, or safe route?
3. **Pressure** — Hunger, water, temperature, weather, predators, or competition changes the situation.
4. **Choice** — Follow the obvious movement, take an alternate route, wait, explore, hunt, or withdraw.
5. **Crisis** — A crossing, pursuit, injury, storm, failed hunt, separation, or resource collapse.
6. **Aftermath** — Recover, reach refuge, exploit the event, or die.
7. **Legacy** — Review the path, behavior, discoveries, and earned Lineage.

Not every life must contain every beat. The ecology should create variation rather than force a fixed screenplay.

## 8. Scientific and fictional framing

The animals should be anatomically and behaviorally grounded in current evidence, while uncertainty remains visible. The complete game may combine species from different periods and regions inside a fictional paleo-continent or simulation context. It must state this honestly rather than implying that every animal coexisted historically.

The game prioritizes:

- plausible animals;
- evidence-linked claims;
- transparent gameplay interpretation;
- coherent ecosystem design;
- no false claim of exact prehistoric certainty.

## 9. Product promise

Eonwild succeeds when players remember lives, not task lists.

The strongest player response is not:

> “I completed three objectives.”

It is:

> “The water was disappearing, I left the herd to take the ridge, heard predators below, found another crossing, got injured, and barely reached the refuge.”

## 10. Working market position

Internal shorthand:

> The animal-life credibility of a strong wildlife simulator, the danger and presence of dinosaur survival, and the replay structure of a roguelite—without becoming an MMO or crafting game.

This is positioning language, not a commitment to copy another game’s systems.

## 11. What Eonwild is not

Eonwild is not:

- a persistent dinosaur MMO;
- a battle royale;
- a survival-crafting game;
- a park builder;
- a corridor runner;
- a collection of disconnected technology demos;
- a photorealism-at-any-cost project;
- a scientific encyclopedia with shallow gameplay;
- an arcade game wearing realistic dinosaur models;
- a game that requires populated servers to feel alive;
- a live service that depends on daily chores.

## 12. Product success definition

A validated product should demonstrate:

- moving as the animal is enjoyable before an objective appears;
- players take different routes and can explain why;
- ecological changes are understood from the world, not only UI;
- herbivore and predator lives create distinct decisions;
- solo play feels complete;
- deaths feel consequential but do not erase an entire evening;
- players voluntarily begin another life;
- players retell emergent events;
- the browser build looks and feels premium enough to support a broader desktop product.


---

# Design Pillars and Product Invariants

Status: **Canonical**

These principles survive changes in technology, milestone scope, species roster, monetization, and map size. A feature that conflicts with them requires an explicit product decision.

## 1. Embodiment before breadth

The first impression is the body:

- weight;
- acceleration;
- foot contact;
- turning;
- stopping;
- breathing;
- head attention;
- tail response;
- interaction with terrain and water.

One convincing animal is more valuable than ten weak ones. New content may not be used to avoid fixing locomotion, camera, deformation, or control.

### Implication

The order of quality investment is:

1. movement and input feel;
2. stable frame time;
3. world coherence and roaming freedom;
4. creature silhouette and deformation;
5. audio and atmosphere;
6. surface richness;
7. distant spectacle.

## 2. Ecology generates pressure

The world should create reasons to move and act through:

- water;
- food quality and biomass;
- temperature;
- weather;
- shelter;
- visibility;
- predators;
- competition;
- herd movement;
- injury and condition.

The game should not rely on arbitrary fetch quests to make the player travel.

### Implication

A conventional marker may support accessibility or communicate already-known information. It should not replace ecological causality.

## 3. Freedom to roam

The map is a place, not a sequence.

The player can:

- leave the efficient migration route;
- backtrack;
- become temporarily lost;
- choose longer safer paths;
- take exposed direct paths;
- investigate landmarks;
- wait for conditions to change;
- ignore the strongest attractor and accept consequences.

Streaming cells, ecological regions, and session phases may not become visible corridor architecture.

## 4. Species are different games, not power tiers

A new species earns its place by changing decisions, information, movement, risks, and ecological relationships.

Bigger is not simply better. Advantages create costs:

- greater mass can enable force but raises food pressure;
- greater speed can improve escape but reduce stability or endurance;
- armor can improve defense but constrain movement and route choice;
- group living can improve awareness but increase competition and visibility.

No universal progression should make every unlocked animal strictly stronger.

## 5. Solo is complete

The ecosystem must function when only one human is playing.

Multiplayer may add:

- cooperation;
- betrayal;
- group vigilance;
- communication;
- emergent mistakes;
- player-controlled predators or prey later.

It may not be the missing content layer that makes the world alive.

## 6. Lives are meaningful, not exhausting

Failure matters, but the game should respect an evening.

The design rejects multi-hour passive growth followed by catastrophic loss as the default structure. A life should reach a meaningful resolution within a reasonable session, with partial progress even after death.

## 7. Learn the world, not the grind

Player mastery comes from:

- reading cues;
- understanding routes;
- knowing species limits;
- judging risk;
- tracking resources and animals;
- learning when to commit or withdraw.

It should not primarily come from repeating a safe action until a meter or currency fills.

## 8. Scientific honesty

The game is allowed to interpret uncertainty for play. It is not allowed to hide that interpretation.

Every meaningful reconstruction or behavior should distinguish:

- supported evidence;
- plausible inference;
- disputed interpretation;
- speculation;
- gameplay-only choice.

Scientific uncertainty is part of the product’s credibility, not an inconvenience to remove.

## 9. Presentation serves perception

High visual quality is important, but the player notices some things more than others.

Never compromise lightly on:

- the foreground animal;
- locomotion;
- contact;
- sound;
- readable ecology;
- scene composition.

Aggressively optimize:

- distant geometry;
- invisible simulation;
- nonessential reflections;
- off-screen populations;
- redundant materials;
- effects that do not affect the fantasy.

## 10. Systemic stories over scripted errands

The intended narrative unit is a life story created by systems. Authored events may shape conditions, but the player should retain agency.

Good authored content:

- drought timing;
- flood conditions;
- herd movement;
- fire front;
- temporary resource bloom;
- predator concentration;
- unusual weather;
- a dangerous crossing.

Weak authored content:

- “eat ten plants”;
- “visit marker A, then B”;
- “kill five enemies”;
- arbitrary daily chores;
- dialogue exposition explaining what the world could show.

## 11. No hidden production debt

This is a product invariant because unreliable automation eventually damages the game.

Accepted content must be:

- reproducible;
- provenance-complete;
- validated;
- benchmarked;
- independently reviewed where perception matters.

An asset or world cell that exists only because one agent manipulated an editor manually is not scalable product content.

## 12. Anti-goals

Features should be rejected or heavily challenged when they introduce:

- crafting inventories;
- base building;
- human weapons or factions;
- universal stat trees;
- paid power;
- loot boxes;
- forced daily login;
- quest-marker dependence;
- public competitive ranking before authority and balance exist;
- enormous maps filled with low-value emptiness;
- species that differ mostly by model and damage number;
- simulation complexity players cannot perceive;
- visual effects that destroy frame-time stability.

## 13. Feature litmus test

A proposed feature is probably aligned when it strengthens at least two of the following without damaging another:

- embodiment;
- ecological causality;
- roaming choice;
- species differentiation;
- emergent stories;
- replayability;
- solo completeness;
- scientific credibility;
- browser viability.


---

# Player Loop and Session Structure

Status: **Canonical loop**, with session durations marked as working direction.

## 1. The moment-to-moment loop

```text
Sense → Interpret → Choose → Move → Encounter → Recover → Learn → Continue
```

### Sense

The player receives information through:

- sight and movement;
- calls and ambient sound;
- tracks, scent, disturbed vegetation, carcasses, mud, and water;
- temperature, wind, rain, visibility, and shelter;
- body condition and social signals.

### Interpret

The player asks:

- Is the local food or water still viable?
- Is that call a herd, rival, predator, or distress signal?
- Is the short route now dangerous?
- Am I strong enough to commit to this hunt or crossing?
- Is the group moving for a reason?
- Can I recover here, or will waiting make things worse?

### Choose

Meaningful choices should include:

- follow, wait, detour, scout, hide, rest, hunt, scavenge, defend, flee, or ignore;
- move with a group or leave it;
- trade speed for cover;
- trade safety for time;
- abandon an encounter before injury becomes catastrophic.

### Move

Movement is not downtime. Terrain, visibility, stamina, scent, water, cover, and other animals make route execution part of play.

### Encounter

An encounter can be:

- another animal;
- a herd concentration;
- a crossing;
- a predator pursuit;
- a failed hunt;
- weather;
- a newly dry water source;
- fire or flood;
- injury;
- a carcass or feeding opportunity;
- a social interaction.

### Recover

After pressure, the player must decide where and how to:

- rest;
- drink;
- feed;
- hide;
- regroup;
- treat time and safety as resources;
- change plans because of injury or exhaustion.

### Learn

The player gains:

- route knowledge;
- species mastery;
- ecological understanding;
- field-guide knowledge;
- Lineage from meaningful events;
- a story to carry into the next life.

## 2. Life structure

A life represents a compressed meaningful period—usually a defining season—not necessarily a literal simulation from hatching to old age.

A normal full life tends to contain:

1. **Entry and orientation**
2. **Preparation and local learning**
3. **Environmental or ecological shift**
4. **Roaming, migration, or territorial response**
5. **Crisis or opportunity**
6. **Resolution and Lineage review**

These are ecological phases, not separate linear levels. The player remains in one continuous world and can revisit prior areas when conditions allow.

## 3. Working session formats

### Diagnostic proof

**10–15 minutes**

Used during early milestones to test one pressure, several routes, embodiment, streaming, and telemetry. It is not the final product duration.

### Quick Expedition — working direction

**12–20 minutes**

A browser/portal-friendly life with compressed pressure and a clear resolution. It should still permit route choice and emergent events.

Use cases:

- first-time play;
- portal distribution;
- shorter daily session;
- low-commitment species trial;
- seeded challenge.

### Full Season — working direction

**30–50 minutes**

The primary direct-browser or premium-desktop experience. It gives time for:

- orientation;
- detours;
- multiple encounters;
- changing conditions;
- injury and recovery;
- a stronger sense of travel and consequence.

### Extended Ecology — future option

Variable duration, potentially using checkpoints, community servers, or more persistent conditions. This is not required for the initial product and must not turn the core into an MMO dependency.

## 4. Starting life stage

Open decision: exact growth implementation.

Current direction:

- early versions may begin as a capable juvenile, subadult, or young adult to avoid long passive growth;
- growth, if present, is compressed and changes decisions rather than merely increasing size over time;
- juvenile vulnerability may become a species or mode-specific challenge;
- the default experience should reach meaningful agency quickly.

The game should not require several hours of passive survival before the species becomes interesting.

## 5. Core verbs

Shared verbs:

- move at species-appropriate gaits;
- turn, slow, stop, and rest;
- look, listen, smell, or invoke a restrained instinct sense;
- feed and drink;
- call or signal;
- use terrain, water, vegetation, and shelter;
- interact socially;
- flee, defend, stalk, or attack when the species permits.

Species-specific verbs should remain few and meaningful. A typical creature might have:

- one primary interaction or attack;
- one secondary defensive or positional action;
- one context action;
- one movement specialization;
- a call vocabulary.

Depth should come from timing, position, information, condition, and ecology—not large button-combo lists.

## 6. Resolution states

A life can resolve through:

- surviving the seasonal pressure;
- reaching a viable refuge or range;
- completing a species-specific ecological objective;
- establishing a successful hunt or feeding season;
- rejoining or protecting a group;
- dying;
- voluntarily ending at a valid rest/checkpoint state in supported modes.

Survival creates a meaningful bonus, but death still awards completed Lineage events.

## 7. Death philosophy

Death should create tension and stories without invalidating an evening.

On death:

- the current individual is lost;
- completed events and discoveries remain eligible for Lineage;
- survival/completion bonuses are lost;
- the player receives a clear account of what happened;
- a new run can begin quickly.

Avoid:

- opaque instant deaths with no readable cause;
- losing many hours of passive growth as the default;
- paid revival;
- advertising used to reverse death;
- corpse-running or inventory recovery loops.

## 8. Replay structure

A repeated life changes through:

- world seed;
- weather timing;
- water and food suitability;
- herd origin and destination;
- predator pressure;
- route availability;
- flood, drought, cold, fire, or storm events;
- starting location and condition;
- species role;
- player knowledge.

Replay should not depend on randomizing everything. The world needs persistent geographic identity so knowledge and attachment matter.

## 9. Example full-season rhythm

| Phase | Approx. time | Typical decisions |
|---|---:|---|
| Orientation | 0–7 min | locate water/food, read calls, assess condition |
| Preparation | 7–15 min | feed, choose group/territory, scout routes |
| Pressure emerges | 15–22 min | interpret drying, weather, predator, or herd shift |
| Roam/migrate/hunt | 22–38 min | route choice, encounters, energy management |
| Crisis | 30–45 min | crossing, pursuit, storm, injury, failed hunt |
| Resolution | final minutes | refuge, recovery, death, summary, Lineage |

The timing is a starting hypothesis, not a scripted timeline.

## 10. Session-quality questions

A life is working when:

- meaningful input begins quickly;
- the player understands at least one cue without a tutorial wall;
- travel includes decisions rather than dead time;
- an herbivore can have an engaging life without combat;
- a predator spends meaningful time deciding not to attack;
- death has a readable causal chain;
- the player is curious about another route or species;
- the summary describes a story rather than a checklist.


---

# World, Continent, and Roaming

Status: **Canonical world principles**, working direction for exact content scale.

## 1. World identity

Eonwild takes place in a **fictional paleo-continent** built to support credible animals, multiple climatic characters, seasonal movement, and future expansion.

The continent is not a historical claim that every included species coexisted. It is a coherent game ecosystem whose animals are individually grounded in evidence and whose real age/geography remain available through the field guide.

## 2. One world, not a chain of zones

The world uses one continuous coordinate space. It may be partitioned for:

- streaming;
- rendering;
- navigation;
- authoring;
- simulation fidelity;
- download packaging.

Those partitions must not become visible level structure.

The player should be able to:

- wander laterally;
- return by a different route;
- backtrack;
- ignore migration pressure;
- investigate quiet valleys and side areas;
- temporarily become lost;
- find alternative water or shelter;
- observe a landmark from several approaches.

## 3. Biomes are environmental blends

The world should not be authored as a fixed sequence such as:

```text
forest → corridor → floodplain → basin → refuge
```

Those environmental characters may exist, but their shapes emerge from overlapping fields:

- elevation;
- moisture;
- temperature;
- canopy;
- substrate;
- water proximity and depth;
- exposure;
- shelter;
- seasonal biomass;
- fire/flood history;
- traversal cost.

This permits:

- forest descending into sheltered valleys;
- dry rain-shadow areas beside elevated terrain;
- riparian corridors crossing several regions;
- wetlands opening into exposed floodplains;
- mixed ecotones rather than hard biome borders.

## 4. Macro environmental characters

Long-term world design may include combinations of:

### Upland forest and ridge country

- cooler temperatures;
- cover and shelter;
- limited sight lines;
- elevated observation routes;
- seasonal food decline;
- narrow but natural passes.

### Floodplain and braided river

- high biomass;
- changing channels;
- exposed mud and sandbars;
- herd concentration;
- dangerous crossings;
- flood and drought variability.

### Fern woodland and wetlands

- dense cover;
- high ambient life;
- reduced visibility;
- soft ground and water edges;
- predator ambush opportunities.

### Dry basin and open country

- scarce cover;
- long sight lines;
- sparse water;
- mineral or feeding sites;
- heat and travel pressure.

### Seasonal refuges

- temporary suitability rather than permanent safe zones;
- water or food concentration;
- high competition;
- predator pressure;
- social gathering.

These are a palette, not a mandatory traversal order.

## 5. Roaming topology

The world should offer several route types:

- **direct and exposed** — shorter, visible, potentially dangerous;
- **covered** — longer, lower visibility, constrained movement;
- **elevated** — better information, higher traversal or weather cost;
- **water-following** — reliable orientation, greater predator/herd activity;
- **exploratory** — uncertain reward, landmark or route discovery;
- **seasonal** — available only under certain water, flood, or temperature states.

Major areas should connect through loops. Natural chokepoints are valuable when they are a minority of travel and arise from geography rather than loading needs.

## 6. Scale and density

Logical world size and active cost are separate.

The existing technical direction uses a 12 × 12 demonstration grid of 256-metre cells, producing a logical bounding space of roughly 3.07 × 3.07 km. That is a benchmark envelope, not a permanent limit or a promise that every cell is equally authored.

The product should prioritize:

- enough area for route choice and temporary disorientation;
- density of meaningful signs and ecological information;
- memorable landmarks;
- quiet wilderness that feels intentional;
- high-value vistas and event locations;
- outward expansion without coordinate or save rewrites.

Do not increase square kilometres merely to market a large number.

## 7. Content-density tiers

### Tier A — memorable vistas and ecological stages

Examples:

- herd river crossing;
- valley overlook;
- drying waterhole;
- storm front over open basin;
- refuge seen from a ridge;
- predator concentration around a bottleneck.

These receive the highest composition and rendering investment.

### Tier B — normal roaming landscape

The majority of play:

- route choices;
- feeding and cover;
- tracks and signs;
- modest encounters;
- navigation by terrain and sound.

### Tier C — quiet transition and wilderness

Lower density, but still intentional:

- supports anticipation;
- creates contrast;
- allows recovery;
- communicates scale;
- avoids constant theme-park stimulation.

## 8. Landmarks and orientation

Players should navigate through:

- river systems;
- ridges;
- mountain silhouettes;
- distinctive tree groups;
- rock formations;
- wetlands;
- mineral deposits;
- distant herd movement;
- sky/weather direction;
- audio landmarks.

A restrained map or memory aid may exist, but the world should remain learnable from observation.

## 9. Dynamic geography

Environmental state may temporarily change traversal:

- flood removes or creates crossings;
- drought exposes mudflats and channels;
- fire or smoke makes an area dangerous;
- storms reduce visibility;
- cold or heat changes shelter value;
- vegetation density changes feeding routes;
- carcasses and herds create temporary hotspots.

Dynamic events may close a path for ecological reasons. They must not become permanent excuses for a linear structure.

## 10. Distant world illusion

The world can feel much larger than the fully active area through:

- horizon meshes;
- distant mountains;
- atmospheric perspective;
- off-map herd silhouettes;
- dust;
- weather fronts;
- distant calls;
- rivers continuing beyond current authored terrain;
- far ecology records.

The renderer should spend detail where the player can perceive it.

## 11. World expansion model

The continent expands through:

- new adjacent cells;
- new environmental-field presets;
- new shared vegetation and terrain packs;
- new water systems;
- new ecology tables;
- new seasonal events;
- horizon and landmark updates.

Expansion should not require:

- renumbering existing cells;
- moving the world origin;
- rewriting saves;
- changing core biome enums;
- replacing the renderer;
- introducing a chapter sequence.

## 12. World acceptance questions

A world slice is aligned when:

- players choose more than one route;
- most space exists outside the shortest objective path;
- backtracking works;
- landmarks orient without over-explaining;
- quiet areas still contain signs of life;
- migration influences but does not command movement;
- cells are invisible to the player;
- players describe a place, not a level layout.


---

# Ecology, Migration, and Animal AI

Status: **Canonical architecture and experience direction**

## 1. Ecology is the objective generator

Eonwild’s world should produce player goals from changing suitability rather than a conventional quest system.

A species evaluates places according to factors such as:

```text
suitability =
  food value
  + water value
  + thermal comfort
  + shelter
  + social attraction
  + reproductive/seasonal value where applicable
  - predator pressure
  - competition
  - traversal cost
  - injury risk
  - environmental hazard
```

The exact formula is species-dependent and tunable. It is a game model, not a claim of complete paleobiological accuracy.

## 2. Ecological state

The world tracks coarse fields and records including:

- plant biomass by feeding type and height;
- water availability and suitability;
- shelter and visibility;
- temperature and exposure;
- carcass/scavenge opportunities;
- disturbance, fire, flood, or drought;
- population capacity;
- traffic and predation pressure;
- herd/pack destinations and memory.

Only information that can affect behavior or presentation should be simulated.

## 3. Migration as a changing attractor

Migration is not:

- a glowing route;
- a scripted spline every animal follows;
- a hard boundary closing behind the player;
- the only meaningful activity.

Migration is a distribution of incentives.

Different groups may:

- leave at different times;
- use different routes;
- stop or split;
- remain territorial;
- move only locally;
- follow prey;
- avoid a recently dangerous crossing;
- remember prior water or feeding sites.

The player may follow early, follow late, scout, exploit abandoned areas, wait, or ignore the movement.

## 4. Near, mid, and far simulation

### Individual fidelity — near players

- individual position and movement;
- detailed condition;
- perception;
- local decision making;
- collision and interaction;
- skeletal animation;
- combat or social behavior;
- injury and death.

### Group fidelity — mid distance

- herd/pack centroid;
- population and composition;
- formation or visual subset;
- shared destination;
- average condition;
- alertness;
- simplified route and avoidance;
- reduced decision frequency.

### Record fidelity — far world

- species/archetype;
- approximate cell/region;
- population count;
- life-stage and condition distribution;
- resources and threat pressure;
- destination and movement intent;
- deterministic seed and recent significant events.

Promotion and demotion must conserve population, group identity, injuries/deaths that matter, and movement intent.

## 5. Herd behavior

A herd should feel like a social population, not synchronized clones.

Group-level state can include:

- cohesion;
- panic;
- vigilance;
- travel urgency;
- trust/familiarity;
- juvenile protection;
- feeding spread;
- route memory;
- dominant movement cues.

Individuals add:

- local spacing;
- animation variation;
- delayed reactions;
- occasional independent decisions;
- condition and age differences.

A herd is not forty independent global pathfinders. It is one group decision system expanded into perceptible individual variation near the player.

## 6. Predator behavior

Predators should make readable, risk-aware decisions:

- follow prey concentration;
- use cover and wind where relevant;
- assess isolation, size, condition, terrain, and competition;
- abandon bad hunts;
- scavenge;
- defend or avoid carcasses;
- rest after exertion;
- avoid injury when the expected reward is poor.

Predators should not attack every visible player. Constant aggression destroys ecological credibility and makes avoidance impossible to read.

## 7. Social and coordinated behavior

Behavior such as pack hunting, parental care, or complex group coordination is often scientifically uncertain.

The design can use it when:

- it creates a strong species role;
- it is marked as plausible, disputed, speculative, or gameplay-only;
- the field guide does not present it as settled fact;
- the AI remains readable and fair.

Coordination should emerge from shared targets, communication, position, and role assignment—not a magical damage bonus.

## 8. Runtime AI technology

Shipped animals use conventional bounded systems such as:

- utility scoring;
- state machines/state trees;
- perception;
- route graphs;
- group blackboards;
- deterministic randomness;
- local avoidance;
- event-driven updates.

Runtime LLM calls are not part of the core game. They would create cost, latency, nondeterminism, networking difficulty, and hard-to-debug behavior without improving the central fantasy enough.

## 9. Ecological communication

The player should infer state from:

- herd direction;
- unusual silence;
- alarm calls;
- tracks converging or dispersing;
- exposed mud or dropping water;
- scavenger concentration;
- smoke and wind;
- vegetation condition;
- animal posture and pace;
- distant dust;
- weather fronts.

A restrained instinct interface may amplify information the animal plausibly senses. It should not become a wall-hack or objective radar.

## 10. Fairness and readability

Systemic does not mean arbitrary.

Danger should usually have evidence:

- calls;
- tracks;
- disturbed animals;
- visibility and terrain cues;
- scent or instinct indications;
- prior knowledge of hotspots.

Ambushes can surprise the player, but the game should avoid repeated unavoidable deaths from untelegraphed spawning.

## 11. Ecological events

Candidate event families:

- drought and shrinking water suitability;
- flood and crossing changes;
- cold front and shelter pressure;
- heat wave and activity shift;
- vegetation bloom or decline;
- fire/smoke front;
- herd arrival or departure;
- predator concentration;
- carcass event;
- disease or contamination only if it creates clear choices and does not become opaque punishment.

Events should change routes and relationships, not merely apply a debuff icon.

## 12. Ecology success criteria

The ecology is working when:

- players explain why animals are moving;
- different species respond differently to the same event;
- the player can predict some outcomes without the world becoming deterministic;
- solo sessions remain populated and causally coherent;
- the system creates repeatable stories;
- far simulation supports scale without wasting active actors;
- event changes are visible and audible;
- route choice changes without a forced quest path.


---

# Creatures, Species, and Player Roles

Status: **Canonical architecture and roster principles**; initial roster remains a working decision.

## 1. Species are role packages

A playable species is not a model plus statistics. It is a complete way of receiving information, moving through the world, managing pressure, and interacting with other animals.

A species definition combines:

- taxonomy and evidence;
- morphology;
- biomechanical family;
- locomotion profile;
- ecology profile;
- senses;
- social tendencies;
- capabilities;
- presentation;
- life-stage and condition rules.

The runtime should not branch on literal species names for mechanics that can be expressed through those components.

## 2. Species differentiation dimensions

A species can differ through:

### Information

- vision distance and motion sensitivity;
- hearing direction/range;
- scent or track reading;
- group warning calls;
- water or food detection;
- ability to interpret distant herds or carcasses.

### Movement

- acceleration;
- maximum and sustainable speed;
- turning radius;
- stamina;
- terrain tolerance;
- wading or swimming ability;
- cover usage;
- slope and mud performance.

### Needs

- food quantity and type;
- water dependence;
- thermal comfort;
- rest requirements;
- group or territory pressure;
- injury recovery cost.

### Interaction

- flee;
- hide;
- warn;
- brace;
- shove;
- pounce;
- bite;
- slash;
- tail strike;
- group pursuit;
- protect or follow.

### Risk profile

- visibility;
- vulnerability to injury;
- scarcity of suitable food;
- competition;
- juvenile difficulty;
- dependence on group behavior;
- commitment required by attacks or defensive actions.

## 3. Engineering families

Taxonomy and engineering reuse remain separate.

Initial or planned biomechanical families include:

### Agile predatory biped

Possible members include small dromaeosaurid-like or other agile theropods within a compatible morphology envelope.

Core play themes:

- rapid acceleration;
- balance and reorientation;
- cover and stalking;
- target selection;
- limited commitment;
- possible social coordination where configured.

### Light cursorial biped

Useful for small or medium herbivorous/omnivorous runners.

Core play themes:

- vigilance;
- endurance;
- route discovery;
- low food cost;
- loose herd behavior;
- escape through awareness and movement.

This may share technical systems with agile predatory bipeds while requiring different posture, feeding, head/arm, and gait treatment.

### Heavy predatory biped

Useful for many tyrannosaurid-like morphologies.

Core play themes:

- momentum;
- powerful bite and body pressure;
- territorial visibility;
- high food demand;
- costly turning and recovery;
- severe injury consequences.

### Long-reach predatory biped

Useful for megaraptoran-like morphologies.

Core play themes:

- forelimb reach and positioning;
- a different contact grammar from heavy-headed predators;
- potentially more gracile pursuit;
- unique commitment distances.

### Low armored quadruped

Useful for ankylosaurian-like forms.

Core play themes:

- low center of mass;
- bracing;
- armor orientation;
- defensive terrain selection;
- limited acceleration;
- optional tail-weapon mechanics.

### Future families

Potential future families include:

- hadrosauriform/facultative bipedal herbivore;
- large ceratopsian;
- stegosaurian;
- sauropod variants;
- spinosaurid or water-edge specialist;
- therizinosaurian;
- small generalized herbivore;
- aerial and aquatic families only after the terrestrial game is mature.

A family enters production only when reuse value and mechanical difference justify its cost.

## 4. Initial playable roster direction

The strongest early roster is not a famous apex predator lineup.

### Starter role A — fast herbivore or omnivore

Purpose:

- prove non-combat play;
- teach observation and route choice;
- make migration, herd, and environmental systems central;
- operate within manageable animation and food-web requirements.

Desired experience:

- detect danger;
- decide when to leave;
- use cover and stamina;
- warn or follow a herd;
- exploit varied food;
- survive through information.

### Starter role B — small or medium predator

Purpose:

- prove tracking, positioning, and risk-aware hunting;
- reuse parts of a biped technical foundation;
- create a contrasting decision loop.

Desired experience:

- read tracks and wind/scent;
- select an isolated target;
- commit only when conditions are good;
- abandon hunts;
- scavenge;
- avoid injury and competition.

### Third role — defensive quadruped, later

Purpose:

- prove a genuinely different body family;
- create position/defense gameplay;
- broaden herbivore fantasy.

### Apex predator, later

A large tyrannosaurid-like animal should arrive after:

- the food web supports its demand;
- prey AI is credible;
- injury, momentum, and contact are mature;
- players already understand smaller roles;
- animation quality can meet the highest expectations.

## 5. Why apex is not the default progression end

An apex predator is not “the best dinosaur.” It pays for power through:

- enormous food pressure;
- few appropriate targets;
- visible movement and territory;
- dangerous rivals;
- high cost of failed hunts;
- slower recovery;
- severe injury risk;
- vulnerable early life if ontogeny is used.

The server/world should not converge into only apex animals.

## 6. Capabilities from physical relationships

Mechanics should emerge from traits and relative state.

Examples:

### Momentum knockdown or destabilization

Inputs may include:

- attacker mass;
- target mass;
- relative speed;
- contact angle;
- target stance;
- armor;
- footing;
- stamina.

### Coordinated pursuit

Inputs may include:

- social-behavior profile;
- group size;
- communication state;
- relative positions;
- stamina;
- target awareness;
- scientific/gameplay confidence.

### Armor brace

Inputs may include:

- armor distribution;
- body orientation;
- stance;
- incoming direction;
- terrain;
- tail-weapon readiness.

### Browse-height access

Inputs may include:

- head reach;
- neck posture;
- body size;
- rearing capability;
- vegetation height band.

These systems enable large/small differences without bespoke species classes.

## 7. Ontogeny and life stages

Working direction:

- life stage can materially change gait, stability, diet, risk, group position, and capability thresholds;
- juveniles should not be simple scaled adults;
- ontogeny can create interesting species-specific runs;
- initial versions may avoid full hatchling-to-adult simulation to reduce animation and balance scope;
- a species may start as a capable young animal while later modes explore vulnerable juvenile lives.

## 8. AI-only species and ambient life

Not every species needs full playable depth.

Content tiers:

- **Playable hero species** — complete controls, animations, progression, field guide, and role.
- **Full AI ecological species** — detailed near behavior and interactions.
- **Simplified ecological species** — limited behaviors supporting the food web.
- **Ambient life** — insects, fish, distant flyers, small animals, silhouettes, and calls.

The world can feel diverse without making every animal playable.

## 9. Roster expansion criteria

A new playable species should add at least two strong differences in:

- information loop;
- movement;
- resource pressure;
- route choice;
- social behavior;
- interaction capability;
- ecological relationship.

It should also have:

- a provenance-complete dossier;
- a reviewed body-family fit;
- known unique animation cost;
- a runtime budget;
- an explicit role in the current ecosystem;
- no dependence on protected reference imagery.

## 10. Species-quality questions

A species is working when:

- players change strategy rather than only animation;
- its advantages create visible costs;
- its body feels appropriate to its mass and morphology;
- it remains interesting away from combat;
- its field-guide claims remain honest;
- another species can share its family without feeling like a reskin.


---

# Survival, Senses, Hunting, and Injury

Status: **Canonical principles**, working direction for exact tuning.

## 1. Survival without chore simulation

Eonwild should make animal needs meaningful without turning the game into constant meter maintenance.

Needs exist to create decisions:

- when to leave;
- where to rest;
- whether to commit to a hunt;
- whether to cross exposed terrain;
- whether to remain with a group;
- whether injury makes the current route impossible.

They should not force repetitive eating or drinking every few minutes merely to keep the player busy.

## 2. Core condition model

Potential condition dimensions:

- energy/hunger;
- hydration;
- stamina and exertion;
- thermal comfort;
- rest/fatigue;
- injury;
- fear/alertness;
- social state where relevant.

Not every dimension needs a prominent bar. Several should be communicated through:

- animation;
- breathing;
- posture;
- sound;
- movement limits;
- sensory changes;
- subtle HUD states.

## 3. Feeding

Feeding should involve ecology and safety, not only holding a button.

Herbivore decisions can include:

- food type and quality;
- feeding height;
- exposure;
- group spacing;
- how long to remain in one patch;
- whether local biomass is recovering or declining;
- competition;
- water proximity;
- escape routes.

Predator feeding can include:

- fresh kill versus carcass;
- competition;
- time spent vulnerable while feeding;
- carcass ownership and intimidation;
- whether the meal justifies injury or travel.

Repeated low-risk feeding must not become the optimal Lineage farm.

## 4. Senses

The player should not possess unrestricted omniscient vision.

### Vision

- movement and silhouette detection;
- obstruction by vegetation and terrain;
- species-dependent field and sensitivity;
- weather and light influence;
- head orientation matters where practical.

### Hearing

- directional calls;
- distance and occlusion;
- water, wind, and vegetation masking;
- recognizable call meanings learned over time.

### Smell and tracks

- broad scent direction or recent trail;
- wind influence;
- age/strength of sign;
- carcass, water, herd, predator, or individual clues;
- species-dependent ability.

### Instinct interface

A restrained sensory mode may visualize information the animal could plausibly infer.

It should:

- amplify nearby evidence;
- remain species-specific;
- preserve uncertainty;
- avoid showing every actor through terrain;
- avoid becoming a permanent navigation overlay.

## 5. Hunting

A hunt should be a sequence of decisions:

1. locate likely prey or sign;
2. assess target, group, terrain, and competitors;
3. approach using cover, wind, speed, or patience;
4. choose whether to commit;
5. execute a short high-risk contact phase;
6. pursue, disengage, or recover;
7. secure and feed, or accept failure.

The most important predator skill may be knowing when not to attack.

## 6. Combat philosophy

Combat is:

- physical;
- positional;
- relatively simple in controls;
- dangerous;
- species-dependent;
- not the sole content loop.

A creature typically has a limited action grammar:

- primary bite/strike/shove;
- secondary defensive or positional action;
- contextual interaction;
- movement specialization;
- calls and body language.

Avoid:

- long combo strings;
- ability cooldown bars resembling a hero shooter;
- large health pools encouraging repetitive trading;
- universal dodge rolls;
- arbitrary rock-paper-scissors species bonuses;
- instant animation cancellation that removes mass.

## 7. Contact and commitment

Actions should have:

- anticipation;
- commitment;
- contact window;
- recovery;
- terrain and orientation requirements;
- species-appropriate vulnerability.

A large bite or body impact may be powerful but harder to redirect. A smaller animal may attack more quickly but cannot ignore mass and armor.

## 8. Injury

Injury should alter the life story rather than only reduce a health number.

Possible effects:

- reduced acceleration;
- altered gait;
- lower sustainable speed;
- limited turn direction;
- increased energy cost;
- bleeding or scent risk where appropriate;
- reduced attack confidence;
- need for longer rest;
- inability to use certain routes or crossings.

Injury severity must remain readable. The player should understand what changed and why.

## 9. Recovery

Recovery creates decisions about:

- shelter;
- rest duration;
- water and food;
- group safety;
- exposure;
- abandoning a migration or hunt;
- accepting a slower route.

Do not require crafting medicine or collecting healing items.

## 10. Herbivore gameplay depth

Herbivore lives must remain engaging without combat.

Key pressures:

- forage quality and competition;
- vigilance;
- herd cohesion;
- warning calls;
- route timing;
- weather;
- crossings;
- juvenile or vulnerable group members later;
- shelter and open-ground decisions;
- deciding when a predator is real versus distant.

A herbivore should not spend the session only eating while waiting to be attacked.

## 11. Escape

Escape is a skill loop:

- detect;
- orient;
- choose terrain;
- accelerate;
- manage stamina;
- break line of sight;
- use group or cover;
- avoid panicked dead ends;
- know when pursuit has ended.

Lineage can reward a genuine close escape, but repeated artificial triggering should stop paying.

## 12. Scavenging

Scavenging creates lower-cost but contested opportunities:

- scent or visible scavengers lead to carcasses;
- freshness and remaining food matter;
- the killer may return;
- multiple predators create intimidation or avoidance;
- carcasses become temporary ecological hotspots.

## 13. Violence and tone

Working direction:

- predation is naturalistic and consequential;
- avoid celebratory gore or excessive spectacle;
- blood/injury effects should communicate state, not become the aesthetic focus;
- final content rating remains an open production decision.

## 14. Survival-quality questions

The system is aligned when:

- needs change plans rather than create chores;
- hunts include meaningful aborted attempts;
- injury changes route and behavior;
- herbivore play remains interesting;
- danger is usually readable;
- combat preserves mass and commitment;
- death has a causal story;
- players can recover through animal behavior rather than inventories.


---

# Lineage, Progression, and Unlocks

Status: **Canonical progression philosophy**; exact economy remains a working direction.

## 1. Why progression exists

Progression should encourage:

- trying different species;
- learning ecological roles;
- taking meaningful risks;
- exploring routes;
- noticing behavior and environment;
- replaying lives without turning them into chores.

The progression resource is **Lineage**.

Lineage represents accumulated mastery, legacy, and the continuation of animal lives across runs. It is not literal money carried by a dinosaur.

## 2. What earns Lineage

Lineage comes from meaningful events and species-appropriate behavior.

Candidate event categories:

### Survival and movement

- reaching a viable seasonal range;
- completing a dangerous crossing;
- surviving a severe weather or environmental event;
- finding an alternate route;
- recovering from serious injury;
- surviving after separation from a group.

### Awareness and escape

- detecting a threat before attack;
- warning nearby animals;
- breaking a committed pursuit;
- using terrain or cover effectively;
- avoiding repeated exposure while vulnerable.

### Feeding and hunting

- finding a scarce food source;
- completing an appropriate hunt while genuinely needing food;
- selecting viable prey;
- abandoning a poor hunt before catastrophic injury;
- locating a carcass through sign or scent;
- defending or sharing a feeding opportunity when the species design supports it.

### Social/ecological behavior

- traveling successfully with a herd/group;
- assisting or protecting another animal;
- responding appropriately to calls;
- maintaining group cohesion during pressure;
- completing a species-specific social challenge.

### Knowledge

- discovering a route, water source, landmark, or ecological relationship;
- completing a field-guide observation;
- demonstrating mastery of a species role.

## 3. Anti-farming rules

Lineage should not be earned efficiently by:

- eating the same safe resource repeatedly;
- walking in circles;
- deliberately triggering the same predator escape;
- cooperating with another player to trade harmless attacks;
- idling through a timer;
- repeating trivial early events without increasing challenge.

Controls include:

- diminishing returns;
- event uniqueness per life;
- risk and context requirements;
- species-appropriate eligibility;
- maximum contribution from low-risk actions;
- server/host validation where multiplayer matters later.

## 4. Death and completion

On death:

- completed event Lineage remains;
- discoveries and field-guide observations may remain;
- completion/survival bonuses are lost;
- the current individual ends;
- the player can review the causal path and begin again quickly.

Survival should be valuable but not the only way a difficult life produces progress.

## 5. What Lineage unlocks

Appropriate unlocks:

- new playable species;
- species trials or ecological-role branches;
- natural pattern, feather, scale, scar, or coloration variants;
- field-guide knowledge;
- alternate starting conditions;
- seeded challenges;
- species mastery records;
- replay, photography, or life-history presentation features;
- optional difficulty modifiers.

Potential later unlocks:

- additional ecosystems or seasonal campaigns;
- supporter cosmetics;
- cosmetic call/body-language variations where they do not affect readability.

## 6. What Lineage must not unlock

- universal damage bonuses;
- permanent maximum health advantages;
- purchased stamina advantages;
- faster hunger reduction for paying players;
- better matchmaking power;
- exclusive statistically dominant apex predators;
- paid revival;
- purchasable Lineage;
- loot boxes.

## 7. Species unlock philosophy

Unlocking a species opens a new problem, not a larger number.

A fast small animal may be easier to feed but vulnerable to contact. An armored herbivore may survive direct pressure but travel slowly. A large predator may dominate a narrow situation while struggling with energy and injury.

The progression tree should communicate ecological relationships and role variety rather than a ladder ending at “strongest carnivore.”

## 8. Starter access

Working direction:

- at least one complete non-predator role should be available immediately;
- a contrasting predator role should be accessible early through play or included in the initial free/premium package;
- players should understand the game before being asked to grind for the fantasy shown in marketing;
- locked species may be trialed in controlled solo challenges without creating power pressure.

## 9. Species mastery

Each species can have mastery categories such as:

- locomotion and route use;
- feeding strategy;
- threat response;
- social behavior;
- hunting or defense;
- seasonal survival;
- discovery.

Mastery should reveal knowledge, cosmetics, challenges, and personal records. It should not create a permanent competitive stat gap.

## 10. Life summary

After a life, show:

- path traveled;
- major environmental events;
- encounters;
- injuries;
- discoveries;
- completed Lineage events;
- cause of death or resolution;
- species mastery changes;
- notable choices.

The summary should help the player retell the story and understand what they could try differently.

## 11. Save and authority direction

Early versions can use:

- local profile;
- local Lineage;
- local unlocks;
- optional browser storage or later Wails/Steam cloud synchronization.

Because the game is solo/co-op and has no tradeable economy, local save editing is a lower risk than prematurely building an account backend.

Paid ownership and important commercial entitlements should eventually use platform/server validation. Lineage itself should never become financially tradeable.

## 12. Progression-quality questions

The system is working when:

- players pursue different animal behaviors;
- death still creates forward movement without feeling consequence-free;
- safe repetitive actions are not optimal;
- new species feel like new games;
- a player can enjoy the base game without paying for power;
- the summary makes another life appealing;
- progression reinforces ecology rather than replacing it.


---

# Game Modes, Multiplayer, and Social Play

Status: **Canonical solo-first principle**; multiplayer details are working direction.

## 1. Solo is the primary contract

Every core system must work for one player:

- ecology;
- migration;
- herds;
- predators;
- scavengers;
- progression;
- environmental events;
- replayability.

The game must not become empty or mechanically incomplete when no other humans are online.

## 2. Initial mode structure

### Solo life

The complete core experience:

- local world simulation;
- local progression;
- pause where appropriate;
- no network dependency after required assets are available;
- seeded conditions and repeatable lives.

### Private cooperative life — later working direction

Start with two players and expand toward four only after the solo game is strong.

Initial assumptions:

- invite/link or room code;
- same species or compatible social role first;
- host-authoritative simulation;
- no public ranking;
- no tradeable economy;
- partial Lineage settlement on disconnect.

### Public PvPvE — future option

Possible only after:

- movement and combat are stable;
- authority and cheating risks are acceptable;
- matchmaking population exists;
- species balance is based on ecology rather than duel parity;
- public sessions add more value than operational burden.

It is not required for product validation.

## 3. Why same-species co-op comes first

Same-species or herd-compatible co-op reduces early complexity:

- shared movement expectations;
- compatible needs;
- fewer balance permutations;
- understandable calls and social roles;
- easier testing;
- cooperation rather than instant predator/prey griefing.

Mixed species and human-controlled predator/prey interaction can come later.

## 4. Multiplayer architecture direction

Browser private sessions may use:

- one authoritative host browser;
- WebRTC data channels;
- a small Go signaling service;
- STUN and TURN fallback where required;
- state snapshots and events rather than visual-effect replication.

Wails/Steam editions may later use platform lobby/relay services or dedicated/community hosting.

This architecture is a cost-saving direction, not a promise of zero infrastructure. Signaling, relay fallback, diagnostics, and support still exist.

## 5. What synchronizes

Synchronize meaningful state:

- player input;
- position and orientation;
- movement state;
- action events;
- confirmed contact/damage;
- condition and injury;
- feeding/drinking ownership;
- important AI state;
- weather/ecology seed and events;
- Lineage event eligibility.

Recreate locally:

- footsteps;
- rain particles;
- grass movement;
- breathing;
- minor head/tail variation;
- ambient insects;
- nonessential visual effects.

## 6. Host departure

Initial direction:

- settle completed Lineage events;
- preserve an optional chapter/checkpoint state when feasible;
- end or re-host cleanly;
- do not build seamless host migration before the game proves demand.

A graceful session ending is better than an unreliable transparent migration system.

## 7. Separation and world cost

Multiple players can move apart and expand the active-world union. Early multiplayer may impose a generous but explicit separation policy or warn when players exceed supported distance.

The constraint should be presented as social/ecological cohesion where appropriate, not an invisible teleport wall. The solo world remains continuous.

## 8. Social communication

Primary in-world communication should use:

- species calls;
- body orientation;
- posture;
- movement;
- group markers only where necessary;
- limited contextual signals.

Text chat may exist in private sessions later. Built-in voice chat is not an initial requirement.

Calls must remain meaningful and readable. Cosmetic call variation cannot make critical communication ambiguous.

## 9. Cooperation examples

- shared vigilance;
- alternating attention while feeding;
- warning calls;
- protecting a vulnerable group member;
- coordinated movement through a crossing;
- pressure/flank/intercept behavior for species where the game interpretation supports it;
- guiding another player toward water or shelter;
- sharing or contesting a carcass.

Cooperation should not reduce to standing close for a passive stat buff.

## 10. PvP philosophy

When human predator/prey interaction exists:

- the world is not balanced as equal duels;
- avoidance, detection, terrain, group size, condition, and species role matter;
- spawn camping and repeated targeting need safeguards;
- death remains meaningful but session length respects the player;
- no ranked ladder or cash-valued progression should motivate cheating.

## 11. Community servers — future

A later desktop edition may provide a headless or community-hosted server executable with configurable:

- player count;
- session length;
- PvP rules;
- ecological intensity;
- species availability;
- progression policy;
- accessibility and difficulty.

Community hosting can support dedicated players without requiring Eonwild to fund every persistent server.

## 12. Not in initial multiplayer scope

- 100-player promises;
- seamless host migration;
- guilds/clans;
- global economy;
- trading;
- ranked esports;
- voice moderation infrastructure;
- persistent MMO world;
- cross-platform competitive progression;
- public matchmaking before private sessions are stable.

## 13. Multiplayer-quality questions

Multiplayer is worth expanding when:

- it adds stories unavailable in solo;
- players communicate through animal behavior;
- solo remains complete;
- host authority is stable;
- disconnection does not erase the session unfairly;
- group play does not trivialize ecological pressure;
- infrastructure and support costs remain proportionate to demand.


---

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


---

# Audio and Sensory Design

Status: **Canonical direction**

## 1. Audio is gameplay information

Eonwild’s sound should do more than create atmosphere. It should communicate:

- distance and direction;
- herd movement;
- predator presence;
- weather and water state;
- vegetation density;
- terrain and body weight;
- social intent;
- exertion and injury;
- environmental change.

A player should sometimes understand an ecological event before seeing it.

## 2. Dinosaur vocal direction

Exact dinosaur vocalizations are unknowable. Eonwild should present them as **plausible bioacoustic reconstructions**, informed where useful by modern birds, crocodilians, other reptiles, body size, resonating structures, and habitat—not as claims of recovered historical sound.

Avoid the default language of cinematic monster roars.

Desired qualities:

- breath and body resonance;
- low-frequency components for large bodies;
- non-mammalian texture where appropriate;
- calls designed for distance and habitat;
- restraint;
- species/family coherence.

## 3. Call vocabulary

A playable species may use a compact call set:

- contact;
- alarm;
- threat;
- submission/appeasement;
- distress;
- juvenile/dependent call where relevant;
- feeding or group-location call;
- long-distance call;
- breath/exertion.

Not every species needs the same vocabulary. Calls should have gameplay meaning without becoming a conventional chat emote wheel detached from animal behavior.

## 4. Call readability

Critical calls need:

- recognizable acoustic identity;
- distance variants;
- occlusion and habitat response;
- directionality;
- controlled variation that preserves meaning;
- optional caption/visual accessibility support.

Cosmetic variants must not make an alarm sound like a friendly contact call.

## 5. Movement and body sound

Creature presence comes from:

- footfalls by substrate and gait;
- breathing and exertion;
- vegetation contact;
- water contact;
- body/armor/feather movement where appropriate;
- jaw and feeding sound;
- injury and fatigue variation.

Footstep intensity should reflect perceived mass, speed, and surface without becoming exaggerated every step.

## 6. Environmental sound layers

### Water

- current;
- shallow edge;
- deep channel;
- wetland;
- rain on water;
- drying/receding water state.

### Vegetation

- wind by canopy type;
- close foliage movement;
- dry versus wet material;
- distant forest mass;
- insects and small ambient life.

### Weather

- distant thunder;
- approaching rain;
- wind direction and strength;
- smoke/fire where used;
- reduced/muffled sound under severe weather.

### Distant life

- herd calls;
- scavenger activity;
- panic movement;
- off-screen population;
- occasional silence signaling danger.

## 7. Ecological cue design

An event should use several reinforcing channels.

Example: drying watercourse

- water ambience weakens;
- exposed mud has different foot sound;
- distant herd calls shift direction;
- local ambient life changes;
- wind carries another water source;
- the instinct interface may amplify the change.

No single cue should carry the entire burden when accessibility and noisy environments are considered.

## 8. Music

Working direction:

- music is sparse;
- environmental sound carries most of the experience;
- music supports awe, transition, crisis, and aftermath rather than constant action;
- avoid making every predator encounter sound like a scripted boss fight;
- silence and natural ambience remain valuable.

## 9. Procedural variation

Use bounded variation in:

- pitch;
- timing;
- layer combination;
- distance processing;
- reverb;
- intensity;
- surface response.

Variation must not change semantic meaning or produce obviously random synthetic output.

## 10. AI-generated audio policy

Generated source material can accelerate production when:

- the provider license permits commercial use;
- model, version, prompt, inputs, and terms are recorded;
- the output is edited, layered, and reviewed;
- no protected or noncommercial sample is laundered through generation;
- the result fits the shared sonic language.

Raw “AI dinosaur roar” output should not ship without design and mixing.

## 11. Spatial audio and performance

Priorities:

- accurate direction for gameplay-critical calls;
- distance rolloff;
- limited occlusion where it provides value;
- pooled emitters;
- group-level distant audio rather than one emitter per far animal;
- controlled simultaneous voice count;
- device/headphone/speaker testing.

## 12. Accessibility

Support where feasible:

- call captions or categorized indicators;
- directional audio visualization;
- separate volume groups;
- reduced low-frequency intensity option;
- subtitle-like environmental cue descriptions in accessibility mode;
- no gameplay information available only through one inaccessible channel.

## 13. Audio-quality questions

Audio is working when:

- the animal feels heavier and more alive with sound;
- players locate calls;
- ecological changes are heard;
- species calls remain recognizable;
- repetition is controlled;
- mix clarity survives dense scenes;
- provenance is complete;
- silence is used intentionally.


---

# UI, UX, Field Guide, and Accessibility

Status: **Canonical principles**, working direction for final interface design.

## 1. UI philosophy

The world should communicate before the HUD does.

The interface should help the player understand:

- their body;
- urgent needs;
- known ecological information;
- calls and senses;
- Lineage and life history;
- settings and accessibility.

It should not turn Eonwild into a conventional quest tracker or spreadsheet overlay.

## 2. HUD hierarchy

### Always or frequently visible

Only information that needs immediate action:

- critical condition;
- stamina/exertion feedback;
- injury state;
- contextual interaction;
- essential group/call information where applicable.

### Contextual

- hydration or food quality details;
- sensory observations;
- species capability readiness;
- route/landmark memory;
- environmental warnings already detected by the animal.

### Out of active play

- Lineage;
- field guide;
- life summary;
- species mastery;
- settings;
- detailed evidence/science notes.

## 3. Communicating body condition

Use several channels:

- animation and posture;
- breathing;
- sound;
- movement response;
- screen/HUD indication;
- controller feedback where available.

Do not require the player to stare at multiple bars to know the animal is exhausted or injured.

## 4. Sensory interface

A sensory/instinct action can:

- emphasize recent tracks;
- indicate broad scent direction;
- isolate calls;
- reveal known water/food suitability;
- identify group signals;
- summarize information the animal plausibly perceives.

It should not:

- reveal every animal through terrain;
- show an exact objective route;
- remove uncertainty;
- remain permanently active without tradeoff;
- present human scientific labels during immediate danger.

## 5. Navigation

Potential navigation aids:

- remembered landmarks;
- a stylized mental map;
- discovered water/route knowledge;
- sun, wind, river, and terrain orientation;
- optional stronger assistance accessibility mode.

Avoid a permanent GPS line to migration.

A map should represent what the player/animal has learned rather than expose the entire world immediately.

## 6. Onboarding

The first session should:

- allow movement within seconds;
- teach one input at a time through context;
- show food/water/sense interactions naturally;
- avoid a long text tutorial;
- allow experienced players to skip guidance;
- reveal ecology through an early readable change.

A safe tutorial enclosure should not misrepresent the open-world game.

## 7. Species selection

The selection screen should communicate:

- ecological role;
- movement style;
- food/water pressure;
- social tendency;
- difficulty;
- major strengths and costs;
- scientific period and geography;
- current unlock/mastery state.

Do not present species as a damage/health tier list.

## 8. Field guide

The field guide is both educational and progression content.

For each species, distinguish:

### Scientific record

- name and classification;
- geological age;
- geography/formation;
- size ranges and evidence;
- known material;
- integument evidence;
- diet/locomotion evidence;
- uncertainty and disputes.

### Eonwild interpretation

- fictional ecosystem role;
- gameplay-tuned values;
- chosen social/hunting interpretation;
- capabilities;
- deviations made for play.

### Player observations

- discovered calls;
- food sources;
- tracks;
- routes;
- encounters;
- mastery records.

The guide should never blur gameplay invention into scientific fact.

## 9. Life summary

At the end of a life, present:

- route map;
- timeline of major events;
- environment changes;
- herd/group interactions;
- hunts, escapes, injuries, and discoveries;
- cause of death or success;
- Lineage earned and why;
- species mastery;
- another-life options.

Tone should resemble a natural-history life record, not a kill/death scoreboard.

## 10. Menus and application shell

Svelte owns low-frequency interfaces:

- home/start;
- species selection;
- Lineage;
- field guide;
- settings;
- playtest/telemetry consent;
- pause;
- life summary;
- store/platform surfaces later.

The real-time renderer and simulation remain outside Svelte reactivity.

## 11. Input support

Committed desktop direction:

- keyboard and mouse;
- controller;
- full remapping where practical;
- consistent abstract action map;
- separate camera and movement sensitivity;
- toggle/hold alternatives;
- no essential hover-only interaction.

Mobile touch is not a committed target, but the action model should avoid needless complexity that makes future adaptation impossible.

## 12. Accessibility baseline

### Visual

- scalable UI/text;
- contrast controls;
- color not the sole information channel;
- subtitle/call indicators;
- reduced bloom/fog intensity where needed;
- optional outline or cue assistance;
- safe-area and resolution support.

### Motion and camera

- camera shake control;
- motion blur toggle;
- head bob control;
- FOV/camera-distance options within gameplay limits;
- recenter behavior;
- reduced sudden camera movement;
- pause in solo.

### Audio

- categorized captions;
- directional indicators;
- separate volume groups;
- low-frequency reduction.

### Motor/cognitive

- remapping;
- hold/toggle options;
- auto-run;
- sensitivity/dead-zone control;
- optional stronger environmental cue assistance;
- clear cause-and-effect feedback.

Accessibility assistance should communicate more clearly without automatically trivializing the ecological choice.

## 13. Telemetry and privacy

During development playtests:

- use anonymous local session IDs;
- identify build, content hash, seed, renderer, and quality profile;
- collect gameplay/performance events only;
- export locally by default;
- do not collect name, email, precise location, microphone, camera, or unrelated files without explicit need and consent.

## 14. UX-quality questions

The interface is aligned when:

- players move quickly;
- they understand at least one environmental cue without exposition;
- HUD use does not replace looking at the world;
- species selection communicates roles;
- the field guide is scientifically honest;
- life summaries create replay desire;
- accessibility uses multiple channels;
- the interface feels like Eonwild, not a generic survival template.


---

# Scientific Framing, Setting, and World Fiction

Status: **Canonical framing**

## 1. Core setting decision

Eonwild uses a fictional paleo-continent or ecological simulation context so it can combine compelling species, climates, and food-web roles without falsely claiming that every animal coexisted in one historical place and time.

The game should state this clearly.

## 2. The animals versus the assemblage

### Animals

Target:

- anatomically plausible;
- evidence-linked;
- current reconstruction thinking;
- uncertainty documented;
- behavior marked by confidence;
- gameplay tuning separated from evidence.

### Assemblage

Game fiction:

- species may come from different formations, regions, and ages;
- climatic distribution is designed for a coherent playable continent;
- ecology is tuned to produce meaningful roles and migration;
- the game does not claim a literal historical ecosystem.

This lets the project satisfy players who want a broad roster while remaining scientifically honest.

## 3. No required human framing

The core fantasy does not require:

- time travelers;
- laboratories;
- human observers;
- cloning facilities;
- sci-fi factions;
- human equipment;
- a human protagonist.

The player is the animal. Menus and the field guide can exist as a presentation layer without inserting humans into the world.

An explicit simulation fiction may be added later only if it improves the product and does not undermine the animal fantasy.

## 4. Narrative tone

The world is:

- beautiful;
- indifferent;
- dynamic;
- dangerous;
- not malicious;
- not a theme park built for the player.

Stories come from:

- survival;
- loss;
- movement;
- weather;
- resource change;
- group relationships;
- predation;
- discovery;
- recovery.

Avoid moralizing animals as heroes and villains. Predators are not evil; herbivores are not passive victims.

## 5. Evidence classes

Every claim or reconstruction choice should use statuses such as:

- **supported** — direct or strong evidence;
- **plausible** — reasonable inference;
- **disputed** — meaningful scientific disagreement;
- **speculative** — limited evidence;
- **gameplay-only** — chosen for play rather than presented as science.

A claim can also record confidence and source tier.

## 6. Scientific and gameplay values

Store both when they differ:

```text
evidence value/range
        +
confidence/source
        +
gameplay value
        +
reason for deviation
```

Examples:

- speed range;
- mass;
- turning;
- bite proxy;
- social behavior;
- feather distribution;
- display coloration;
- habitat tolerance.

Do not alter evidence values to make balance appear scientifically justified.

## 7. Behavior uncertainty

Common player expectations can be uncertain:

- coordinated pack hunting;
- parenting;
- group structure;
- specific calls;
- daily activity;
- territoriality;
- migration patterns.

The game may choose an interpretation for a species role. The field guide must identify that interpretation honestly.

## 8. Appearance uncertainty

Separate:

- skeletal proportions;
- preserved structures;
- broad soft-tissue envelope;
- integument evidence;
- inferred related-taxon features;
- artistic coloration;
- display structures;
- gameplay readability adjustments.

Coloration is usually artistic unless evidence supports it. The game can still establish a coherent natural palette.

## 9. Ecological plausibility

Even in a fictional assemblage, the ecosystem should remain internally credible:

- food and water support populations;
- prey availability supports predators;
- large animals carry large resource demands;
- habitat preferences influence distribution;
- climate and water shape movement;
- species roles avoid impossible density;
- AI populations have carrying capacity and pressure.

“Fictional” is not permission for arbitrary ecology.

## 10. Authentic ecosystem scenarios — future option

The architecture may later support historically constrained scenario packs based on a particular formation and interval.

Such a pack could offer:

- authentic contemporaries;
- constrained flora/climate;
- museum or educational partnership potential;
- a more rigorous scientific mode.

It should be an expansion of the same systems, not required for the initial broad-fictional continent.

## 11. Reference and IP policy

Fantastic Dinosaurs is useful for:

- taxon discovery;
- human visual-quality comparison;
- identifying research questions.

Its protected text, illustrations, 3D models, animations, sounds, and other media must not be copied, scraped, redistributed, or used as generation inputs without permission.

Production research should rely on:

- peer-reviewed literature;
- museum records;
- open collections;
- item-level licensed scans/images;
- Paleobiology Database as an evidence and bibliography aid;
- original project art and properly licensed sources.

## 12. Educational value

The field guide can teach:

- where and when the animal lived;
- what evidence exists;
- what remains uncertain;
- how reconstruction changes;
- how the game interpretation differs;
- why biomechanics and ecology matter.

Education should emerge from curiosity and play, not interrupt the game with lectures.

## 13. Revision philosophy

Scientific understanding changes.

The project should:

- use stable internal taxon IDs;
- version dossiers;
- record source dates;
- revise appearances or claims transparently;
- avoid tying saves to display taxonomy;
- distinguish a scientific update from a balance change.

## 14. Setting-quality questions

The framing is successful when:

- players trust the game without believing it claims certainty;
- the broad roster does not create a false historical claim;
- the world feels ecologically coherent;
- no human narrative distracts from animal life;
- the field guide makes uncertainty interesting;
- copyrighted reference work never becomes untracked production input.


---

# Platform, Distribution, and Business Model

Status: **Browser-first platform decision is canonical**; commercial model is a working direction, not current sprint scope.

## 1. Platform strategy

The canonical first runtime is the browser because it provides:

- immediate link-based testing;
- rapid updates;
- Mac-friendly development;
- strong AI-code automation;
- low distribution friction;
- portal options;
- progressive asset delivery;
- a path to PWA installation;
- reuse inside Wails desktop later.

WebGL2 is the compatibility baseline. WebGPU enhances quality where available.

## 2. Primary targets

### Desktop browser

Committed first product-validation target.

- Chrome/Edge and Safari/WebKit priority;
- Firefox later as supported matrix expands;
- keyboard/mouse and controller;
- progressive streaming and caching;
- static deployment where possible.

### PWA

Working direction:

- installable shell;
- cached assets;
- offline solo after required packs are available;
- low-friction return play.

### Wails desktop

Later premium/installed target:

- Windows and macOS first;
- Linux only when support cost is justified;
- same web game core;
- local Go services;
- larger installed asset packs;
- offline play;
- Steam/platform integration;
- local hosting or mod paths later.

Wails does not replace browser rendering with a native 3D engine. It expands packaging and platform capabilities.

### Mobile

Not committed.

Preserve basic architectural possibility through:

- abstract input actions;
- scalable UI;
- quality profiles;
- no hover-only essentials.

Do not lower the desktop game or spend current scope on touch/device QA.

## 3. Distribution sequence

Working sequence:

1. private development links;
2. public solo browser slice;
3. direct PWA and selected nonexclusive portal test;
4. private two-player browser build;
5. monetizable browser release if retention supports it;
6. premium Wails/Steam desktop edition;
7. broader multiplayer, mobile, or dedicated hosting only after evidence.

## 4. Browser free experience

Potential free offering:

- one or two starter species;
- one complete ecological world/slice;
- solo play;
- local Lineage;
- daily/weekly seeded expeditions;
- standard-quality assets;
- private co-op later;
- no arbitrary energy timer.

The free game should prove the real fantasy, not be a shallow tutorial designed only to force purchase.

## 5. Premium desktop experience

Potential premium value:

- no advertising;
- higher-resolution optional asset pack;
- longer full-season mode;
- additional species/ecosystem content;
- fully offline play after installation;
- controller and platform integration;
- private co-op;
- cloud save/achievements later;
- community hosting or mod support later.

The premium edition should add convenience, content, fidelity, and ownership—not repair a deliberately unpleasant free game.

## 6. Advertising principles

Ads are optional commercial tools, not a design pillar.

Acceptable placements:

- after a complete run;
- at a major life-summary boundary;
- before an optional bonus challenge;
- for a temporary cosmetic preview;
- at a natural chapter/checkpoint in a portal-specific short mode.

Unacceptable placements:

- during a chase or hunt;
- on a fixed intrusive timer;
- during multiplayer action;
- to revive after death;
- to restore health/stamina;
- to double essential progression aggressively;
- inside the natural-history presentation.

## 7. Paid content principles

Appropriate paid content:

- supporter cosmetics;
- natural pattern/feather/skin packs;
- new ecological campaigns or regions;
- new biomechanical family/species expansions;
- soundtrack or art book;
- premium desktop edition;
- optional high-resolution assets.

Conditions:

- species remain sidegrades;
- paid animals do not dominate free animals;
- the ecosystem remains functional for base players;
- critical communication is not obscured by cosmetics;
- store descriptions clearly separate real-world science and game fiction.

## 8. Prohibited monetization

- paid Lineage;
- direct combat power;
- loot boxes;
- paid revival;
- hunger/energy reduction purchases;
- exclusive statistically superior apex species;
- paywalled basic accessibility;
- mandatory subscription for solo play;
- a battle pass requiring daily chores.

## 9. Backend discipline

The early product should use:

- local profile and Lineage;
- static content delivery;
- no account requirement;
- minimal signaling only when private multiplayer arrives;
- platform entitlements when commercial content arrives.

Do not build accounts, global economy, or authoritative progression before the product needs them.

## 10. Portal strategy

Portals can provide discovery and ad infrastructure, but may impose:

- size limits;
- initial-load limits;
- SDK requirements;
- monetization rules;
- exclusivity or traffic terms;
- lower-end device expectations.

Use platform adapters and separate build profiles. Do not contaminate game-core with portal SDK logic.

The direct website remains important for:

- community ownership;
- experiments;
- richer builds;
- browser-to-desktop conversion;
- avoiding premature exclusivity.

## 11. Business validation sequence

Commercial decisions follow evidence:

1. Is movement enjoyable?
2. Do players understand ecology?
3. Do they replay?
4. Do they share or return?
5. Does the browser funnel reach enough players?
6. Do committed players want a premium desktop edition or content?
7. Does multiplayer improve retention enough to justify infrastructure?

Advertising cannot rescue weak retention.

## 12. Pricing

Open decision.

Previous planning considered a lower-priced premium indie release/early-access range rather than a full AAA price. Exact price should follow:

- content scope;
- species count;
- polish;
- comparable products at release;
- regional pricing;
- browser free value;
- storefront economics.

Do not encode a price into product identity before the build is validated.

## 13. Commercial success principle

Design cash risk so the project remains survivable at modest sales, while keeping upside through:

- low infrastructure costs;
- player-hosted/private sessions;
- reusable content factories;
- browser discovery;
- premium conversion;
- expansion content.

The largest cost remains development time and quality, not bandwidth.


---

# Content Scope and Release Roadmap

Status: **Canonical sequencing principles**, working direction for content counts.

## 1. Roadmap philosophy

Eonwild should grow through validated layers:

```text
factory
  → embodiment proof
  → roaming/ecology proof
  → vertical slice
  → public browser demo
  → browser product
  → premium desktop product
  → broader multiplayer and expansions
```

Do not build the final roster or continent before the first life is worth replaying.

## 2. Stage 0 — production factory

Purpose:

- reproducible tools;
- provenance;
- Blender pipeline;
- GLB/KTX2 path;
- browser benchmark;
- world-cell contracts;
- evidence and review automation;
- family/species schemas.

Success is a deterministic fixture and world proof, not a game.

## 3. Stage 1 — embodiment and roaming proof

Purpose:

- one production-intent proxy;
- fixed-tick movement;
- camera and animation state graph;
- streamed route loops;
- one ecological pressure;
- near/mid/far herd proof;
- live human diagnostics.

Success means Eonwild has become an evaluable experience.

## 4. Stage 2 — vertical slice

Target content direction:

- one polished playable starter species;
- one contrasting AI threat;
- one herd/prey role;
- ambient life;
- one continuous authored slice with several environmental characters;
- feeding, drinking, rest, senses, escape or hunt;
- injury at limited depth;
- Lineage summary;
- 15–30 minute complete life;
- robust browser performance;
- automated video/perceptual review.

This is the first serious market-testable product.

## 5. Stage 3 — public browser demo

Target direction:

- two playable species with contrasting roles;
- one accepted shared family or two carefully justified families;
- richer ecology;
- several seeded seasonal conditions;
- strong onboarding;
- field guide;
- local progression;
- quality presets;
- controller support;
- static/PWA deployment;
- broad external testing.

Possible modes:

- Quick Expedition;
- a longer Full Season preview;
- seeded challenge.

## 6. Stage 4 — first browser product

Working content direction:

- two free starter species;
- four or more additional earnable or packaged species over time;
- one complete continent/major ecosystem built from streamed cells;
- multiple environmental pressures;
- several full AI ecological species;
- ambient fauna;
- local Lineage and mastery;
- optional private two-player co-op after solo is stable;
- respectful portal monetization where appropriate.

Exact roster depends on body-family reuse and retention evidence.

## 7. Stage 5 — premium desktop / early access

Working direction:

- three to four polished playable species at initial paid entry;
- six to ten significant AI species/roles;
- longer Full Season mode;
- higher-quality installed asset pack;
- offline play;
- controller and platform integration;
- private 1–4 player sessions when stable;
- community-hosted server path later;
- additional Lineage, field-guide, and mastery depth.

A paid build should not depend on promises of dozens of future dinosaurs to justify current value.

## 8. Expansion order

Recommended expansion priority:

1. Improve the first animal until embodiment is convincing.
2. Add a contrasting player role using maximum legitimate family reuse.
3. Deepen ecology so both roles have meaningful lives.
4. Add a genuinely different body family.
5. Expand world content and events.
6. Add private multiplayer.
7. Add apex roles only when the food web supports them.
8. Add historically constrained ecosystem packs or more exotic locomotion later.

## 9. Initial species strategy

### First polished playable

A fast herbivore/omnivore or other non-apex role is preferred because it proves:

- roaming;
- senses;
- herd behavior;
- environmental pressure;
- non-combat fun;
- manageable resource demand.

### Second playable

A small/medium predator proves:

- tracking;
- hunt selection;
- commitment;
- injury risk;
- contrasting information.

### Third family

A defensive quadruped or other mechanically distinct herbivore proves the architecture can expand beyond biped reuse.

### Large predator

Introduced after prey, contact, injury, and ecology are mature.

## 10. Explicitly excluded from initial product

- humans;
- crafting;
- base building;
- complex inventory;
- flying playable animals;
- fully aquatic playable animals;
- underwater combat;
- nesting, eggs, mating, genetics, and parenting as launch requirements;
- clans and global economy;
- public ranked PvP;
- 100-player promise;
- voice chat;
- seamless host migration;
- large mod ecosystem;
- persistent MMO world;
- mobile release commitment;
- photorealistic cinematics as a prerequisite.

These may be reconsidered after the core product is successful. They are not hidden launch promises.

## 11. Content quality rule

A content milestone is not complete because the count is reached.

Every playable species must pass:

- role differentiation;
- scientific/provenance review;
- movement and deformation review;
- performance budget;
- ecology integration;
- Lineage integration;
- live player comprehension.

Every world area must pass:

- roaming topology;
- streaming;
- ecology value;
- composition;
- performance;
- absence of obvious repetition and seams.

## 12. Roadmap decision gates

Before expanding scope, require evidence:

### Add second playable species when

- first species movement is satisfying;
- one life is replayed voluntarily;
- the shared family or new-family cost is known;
- ecology can support the role.

### Add multiplayer when

- solo retention exists;
- network prototype does not damage movement;
- private co-op clearly adds stories;
- signaling/TURN cost and support are measured.

### Add paid product when

- raw gameplay footage communicates the fantasy;
- external players replay;
- quality and performance are credible;
- the free/browser value and premium value are distinct;
- support burden is understood.

### Add apex species when

- prey density and AI are sufficient;
- hunt/injury systems are strong;
- the species has meaningful costs;
- its quality can meet marketing expectations.

## 13. Roadmap anti-patterns

Avoid:

- making a huge roster before locomotion is solved;
- filling a huge map with generic generated content;
- adding multiplayer to create missing AI content;
- adding progression before the life loop is enjoyable;
- adding ads before retention;
- implementing mobile because the web build technically opens on a phone;
- promising a persistent MMO to compensate for weak session structure;
- treating Early Access as permission to sell an unfinished factory.


---

# Example Player Stories

Status: **Illustrative**

These stories are not scripted missions. They demonstrate the kinds of causal lives Eonwild systems should produce.

## 1. The runner that left early

### Role

Fast herbivore/omnivore; loose herd; strong hearing and vision; low direct defense.

### Story

The player begins near an upland feeding area. The local plants remain edible, but distant contact calls are moving toward the floodplain. Other animals are not panicking, so the player could safely stay and feed longer.

The player climbs a ridge and sees a weather front and several herd groups already moving. Instead of following the direct river path, the player takes a longer forest route with more cover.

The route has weaker food but avoids a predator concentration near the main crossing. A juvenile AI animal becomes separated during a storm. The player uses contact calls and waits, sacrificing time and hydration to help it rejoin.

At the floodplain, the direct ford is already rising. The player remembers a shallow western crossing discovered in a prior life. During the crossing, a predator commits. The player breaks line of sight among channels, spends most of its stamina, and reaches the opposite bank injured but alive.

### Lineage events

- early environmental read;
- alternate route discovery/use;
- group assistance;
- dangerous crossing;
- close escape;
- seasonal refuge reached while injured.

### Why it matters

The life is engaging without attacking anything. Knowledge, route choice, social behavior, weather, and escape create the story.

## 2. The hunt that should be abandoned

### Role

Small/medium feathered predator; high acceleration; limited mass; good tracking; injury-sensitive.

### Story

The player begins hungry near a wet woodland. Tracks show a small prey group moving toward open mudflats. Scent and calls suggest another predator is nearby.

The player follows from cover and identifies an isolated, tired individual. The first approach is good, but the wind shifts and the prey group becomes alert. A conventional action game would reward immediate attack. Eonwild makes withdrawal the intelligent choice.

The player circles to another route and finds a fresh carcass with scavengers nearby. Feeding is safer but risks the larger predator returning. The player eats enough to reduce immediate pressure, then leaves before the owner arrives.

Later, the player tracks another prey animal near dense vegetation and completes a short ambush. A leg injury during contact reduces speed. Rather than chasing a second target, the player finds shelter and survives the weather event.

### Lineage events

- viable target assessment;
- abandoned compromised hunt;
- carcass located by sign;
- successful species-appropriate ambush;
- injury recovery;
- seasonal survival.

### Why it matters

Predator mastery includes restraint. The player does not farm kills; food pressure and injury define the decisions.

## 3. The armored animal at the narrow bank

### Role

Low armored quadruped; slow acceleration; strong brace; broad feeding; good defense when oriented correctly.

### Story

The player travels slowly through open country as water suitability declines. The shortest path leads through soft ground where turning is poor. The longer path follows firmer terrain but exposes the animal to heat.

A group of smaller herbivores uses the armored animal as a moving point of safety. Near the water, a predator tries to separate one animal. The player does not chase. It chooses a narrow bank, turns armor and tail toward the threat, and braces.

The predator tests the position, then withdraws because the contact risk is not worth the meal. The player reaches water late and overheated but uninjured.

### Lineage events

- terrain-appropriate route choice;
- group-protection behavior;
- successful brace/deterrence;
- hydration recovery;
- refuge reached.

### Why it matters

Defense is positional, not a passive armor statistic. Slow movement changes route planning and timing.

## 4. The future large predator

### Role

Heavy predatory biped; high mass and bite potential; high food demand; limited turning; severe injury cost.

### Story

The player controls a powerful animal but begins with poor condition. A distant herd is visible, yet most adults are too dangerous and the open ground makes a failed pursuit costly.

The player follows the herd for time, looking for injury, isolation, or terrain that reduces escape options. A smaller predator reaches a carcass first. The player can displace it through size and threat display, but the carcass contains little food.

Later, flooding compresses several animals near a channel. The player uses a momentum-based shove to destabilize lighter prey at the edge, but misses the first contact and suffers a minor foot injury. A second reckless attempt could end the run. The player withdraws, rests, and scavenges instead.

### Lineage events

- carcass control;
- risk-aware hunt selection;
- momentum interaction;
- injury management;
- survival despite unmet ideal prey target.

### Why it matters

Apex scale creates pressure rather than eliminating it. The animal is powerful in a narrow window, not universally easy.

## 5. Two-player migration

### Role

Two players using the same fast herd species in private co-op.

### Story

One player feeds while the other watches distant movement. A warning call causes both to orient rather than showing a UI enemy marker. During travel, they choose different sides of a river channel and temporarily lose visual contact.

One hears an alarm and returns, risking water pressure to help the other break pursuit. They reach a refuge together but earn different Lineage events based on their behavior.

### Why it matters

Multiplayer adds shared attention, communication, rescue, and mistakes. It does not supply the missing ecosystem.

## 6. The life that ignores migration

### Role

Omnivorous runner.

### Story

The dominant herd movement heads south, but the player remains in an abandoned upland area. Food is declining, yet competition is lower. The player discovers insects, seeds, and an overlooked spring.

The choice works for a time. A cold front then makes exposed feeding expensive, and predator pressure rises because fewer prey animals remain. The player must decide whether to leave late through dangerous conditions or commit to a marginal local survival strategy.

### Why it matters

Migration is an attractor, not a command. Ignoring it creates a different life rather than a failure message.

## 7. Story-quality criteria

The systems should make stories like these possible without scripting every beat.

A strong emergent story contains:

- readable initial state;
- at least one meaningful decision;
- consequences;
- interaction between body, world, and ecology;
- a moment of uncertainty or crisis;
- a resolution worth remembering;
- Lineage events that describe behavior rather than grind.


---

# Open Decisions, Design Risks, and Required Experiments

Status: **Canonical uncertainty register**

Agents must not silently resolve these questions. A milestone may adopt a temporary answer for testing.

## 1. First polished playable species

### Current direction

A fast non-apex herbivore/omnivore is preferred, with a small/medium predator second.

### Open questions

- Which real taxon has strong evidence and legally usable references?
- Which body family best balances animation cost and product appeal?
- Will the first species communicate the dinosaur fantasy strongly enough without being a famous apex?

### Experiment

Compare two candidate dossiers and body-family fits, then test silhouette, movement, and player interest using the same environment.

## 2. Exact session duration

### Current direction

- Quick Expedition: 12–20 minutes.
- Full Season: 30–50 minutes.

### Risk

Too short removes attachment and roaming; too long recreates the loss/grind problem.

### Experiment

Test the same ecological scenario at approximately 12, 25, and 40 minutes. Measure route diversity, replay, attachment, and frustration after death.

## 3. Growth and life stage

### Open options

- start as capable young adult;
- compressed juvenile-to-adult within a life;
- species-specific juvenile challenge mode;
- growth across checkpointed sessions.

### Risk

Full growth multiplies animation, balance, asset, and food-web work while delaying player agency.

### Experiment

Prototype size/condition progression using one family and placeholder visuals. Validate whether growth changes decisions enough to justify cost.

## 4. First ecosystem assemblage

### Open question

How broad should the fictional cross-era roster be in the first product?

### Risk

A broad roster improves appeal but can weaken ecological coherence and scientific perception.

### Experiment

Create two roster pitches:

- broad fictional continent;
- more constrained regional/temporal ecosystem.

Test player understanding and content cost.

## 5. Degree of combat and predation

### Risk

Too little contact can make predators unsatisfying; too much turns the game into an arena and makes herbivore play reactive only.

### Experiment

Measure lives where predator pressure is primarily avoidance versus frequent contact. Track tension, fairness, herbivore agency, and injury frequency.

## 6. Injury severity

### Risk

Persistent injury creates stories but can produce a slow unwinnable death spiral.

### Experiment

Test several recovery curves and offer readable choices: shelter, route change, partial recovery, or voluntary life resolution.

## 7. Navigation assistance

### Risk

No assistance may frustrate new players; explicit GPS destroys observation and roaming.

### Experiment

Compare:

- landmarks only;
- discovered mental map;
- species-specific instinct cues;
- accessibility-enhanced route hints.

Measure comprehension and corridor perception.

## 8. World density

### Risk

Large open space can feel empty; dense content can feel like a theme park and overload the browser.

### Experiment

Author quiet, normal, and vista density tiers. Test perceived life, orientation, performance, and whether quiet areas feel intentional.

## 9. First predator threat

### Open question

Should the initial polished slice use a full persistent predator, an event-based threat, or a simplified stalk/pursuit system?

### Experiment

Test each against non-combat herbivore engagement and implementation cost.

## 10. Lineage economy

### Risks

- farming trivial events;
- unlocking too slowly;
- making death irrelevant;
- species locks hiding the main fantasy;
- progression becoming a stat ladder.

### Experiment

Simulate and playtest multiple event distributions. Review the optimal player behavior each economy creates.

## 11. Free versus premium content

### Open questions

- How many starter species are free?
- Is the direct browser build freemium, a complete demo, or a full ad-supported product?
- Which features belong only in premium desktop?
- Are species expansions paid individually or by ecosystem pack?

### Rule

No answer may introduce paid power or make the free game intentionally unpleasant.

## 12. Advertising

### Risk

Ads can damage atmosphere and trust for modest revenue.

### Experiment

Only after retention exists, test natural-boundary placements and measure session abandonment and premium interest.

## 13. Multiplayer value

### Open questions

- Does two-player co-op materially improve replay?
- How much separation is feasible?
- Is same-species play enough?
- When does public predator/prey play become worth the support burden?

### Experiment

Add two-player private hosting only after a stable solo life. Compare stories and retention against solo.

## 14. Browser engine ceiling

### Risks

- Safari/WebView incompatibility;
- vegetation/animation cost;
- shader compilation;
- asset streaming stalls;
- lower-end device variance.

### Experiment

Maintain fixed benchmark scenes and high-quality creature/world videos. Treat WebGL2 as baseline and WebGPU as enhancement.

## 15. Visual target viability

### Current direction

Naturalistic paleo-documentary realism, with staged high-end browser scenes approaching the discussed floodplain reference class.

### Risk

The project may spend too much on still-frame fidelity while movement or ecology remains weak.

### Experiment

Use standardized moving captures, not only screenshots. Evaluate embodiment, scene composition, and frame-time together.

## 16. Perceptual AI review reliability

### Risk

A video model can be inconsistent, prompt-sensitive, or reward cinematic hiding.

### Experiment

Maintain known-good and known-bad calibration clips. Require structured timestamped findings and compare against human reviewers. Cap automated repair loops.

## 17. Field-guide framing

### Open question

How much of the scientific layer appears before, during, or after play?

### Risk

Too much exposition breaks embodiment; too little loses a key differentiator.

### Experiment

Test discovery-based entries and life-summary links rather than active-play popups.

## 18. Death tone and violence

### Open questions

- how explicit are predation and injury visuals?
- what rating/audience target is appropriate?
- should death be immediate, cinematic, or observational?

### Rule

Keep predation naturalistic and non-exploitative. Final rating remains undecided.

## 19. Long-term persistence

### Open options

- fully run-based lives;
- checkpointed Full Seasons;
- community persistent ecology;
- personal route/field-guide persistence only.

### Risk

Persistence can create infrastructure cost and undermine clean life resolution.

### Experiment

Prove the run structure first. Add persistence only for a specific player problem.

## 20. Decision priority

Resolve in this order:

1. movement feel;
2. first species and life loop;
3. world roaming and ecology readability;
4. session duration and death;
5. Lineage;
6. visual ceiling;
7. multiplayer;
8. monetization;
9. broader persistence/mobile.


---

# Eonwild Glossary

Status: **Canonical vocabulary**

## Animal embodiment

The combined perception of controlling a living body through locomotion, inertia, animation, camera, sound, contact, senses, and condition.

## Biomechanical family

A reusable engineering archetype containing skeleton, rig, locomotion grammar, contact model, procedural layers, compatible morphology envelope, and capability hooks. It is not identical to a taxonomic family.

## Capability

A data-driven interaction enabled by morphology, condition, relative physical state, and configured rules—such as brace, shove, pounce, or tail strike.

## Ecological pressure

A changing environmental or population condition that alters choices, such as drought, food decline, temperature, predators, competition, flood, or herd movement.

## Environmental character

A recognizable combination of environmental fields—such as upland forest, floodplain, wetland, or dry basin. It is descriptive, not a hard-coded level or zone.

## Evidence value

A scientific estimate, range, or claim with source and confidence.

## Gameplay value

The value used by the game after explicit tuning. It may differ from evidence but must not overwrite or masquerade as evidence.

## Full Season

Working name for a longer 30–50 minute life format with room for orientation, roaming, multiple encounters, crisis, and resolution.

## Group fidelity

Mid-distance ecology representation using a herd/pack centroid, population, composition, destination, and simplified behavior.

## Instinct sense

A restrained species-specific interface that amplifies information the animal could plausibly perceive. It is not omniscient wall vision.

## Life

One run/session representing a meaningful compressed period in an individual animal’s existence, often a defining season.

## Lineage

Persistent meta-progression awarded for meaningful animal behavior, ecological events, discovery, survival, and species mastery. It unlocks roles and knowledge rather than universal power.

## Near fidelity / individual fidelity

Detailed representation used near players: individual state, perception, animation, collision, interaction, injury, and local behavior.

## Paleo-documentary realism

Eonwild’s visual and audio direction: naturalistic, scientifically grounded where possible, atmospheric, composed like wildlife documentary imagery, and optimized without looking overtly simplified.

## Production-intent proxy

An asset or system more representative than a primitive fixture and suitable for evaluating product quality, but not necessarily final release content.

## Quick Expedition

Working name for a shorter 12–20 minute browser-friendly life with compressed pressure and complete resolution.

## Record fidelity

Far-world ecological representation storing population, approximate location, condition distribution, destination, resources, and threats without active individual actors.

## Roaming

Player-directed traversal and investigation with route choice, loops, backtracking, and off-attractor activity. It is more than movement between objectives.

## Scientific status

Classification of a claim as supported, plausible, disputed, speculative, or gameplay-only.

## Season

A dynamic period in which water, food, temperature, weather, herds, and hazards change. It is both ecological state and a useful session structure.

## Sidegrade

An unlock offering different strengths, costs, information, and gameplay rather than a universal increase in power.

## Suitability

A species-specific evaluation of a location based on resources, temperature, shelter, social attraction, danger, traversal cost, and other factors.

## Streamed cell

A technical partition for loading, rendering, navigation, authoring, or simulation. It must not be perceived as a level.

## Vista area

A deliberately composed high-value location or event stage receiving greater visual investment, such as a crossing, refuge, or overlook.

## World seed

The deterministic input controlling selected variations in environmental events, populations, timing, and scenario state while preserving geographic identity.


---

# Feature Design Review Checklist

Status: **Canonical review tool**

Use this before adding a feature to a sprint or accepting an autonomous design proposal.

## 1. Player problem

- [ ] What player experience or problem does this feature address?
- [ ] Is the problem evidenced by playtest, benchmark, or a canonical design requirement?
- [ ] Could a smaller change solve it?

## 2. Pillar alignment

- [ ] Does it strengthen animal embodiment?
- [ ] Does it strengthen ecological causality?
- [ ] Does it preserve roaming and route choice?
- [ ] Does it make a species meaningfully different?
- [ ] Does solo remain complete?
- [ ] Does it create stories rather than chores?
- [ ] Does it respect scientific uncertainty?

A feature need not satisfy every item, but it must not materially damage a pillar without an explicit accepted tradeoff.

## 3. Anti-goal check

- [ ] Does it avoid crafting/base-building drift?
- [ ] Does it avoid universal permanent power?
- [ ] Does it avoid quest-marker dependence?
- [ ] Does it avoid turning the world into a corridor?
- [ ] Does it avoid requiring populated servers?
- [ ] Does it avoid live-service chores?
- [ ] Does it avoid paid power?
- [ ] Does it avoid simulating detail the player cannot perceive?

## 4. Species and physical logic

- [ ] Is the feature expressed through morphology, ecology, capability, or runtime state rather than a literal species branch?
- [ ] Are relative mass, speed, stance, terrain, and target state used where relevant?
- [ ] Are body-family reuse and species-specific corrections visible?
- [ ] Does the action preserve commitment and mass?

## 5. Science and provenance

- [ ] Are claims sourced?
- [ ] Is uncertainty marked?
- [ ] Are gameplay interpretations separate?
- [ ] Are all visual/audio inputs licensed and recorded?
- [ ] Is protected reference content excluded from generation inputs?

## 6. World and ecology

- [ ] Does the feature create or respond to ecological state?
- [ ] Can the player ignore or approach it differently?
- [ ] Does it work across streamed cells?
- [ ] Does far/mid/near fidelity remain coherent?
- [ ] Does it conserve population and important state?
- [ ] Does it add meaningful route choice rather than a scripted path?

## 7. Session and progression

- [ ] Does it fit a Quick Expedition or Full Season without bloating the session?
- [ ] Is failure readable?
- [ ] Does it create fair Lineage events?
- [ ] Can it be farmed trivially?
- [ ] Does death remain consequential?
- [ ] Does it encourage replay rather than daily obligation?

## 8. UI and accessibility

- [ ] Can the world communicate the feature before the HUD?
- [ ] Is critical information available through more than one sensory channel?
- [ ] Is stronger assistance possible without redefining normal play?
- [ ] Are controls remappable and limited to a coherent action grammar?
- [ ] Is the feature understandable without a tutorial wall?

## 9. Platform and performance

- [ ] Does it work on the WebGL2 baseline?
- [ ] Is WebGPU enhancement optional?
- [ ] Are asset/download/runtime budgets defined?
- [ ] Are distant/invisible versions cheaper?
- [ ] Is Svelte kept out of per-frame entity state?
- [ ] Are benchmark and evidence requirements named?

## 10. Multiplayer and services

- [ ] Does solo still work?
- [ ] Is authority explicit?
- [ ] Does it require new backend infrastructure?
- [ ] Is the cost justified by validated demand?
- [ ] Does host departure have a graceful outcome?
- [ ] Does it create cheating or economic risk?

## 11. Commercial integrity

- [ ] Is the feature complete and enjoyable without paying for power?
- [ ] Is any ad placement outside active dramatic play?
- [ ] Are paid species sidegrades?
- [ ] Is accessibility not paywalled?
- [ ] Is the premium/free distinction additive rather than punitive?

## 12. Validation plan

- [ ] Unit/contract tests identified.
- [ ] Deterministic scenario identified.
- [ ] Performance metrics identified.
- [ ] Fixed-camera or video evidence identified.
- [ ] Perceptual-review rubric identified where relevant.
- [ ] Human playtest question identified.
- [ ] Stop/failure criteria identified.

## 13. Decision

- [ ] Accept for current sprint.
- [ ] Accept for backlog.
- [ ] Experiment first.
- [ ] Reject as misaligned.
- [ ] Requires game-design change proposal.

Record the evidence and reviewer responsible. The proposing agent may not be the sole approver.
