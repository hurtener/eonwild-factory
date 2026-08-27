# Integration Guide — Eonwild Game Design Bible

## 1. Current repository assessment

The current repository already has a solid partial definition of Eonwild:

- `docs/00-product-and-technical-constitution.md` contains the product thesis, world invariant, experience pillars, architecture, sprint scope, and demo statement.
- `docs/02-world-streaming-rfc.md` preserves the non-corridor continuous-world design.
- `docs/03-biomechanics-and-species-architecture.md` preserves family/species composition.
- `docs/05-demo-quality-bar.md` defines initial experience and performance gates.
- `config/project.yml` records key product constraints in machine-readable form.

What is missing is a comprehensive durable description of the game beyond the current factory/demo milestone: session structure, Lineage, survival and hunting rules, role roster, multiplayer shape, art/audio language, UI/field guide/accessibility, fictional/scientific framing, commercial direction, roadmap, stories, and open decisions.

## 2. Copy files

From the pack root:

```bash
cp -R docs/game <repo>/docs/
cp config/game-design.yml <repo>/config/
cp schemas/game-design.schema.json <repo>/schemas/
cp templates/GAME_DESIGN_CHANGE_PROPOSAL.md <repo>/templates/
```

Do not overwrite existing technical RFCs.

## 3. Update `AGENTS.md`

Add to Required reading before the technical constitution:

```text
1. `docs/game/README.md`
2. `docs/game/GAME_OVERVIEW.md`
3. `docs/game/00-game-vision.md`
4. `docs/game/01-design-pillars-and-invariants.md`
5. The game-system document relevant to your task
6. `docs/00-product-and-technical-constitution.md`
...
```

Add a product-intent rule near Hierarchy of truth:

```text
The schemas/configuration remain executable truth for implemented contracts.
`docs/game/00-game-vision.md` and `docs/game/01-design-pillars-and-invariants.md`
are canonical product intent. When implementation contracts cannot satisfy a
product invariant, stop and raise a conflict; do not silently redefine the game.
Sprint plans and handoffs may narrow scope but may not permanently change product
intent without an accepted game-design change proposal.
```

## 4. Update repository `README.md`

Add a section near the canonical design sources:

```markdown
## Game design bible

The durable product definition lives in [`docs/game/README.md`](docs/game/README.md).
It defines what Eonwild is: player fantasy, session structure, world/ecology,
species roles, survival, Lineage, multiplayer, art/audio, UI, scientific framing,
commercial direction, roadmap, and open decisions.

Technical RFCs define implementation. Sprint plans and handoffs define current
scope; they must not become the only source of product intent.
```

The repository title can later change from “Dinosaur Game Asset Factory Kickstart Pack” to an Eonwild project title when the team wants the repository to present as the product rather than the bootstrap pack.

## 5. Update `config/project.yml`

Recommended additive fields:

```yaml
project:
  product_name: eonwild
  game_design_bible: docs/game/README.md
  game_design_summary: config/game-design.yml
```

Do not silently rename `project.id: paleo-lineage` if it is already used by scripts, manifests, or caches. Treat that as a separate migration decision.

## 6. Validation

Add `config/game-design.yml` to the existing YAML/schema validation mapping using `schemas/game-design.schema.json`.

Minimum checks:

```text
- YAML parses
- schema validates
- all docs/game paths in the index exist
- required canonical docs are linked from AGENTS.md
- handoff templates reference product invariants
```

## 7. Handoff template additions

Every weekly handoff should include `templates/HANDOFF_PRODUCT_CONTEXT.md`, or an equivalent section containing:

```markdown
## Product-intent review

- Game-design documents consulted:
- Canonical invariants affected:
- Open design decisions touched:
- Temporary milestone assumptions:
- Any proposed permanent change:
- Game-design change proposal ID, if applicable:
```

This prevents temporary prototype choices from becoming accidental permanent design.

## 8. Sprint plan additions

Each task that changes gameplay should identify:

- owned game-design document;
- pillar(s) strengthened;
- open decision being tested;
- player-facing validation question;
- whether the result is a temporary experiment or candidate canonical direction.

## 9. Manifest and CI

After adding files:

- regenerate `MANIFEST.sha256` using the repository’s canonical command;
- run contract validation;
- run `make verify` or the current accepted clean-checkout gate;
- require an independent documentation/product review;
- merge through the normal WS00/integration path rather than bypassing sprint ownership.

## 10. Suggested ownership

Create a small product-design ownership rule, for example:

```text
docs/game/**                     product/game-design owner
templates/GAME_DESIGN_CHANGE*    product/game-design owner
config/game-design.yml           product + integration review
schemas/game-design.schema.json  schema + product review
```

Implementation agents may propose edits through a report or GDCP. They should not rewrite canonical product intent opportunistically during technical work.
