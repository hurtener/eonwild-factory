# Proposed Repository Edits

This file summarizes the small existing-file changes recommended when integrating the game bible.

## `AGENTS.md`

1. Add `docs/game/README.md`, `00-game-vision.md`, `01-design-pillars-and-invariants.md`, and the relevant game-system doc to Required reading.
2. Add the product-intent conflict rule from `INTEGRATION_GUIDE.md`.
3. Add a stop condition when a task would permanently change game intent without a GDCP.

## `README.md`

1. Add a “Game design bible” section.
2. Keep technical RFC links.
3. Clarify that sprint scope is temporary and the game bible is durable.
4. Consider renaming the top-level README title after Week 1/2 when the repo is no longer primarily a kickstart pack.

## `config/project.yml`

Add references to:

- product name `eonwild`;
- `docs/game/README.md`;
- `config/game-design.yml`.

Keep the internal ID unchanged until its usage is audited.

## `config/ownership.yml`

Add an owner/reviewer rule for `docs/game/**`, the game-design config/schema, and GDCP template.

## Weekly handoffs

Add a “Product-intent review” section listing canonical docs, invariants, open decisions, and temporary assumptions.

## Validation mapping

Map:

```text
config/game-design.yml -> schemas/game-design.schema.json
```
