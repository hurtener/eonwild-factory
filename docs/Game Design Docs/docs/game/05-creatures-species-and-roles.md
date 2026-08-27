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
