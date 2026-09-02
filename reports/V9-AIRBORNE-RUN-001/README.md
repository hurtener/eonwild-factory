# Airborne Run — USER-ACCEPTED NEW BASELINE

**The user explicitly accepted the original iteration006 `feasible-recovery` full-body preview as the new Run baseline.** Motion polish and reference-performance matching remain pending: chest liveliness, tail compensation, buoyancy, and less aggressive leg motion require the separate full-sequence reference analysis before curve changes. This visual acceptance does not establish physical accuracy, true ground-contact velocity, or Sprint readiness.

Accepted artifact directory: `build/V9-AIRBORNE-RUN-001/iteration-006-anatomical-knee/feasible-recovery/`.
Frozen profile: that directory's `engineering-profile.json`.
Accepted preview: `airborne-run-fullbody-side-2cycles.mp4` (native1.25 s cycle repeated once, no retiming).
Root-motion SHA256: `0a470d35ce3c0b15e3f5d8af0a54cf09cb50783bdb7c117d1141a192c4a7b0da`.
In-place SHA256: `57f4891e1ce5f785a0975a3ff9b76cc256719e4b20948fa0d3468e01e44f8ada`.

The subsequent `feasible-recovery-exact-pitch` numerical variant remains **unpromoted**. All13 airborne tests pass after its local precision correction; comparison found identical timing/translations, maximum rotation difference0.004859°, and maximum semantic leg-joint displacement44 µm. The accepted artifact/profile/media bytes were not replaced. Actual ground-contact velocity remains unknown/null: the reported0.43–0.79 m/s peaks were proximity deformation9.81–20.08 mm above the fixed floor during push-off.

## Historical rejected005 evidence

**005 was visually rejected by the user for a knee-branch glitch and severe hip/knee skin collapse.** All005 technical checks below are historical only and do not establish visual viability. Its artifact directory is `build/V9-AIRBORNE-RUN-001/iteration-005-centered-push-off/`. Main profile `profiles/v9/program.airborne-gait.run.json` remains the historical005 binding; the accepted006 profile above is the authority for the new baseline. Accepted Walk and all prior artifacts remain untouched.

### Historical005 motion and evidence

- Full-body side preview: `airborne-run-fullbody-side-preview.mp4` (1100×620, 24 fps, 60 frames / 2.5 seconds). Camera fits the union of all 60 frames.
- One rotation-solved root-motion authority, with an in-place projection derived from exactly the same body channels. Leg local translations/scales are not animated to create reach.
- Step period 15/24 seconds, four-frame flight per step, full same-foot period 30/24 seconds. These are engineering seeds informed by variable V07 timing (14–17 frames), not claims that the source is exactly periodic.
- Same-frame distal-toe split: **3.388 m / 0.283 body lengths**. Signed reaches around actual hip center at that frame: **−1.737 m / +1.651 m**. Reference Run’s approximately 0.296 body-length single-frame split is an uncertain 2D silhouette witness, not the same marker contract.
- Separate per-foot root-relative excursion: **3.565 m / 0.298 body lengths**, versus current Relaxed/Fast Walk **2.101 m / 0.176 body lengths**. The rejected small Run smoke002 had only 1.662 m excursion.
- Run crouch is 0.08 body heights; push-off pitch and recovery pitch are independently parameterized. Earlier lift and later lowering produce a visible brief flight without increasing pelvis bounce.

### Historical005 focused gates and remaining caveat

`solve-receipt.json` measures reopened float32 GLB output: no unreachable extension, maximum foot target residual below 0.000001 m, planted distal-joint velocity below 0.0001 m/s.

`final-skinned-ground-receipt.json` uses the existing multi-influence skin adapter and unchanged accepted source floor: zero foot penetration, zero missed planned stance contacts, and 68 interior-flight samples with zero ground intersections.

The historical bottom-patch speeds (3.089 m/s overall,0.790 m/s in a3 mm relative band,0.430 m/s in0.1–1 mm bands) were not measurements at the actual fixed ground plane. The later006 classification demonstrates why a band relative to a lifted surface must not be called ground slip. The floor/flight pass does not assert no-skate or physical-contact acceptance.

## Reusable paths

- `src/eonwild_motion/planning/airborne_gait.py`: independent airborne plan, normalized parameters, explicit static stance/flight schedule, phase-continuous targets.
- `src/eonwild_motion/solve/airborne_gait.py`: semantic, geometry-derived leg/toe rotational solves; reopened output and final-skinned metrics.
- `tests/test_v9_airborne_gait.py`: duty/flight, contact transitions, emitted parameter mutation, renamed/scaled binding, unchanged limb translations, and active-surface versus lifted-patch velocity tests.
- `build_airborne_run.py`, `evaluate_skin.py`, `measure_stroke.py`, `render_side_preview.py`: task-local entry points. Grounded alternating gait was not weakened.

Focused test command: `PYTHONPATH=src .venv/bin/python -m pytest tests/test_v9_airborne_gait.py tests/test_v9_alternating_gait_regime.py -q`.

## Historical 005 input configuration

The frozen005 GLBs remain the historical authority for that rejected result. The solver is now being corrected for006, so running these old inputs through the new solver does not reproduce005. Run from the repository root into a new output folder only.

```sh
PYTHONPATH=src .venv/bin/python reports/V9-AIRBORNE-RUN-001/build_airborne_run.py \
  --source build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/narrow-gauge-walk-root_motion.glb \
  --source-clip PROC_WALK_RELAXED_V8_1_RESPIN_ROOTMOTION \
  --binding catalog/rigs/hero-theropod-v8_3.semantic-rig.json \
  --profile build/V9-AIRBORNE-RUN-001/iteration-005-centered-push-off/engineering-profile.json \
  --contact-profile build/V9-NARROW-GAUGE-WALK-002/sweep-run-016-v4-skinned-authority/sweep-0p34000000000000002-fa4aa9445c12/candidate-contact-profile-root_motion.json \
  --output build/V9-AIRBORNE-RUN-001/iteration-005-replay
```

The source clip and source-floor binding above are exact. Main profile `parameters` were checked equal to the frozen iteration's `engineering-profile.json`.
