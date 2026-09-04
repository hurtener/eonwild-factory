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
