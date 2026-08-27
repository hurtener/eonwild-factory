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
