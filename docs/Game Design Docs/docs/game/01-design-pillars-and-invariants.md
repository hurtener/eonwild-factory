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
