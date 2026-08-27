# Eonwild Game Design Bible — Repository Pack v1

This pack captures the game Eonwild is intended to become. It complements the existing technical constitution, asset-factory RFCs, sprint plans, and handoff reports.

The central separation is:

- `docs/game/` owns **what the game is and what experience it promises**.
- Existing technical RFCs own **how the current implementation satisfies that promise**.
- Sprint plans and handoffs own **what is being attempted now**.

A sprint handoff may narrow scope temporarily. It must not silently redefine the product.

## Proposed repository additions

```text
docs/game/
  README.md
  00-game-vision.md
  01-design-pillars-and-invariants.md
  02-player-loop-and-session-structure.md
  03-world-continent-and-roaming.md
  04-ecology-migration-and-ai.md
  05-creatures-species-and-roles.md
  06-survival-senses-hunting-and-injury.md
  07-lineage-progression-and-unlocks.md
  08-modes-multiplayer-and-social.md
  09-art-direction-and-visual-language.md
  10-audio-and-sensory-design.md
  11-ui-ux-field-guide-and-accessibility.md
  12-science-setting-and-world-fiction.md
  13-platform-distribution-and-business-model.md
  14-content-scope-and-release-roadmap.md
  15-example-player-stories.md
  16-open-decisions-risks-and-experiments.md
  17-glossary.md
  18-feature-design-review-checklist.md
config/game-design.yml
schemas/game-design.schema.json
templates/GAME_DESIGN_CHANGE_PROPOSAL.md
```

## Status model

- **Canonical** — already agreed and should not be changed by a sprint task.
- **Working direction** — strong direction, but requires playtest or commercial validation.
- **Open decision** — intentionally unresolved; agents must not invent a final answer.

## Installation

Read `INTEGRATION_GUIDE.md`. Copy the files into matching repository paths, apply or manually reproduce the small README/AGENTS changes, validate `config/game-design.yml`, and regenerate the repository manifest.
