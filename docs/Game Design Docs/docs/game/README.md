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
