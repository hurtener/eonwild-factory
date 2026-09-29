# Eonwild factory working rules

Updated 2026-09-29 at the user's direction: Moco is paused; the shared procedural engine
(`src/eonwild_motion`, Unity `ConnectedMotionPlayer`) is the production path. Iterate fast.

## How to work

- Show motion early. Render both animals, watch the video at normal speed and frame-step the
  transitions, fix what you see, repeat. A good-looking clip beats a report.
- One coherent change per pass; both animals every pass; reject your own visual regressions.
- Never infer user approval. Say plainly what is reviewed, what is only measured, what is untested.
- Review the code you touch as you go (correctness, units, frames, edge cases) and fix real bugs.
- No subagents unless the user asks.

## Tests

- `pytest` runs the fast default set (about 1.5 min). Tests listed in `tests/slow_tests.txt`
  are marked `slow` and skipped; run everything with `pytest -m ""` before merging.
- Test behaviour and invariants (continuity, contact, reach, determinism), not golden bytes or
  exact floats. Do not add hash-pinned outputs; replace them when they break.
- Don't write tests for one-off diagnostics or documents.

## Motion rules that stay

- Species differences live in profile/semantic data (mass, strength, stance, stride, ranges),
  never species branches or literal bone names in shared code.
- A behaviour owns its contact choreography. No root teleport, silent foot sliding, stretched
  bones, or render-only clamps that hide a solver problem.
- Re-apply floor, contact and reach constraints after any posture or stance change; move between
  stances through contact choreography, not a pose pop.
- Scientific claims need a source; otherwise label values as authored estimates.
- A Unity root has one movement owner; world logic, not animation cues, decides bites and damage.
- Don't overwrite clips the user approved; write new versions beside them.

## Where things go

- Shared code: `src/`, `tools/`, `tests/`; versioned recipes and profiles: `catalog/`.
- Scratch runs and frames: task storage `research/`. Selected clips go in a new
  `game/Assets/Eonwild/<Name>` folder; review videos in `game/Evidence/<name>/`.
- `build/`, `reports/`, `legacy/` are history, not runtime inputs.

## Inputs and outputs

- Recipes may bind inputs as {path, sha256}. A changed input is used with a one-time note;
  `EONWILD_STRICT_HASHES=1` makes mismatches fail again (e.g. to reproduce an old take exactly).
- Re-running a build replaces its output; the previous output is kept once as `<name>.prev`.
- `factory verify` on a finished package stays strict (it exists to detect corruption).
