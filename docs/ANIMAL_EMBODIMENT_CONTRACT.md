# Animal embodiment profile v1

Canonical files: `catalog/embodiment/allo.v1.json` and `tarbo.v1.json`. These consolidate the approved consumer mappings and settings without changing approved locomotion packages. The shared code stays in `src/eonwild_motion`; there is no new versioned toolkit.

## Authority

This document is the central ownership index. There is not yet one editor or a
single authoring path covering every historical motion family.

| Concern | Editable authority | Consumers / records |
| --- | --- | --- |
| Animal anatomy, semantic bindings, capability and attention numbers | Factory `catalog/embodiment/{id}.v1.json` | Unity `Motion/{id}.profile.json` is an exported copy; candidate profile snapshots preserve provenance |
| Shared attention law and named glance intents | `src/eonwild_motion/attention.py` | Unity's port is checked against exported reference vectors |
| Action choreography and choice of attention intent | `catalog/behaviors/` and shared planners | A behavior selects normal/scan/strong/exceptional; it does not copy animal range numbers |
| Neck research interpretation and citations | Factory `docs/research/THEROPOD_NECK_BASELINE.md` | The game copy is a reference mirror; the original user report is archival evidence |
| Artistic direction | Principal game `docs/ANIMATION_ART_DIRECTION.md` | Guides all authoring and visual reviews |
| Side-impact checkpoint 24 | Principal game `docs/SIDE_IMPACT_RECOVERY_SPEC.md` | Detailed intent and delivered-scope record; profile and recipe remain tuning authority |
| Acceptance and reproducibility | Roadmaps and immutable checkpoint evidence | Historical numbers describe that take; they are not tuning inputs |

Change numerical intent once in the Factory profile, regenerate affected motion,
export to consumers, and review both animals. Do not independently tune copied
Unity profiles, research tables or old receipts. The two repository roadmaps track
their own delivery state and link to evidence; they are not parallel parameter
stores. Legacy compiler migration and consolidation of review tooling remain debt.

An animal profile is the editable entry point for semantic bindings, calibrated axes, sequence timing, attention and secondary-motion settings. `authoring` preserves the original animal-instance evidence, approved emitted gait parameters and original intent references. Historical recipes remain reproducibility inputs, not editable game copies. This checkpoint does not replace every historical compiler configuration format or automatically admit new topology.

`tools/export_embodiment.py` validates required/unique roles, available nodes, finite values, explicit unit axes, sequence intervals and the motion SHA-256, then exports exact profile bytes and Python numerical reference vectors. Consumers receive files; they do not import Factory Python at runtime. Keep profile version, asset hashes and evidence together.

## Frame and law

Profiles describe admitted metre/second glTF assets, right-handed +Y up/+Z forward, xyzw quaternions. Joint `axis` is a local right-handed angular vector. Unity position reflection negates X; angular-vector reflection negates Y/Z. New source frames must be normalized during admission.

The `eonwild.secondary.v1` state is elapsed time, walk intensity and one response value per configured joint, initially zero. Each nonnegative finite time step:

- Walk intensity approaches clamped speed/full-walk-speed with exponential response `1-exp(-dt*walkBlendRate)`.
- Each arm response approaches clamped foot-separation signal times its authored sign, with `1-exp(-dt/max(0.03,responseSeconds))`.
- Jaw/arm breath contribution is `0.5-0.5*cos(elapsed*2*pi/breathPeriod+phase)`.
- Local angular offset is rest + breath contribution + (for arms) walk range × walk intensity × response.
- Apply the offset after source sampling; restore previous offsets before the next source sample. Pausing advances no state. Jaw rhythm intentionally continues through stops.

`src/eonwild_motion/embodiment.py` is the reference evaluator. Unity's numerical adapter must pass the exported reference vectors, including variable time steps, pauses and settling. The scene adapter binds transforms; it does not contain animal names or derive articulation from bone naming patterns. Attention target choice remains a game responsibility and is outside the secondary preview bake.

Arms may be empty. `hasJaw: false` disables the jaw layer. Required grounded-biped and attention roles remain mandatory; unsupported families require explicit shared implementation rather than silent fallback.

## Blender and new animals

`tools/bake_secondary_preview.py` takes an immutable exported clip plus a profile and produces a NEW preview GLB. It retains all non-secondary animation channels and adds the Python-evaluated local rotations for configured joints. Blender can import/play that GLB. This is an offline consumer preview, never source material for generating locomotion and never a production-contact certificate.

New animals require admitted geometry, skinning and semantic mappings; measured local joint axes; documented stride/proportion evidence; authored limits; a compatible shared locomotion family; an immutable generated motion package; profile export; and native-time review of that real rig. A renamed fixture proves naming independence only.

Focused checks: `PYTHONPATH=src python -m pytest tests/test_embodiment.py -q`. Export/bake tools expose their arguments with `--help`. Runtime/Blender evidence and the detailed onboarding guide are maintained in the principal Eonwild game repository under `docs/ANIMAL_PROFILE_ONBOARDING.md` and `game/Evidence/animal-profile-housekeeping/`.


## Locomotion capabilities v1 — checkpoint 11

The optional `locomotion` section extends the same embodiment profile. The approved walk source, stride intent, rig bindings and secondary-motion law remain intact. `planning/locomotion_capabilities.py` resolves explicit-unit values and provenance to effective motion limits. Changing an animal name has no effect; changing its numerical inputs does.

| Input | Resolution / use | Evidence status |
|---|---|---|
| Existing body mass | Effective horizontal force / mass gives acceleration and braking limits | Published estimate already in animal instance |
| Yaw inertia | Effective torque / inertia gives angular acceleration and braking; also drives tail response time | Published specimen/composite estimate; mesh correspondence remains unverified |
| Ilium area / yaw inertia | Separate research turning proxy | Published-model proxy, never converted directly into playback speed |
| Forward, braking, lateral force; yaw driving/braking torque | Independent control budgets, multiplied by selected effort | Authored effective budgets, not reconstructed muscles |
| Preferred / maximum grounded speed and maximum step frequency | Resolve speed and cadence while preserving step and same-foot stride | Authored low-speed intent, not sprint-speed claims |
| Traction coefficient | Caps horizontal acceleration; lateral budget also limits yaw rate at speed | Authored flat-ground assumption |
| Effort, turn cadence multiplier, heading per step, attention lead | Select a response within capability; add support steps when needed | Authored style |

Each input has value, unit, classification and source. The dimensionless agility components summarize linear acceleration/braking/lateral capacity relative to g and turning relative to g/(1 metre). These are engine summaries; the published area/inertia index is kept separately and retains its cm²/(kg m²) convention. Never merge these into one universal agility score.

`resolve_walk` returns requested/resolved speed, preserved stride and cadence. `advance_walk_speed` applies separate forward/braking budgets. `yaw_rate_at_speed` provides the speed-dependent lateral limit. `plan_directional` uses the same choreography and fits travel/heading rates and accelerations to these budgets, before actual-rig IK and contact correction. It regenerates poses rather than retiming an existing clip. Foot anchors and outside-first stepping remain behavior-owned.

Scope: the fit constrains the **locomotion path**, excluding the additional local support/pelvis accommodation. It is NOT final whole-body COM dynamics, segment force balance, muscle/tissue stress validation, or final material contact locking. Those remain the next polishing work. Walking capability resolution is implemented and tested; the approved straight-walk packages are unchanged and have not been regenerated with these profiles.

The current Allosaurus proxy uses the 1512 kg composite row, yaw inertia 2303.25 kg m² and ilium area 1131.5 cm². Tarbosaurus uses PIN 552-1, 2816.3 kg, 4486 kg m² and 2977 cm². Source: [Snively et al. 2019, Table 3](https://pmc.ncbi.nlm.nih.gov/articles/PMC6387760/). Force/torque settings are independently authored; they are not inferred from the research index. [Dececchi et al. 2020](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0223698) informs the distinction between locomotor economy, body size and top speed. No Tarbosaurus sprint speed is claimed.

Export with `tools/export_embodiment.py`; it now adds resolved capability JSON to the existing profile and secondary vectors. Directional generation accepts `--profile catalog/embodiment/allo.v1.json` (or another admitted profile), binds the source geometry/calibrated height, and emits the profile snapshot, resolved limits, fit receipt and motion hashes alongside the GLB. `source-animal.profile.json` is the original authoring snapshot, whose source hash still identifies the approved walk; `resolved-capabilities.json` binds the new directional GLB explicitly. Unity consumes this immutable export; its review player displays the resolved budgets and does not add another root movement owner. Live gameplay control integration is a later checkpoint.

### Future animals

Start with an admitted rig/profile, documented mass, limb dimensions and step/stride. `tools/seed_locomotion_capabilities.py --target TARGET --reference REFERENCE --output NEW_PROFILE` generates an explicitly unreviewed similarity prior. Length comes from hindlimb measurements; inertia scales by mass ratio × length ratio², force by length ratio², and torque by length ratio³. All inherited/scaled values are relabeled derived estimates with reference hashes. These assumptions are a starting point, never new biological measurements. Replace them with specimen evidence or deliberate calibration, regenerate both the new animal and a reference animal, inspect every rendered frame, and review native-time motion. Unsupported body families still require shared implementation.


## Turn support response — checkpoint 12 visually accepted

`solve/turn_support.py` uses the behavior's contact schedule to plan continuous normalized load shares; an airborne foot carries zero. `turn_load_response` in the shared directional recipe sets transfer width, maximum roll and response scale. The offline response time is `response_scale * sqrt(body_height / effective_lateral_acceleration)`, where the profile resolver supplies effective force/mass. Symmetric filtering prepares for known future support; it is not a causal runtime controller or measured ground-reaction force.

A pelvis roll preserves the load-weighted hip height before the shared leg IK. `turn_load_response.v1` uses the existing body-support control interface with a source/recipe/capability SHA-256 binding. Foot contact is corrected afterwards: freeze the admitted material subset's horizontal centroid for each planted interval, solve vertical floor and tangential offsets, and release the accumulated tangential offset into early recovery. Exported assets are reopened at every source key; receipts distinguish centroid drift from maximum per-vertex deformation.

This adds no species branch, edits no approved straight-walk asset, and does not establish whole-body force balance, joint stress, rigid full-patch locking or continuous-time contact acceptance. See the current roadmap and principal game checkpoint 12 evidence before promotion.


### Profile-relative walking curves (checkpoint 13)

`plan_directional` also accepts `step_scale_of_normal` per behavior block, resolving it against the profile's documented one-step distance. It is mutually exclusive with `step_length_body_heights`; resolved metres remain in the receipt. `speed_scale` selects an initial average timing below the preferred walking speed, followed by the existing cadence/acceleration/turn budget fit. It is not a strict instantaneous speed multiplier through the acceleration ramp.

The separate `walking-curve-review.v1.json` recipe chooses shorter steps for tighter slow turns without changing the canonical normal stride. Its optional `walking` policy controls smooth travel ramps, anticipatory heel preparation and low outward recovery. Existing pivot recipes retain their prior law. Generation accepts `--recipe` with `--profile`; profile-relative steps require a profile. The resulting clips are offline authored curves with settling between blocks, not an online steering controller. Native videos and unresolved material contact are recorded in the game evidence package.


### Combined walking-turn recovery (checkpoint 14, timing polish requested)

Checkpoint 13 was rejected for missing walking articulation. `walking-curve-review.v2.json` opts into `walking.articulation_source: admitted_grounded_walk`. The builder resolves heel pitch and clearance from the admitted gait, reuses `grounded_swing_articulation` and `declare_pad_recovery_sample`, and applies authored per-block articulation/clearance scales. Directional choreography still owns support, path, foot yaw and heel timing. Metatarsal direction, recovery timing, pad and digit settings remain in the admitted motion program. Ordinary gait sampling is preserved; no prior animated take supplies timing or joint trajectories.

Both actual rigs have new native videos and every-frame inspection in principal game `game/Evidence/articulated-walking-curve-study/`. User retained the direction and requested unloading/recovery timing polish. Final material contact remains open. Keep accepted in-place turns and straight walks separate from this unapproved candidate.

### Overlapping walking release (checkpoint 15 candidate)

Recipe v3 opts into `walking.recovery_timing: overlapping_walk_release`, with `heel_peak_swing_fraction: 0.10` and `heel_release_swing_fraction: 0.40`. The builder resolves `rounded_swing_peak_fraction` from the admitted gait. Heel pitch continues increasing through the support-to-swing boundary while the free-foot lift ramps into recovery. These timings are authored shared behavior data, not new animal-specific anatomy or measured biological facts. Existing pivot recipes retain their law. Contact times, path and load scheduling are unchanged from checkpoint 14.

Both emitted rigs have native videos and every-frame inspection in `game/Evidence/continuous-walking-release-study/`. Earlier flexion is more pronounced; user review remains pending. This is timing polish and does not close final force/contact acceptance.

### Purposeful walking response (checkpoint 16 candidate)

The shared walking_response module defines a compact recovery window and independent moving articulation gain. The v4 walking-curve recipe derives swing and heel preparation durations from resolved normal step cadence, preserving the capability-limited body path. Foot sampling, pelvis shift and support loads consume the same window.

The walking-response-review.v1 recipe opts the connected straight sequence into a 0.9-step body response and 0.85 moving articulation floor. These are shared authored controls; numerical capability acceleration enforcement and revised whole-body force solving for the straight sequence remain pending. The normal steady gait and approved exports are unchanged. The builder's --response-recipe selects the candidate; default generation retains the preceding law. New contact evaluation and reopened measurements accompany the candidate.

### Walking-curve knee flexion reserve (checkpoint 17 visually accepted)

`walking-curve-review.v5.json` owns the optional authored `walking.knee_extension_preference_degrees` value, currently 155 degrees for both animals. The directional adapter passes this into the shared pose solve as `walking_knee_preference_degrees`. A continuous quartic cost above the preference redistributes sagittal articulation without changing the existing hard ROM, segment lengths, contact schedule or pelvis path. The same control applies across support and recovery to avoid a contact-switch discontinuity. Omission preserves preceding recipes. This is a behavior preference, not a newly measured animal limit; profile hard constraints retain priority.

Use `tools/measure_directional_joint_angles.py --package <candidate> --output <new-receipt.json>` to reopen the final hash-bound GLB with its semantic profile and measure keys plus midpoints. Zero reach overflow alone missed the checkpoint 16 Allosaurus knee approaching 180 degrees. The new evidence is diagnostic, not continuous-time ROM, Unity skin parity or whole-body force certification.


### Backward locomotion (checkpoint 18 candidate)

`reverse-walking-review.v1.json` declares `travel_direction: backward`, positive profile-relative step magnitudes and the `backward_grounded` articulation source. `plan_directional` resolves a negative displacement and preserves the original onboarded normal step intent. The first review supports straight retreats only; ambiguous absolute distances and forward-articulation policies are rejected. Animal acceleration and cadence budgets constrain timing, while reverse-specific step/speed fractions remain explicitly authored estimates.

The reverse module owns toe curl, metatarsal pitch preference and a bounded attention cue. The same semantic rig, limb solver, knee flexion preference, support-plane accommodation, load response and material correction are reused for both animals. No animal profile or approved take is changed. The Unity diagnostic selects the new immutable exports with `-reverse`, optionally `-capture-allo` and `-three-quarter`; one sampled root still owns movement.


## Profile-owned attention envelope — checkpoint 19

Read [the neck baseline](research/THEROPOD_NECK_BASELINE.md) and preserve its evidence classes when
onboarding or extending a motion family. attention.envelope stores explicit
whole-head degree ranges, ordered semantic neck weights and provenance. The
reference law is src/eonwild_motion/attention.py; the optional contract preserves
historical profiles. New profiles must select their envelope deliberately.

Export adds hash-bound attention-vectors.json. Unity AttentionLaw matches the
Python saturation; its scene layer applies profile weights and compensates existing
source yaw so the requested gaze is not added twice. Grounded directional exports
bake bounded attention before final contact correction. Each exported candidate
retains its original profile snapshot and must reopen its head/torso heading with
tools/measure_attention_envelope.py. This does not certify arbitrary source poses
or maximum-range soft-tissue behavior.

No automatic body/root motion is added: body-follow output requests a separately
coordinated turn. Ordinary cap is 80 degrees Allosaurus / 60 Tarbosaurus;
exceptional cap 85 / 65 requires explicit selection. Numerical settings are
reconstruction estimates, not direct biological measurements. Coupled roll/pitch
and older authoring paths remain separate migration work.

## Lateral recovery — checkpoint 21

The lateral recovery recipe owns a broad stance, semantic travel-side opening,
follower placement, modest toe release and recovery height. Its single stance-width
value is lateral.stance_width_body_heights; do not duplicate it in turn settings.
The profile remains authoritative for mass, effective lateral force, cadence and
attention range. The lateral planner consumes force per mass and cadence to select
a period, then uses the shared directional support/event interface and leg/contact
solvers. It adds no species branches.

The result is a planned open-and-follow adjustment, not a simulated shove, COM
feedback controller, slip detector or terrain response. The pelvis trajectory and
load shares remain authored kinematics. Preserve the approved walking, turning
and ordinary/exceptional glances. Checkpoint 21 lateral visual review is accepted; production acceptance remains pending.

### Received side-hit recovery (checkpoint 22)

Behavior authority is `catalog/behaviors/stumble-recovery-review.v1.json`.
The `impact` section owns broad stance, reaction/settling times, per-pair reach
and compliant pose envelopes. Blocks supply received impulse in N s and the
semantic travel side. The shared planner divides received impulse by the victim
profile's mass and estimates braking distance with its lateral acceleration;
that estimate chooses catch count/placements. Effective impulse transfer from an
attacker, contact height/angular impulse, live state-dependent balance, falls,
terrain and arbitrary incoming velocity are not implemented. Do not present
the finite authored recovery envelope as a physics or biological threshold.

The Unity viewer consumes a baked result and an optional diagnostic
`*.review.json` impact timeline. This file annotates the capture only; it owns no
movement, damage or animal tuning. Profile files are unchanged. A reusable
Python behavior exists; interactive Unity dispatch/parity is still pending.

### Immediate curved impact (checkpoint 23 candidate)

The current candidate authority is `catalog/behaviors/stumble-recovery-review.v2.json`;
v1 remains the checkpoint 22 revision reference. The behavior owns an explicit
catch recovery window, no-prehit load release boundary, earlier swing travel,
and per-catch duration scales. `support_transfer_times` aligns planner weights
and contact loads. Defaults preserve other walking/turning policies.

`reaction_seconds` controls first event onset. `braking_delay_seconds` belongs to
the authored stopping-distance estimate and is not a second foot-reaction delay.
`catch_duration_scales` multiplies the ordinary profile-derived base period;
this emergency burst is authored and does not change the canonical animal's
normal cadence. The capability receipt's `stepSeconds` remains that unscaled
base period; actual event timing is in the evidence measurements summary.

Chest yaw is distributed through semantic spine joints before shared limb solve
and final contact correction. Head attention retains profile bounds; tail lag
completes the side bend. Lower clearance and vertical compression avoid the
first draft's Allosaurus ankle snap. No animal names or literal bone names enter
the shared policy. Final source-rig measurements and every captured frame were
reviewed; user approval and full physical/contact acceptance remain pending.

### Support-dependent impact response (checkpoint 24 candidate)

Select `impact.response_model: support_coupled` in the v3 behavior recipe.
Legacy impact recipes retain their original planner. The shared
`planning/impact_response.py` integrates body offset/velocity, yaw/rate,
contact/load state and five response channels at 240 Hz. Finite horizontal
impulse and yaw lever arm use canonical mass and yaw inertia. Effective support
reactions use canonical acceleration budgets; contact acceptance changes braking.
This is a reduced model with authored vertical compliance.

Optional canonical `impactResponse` profile data owns application-landmark
fallbacks, response times, regional bend and secondary-motion ranges. Every new
value is labeled authored. The real-rig producer maps chest/pelvis through
semantic bindings and records the resolved point in metres; it does not branch
on animal names. The v3 recipe owns event cases, reaction/acceptance timing,
placement limits, entry gait and ready stance. Profile copies in Unity are
immutable export snapshots.

Walking entries reuse current foot position, derivatives and swing phase.
A committed catch curve targets support; remaining placements respond to
residual body motion. Exit receipts preserve velocity, anchors, support shares,
heading, channels and a known threat target. They do not infer injury.

Secondary motion is baked before final contact correction. The diagnostic Unity
timeline declares `secondaryBaked` so playback does not apply it twice. Timeline
hit/target markers annotate the review; they never own root motion or gameplay.
Unity plays the emitted clip with one root owner. Live collision and arbitrary
runtime state transfer are not implemented.

The principal game's `docs/SIDE_IMPACT_RECOVERY_SPEC.md` records the detailed
intent and bounded implementation. Evidence under
`game/Evidence/support-coupled-impact-study/` includes final GLB identities,
profiles, recipes, contact/joint/attention/body traces and all-frame review.
User approval and production force/material-contact certification remain pending.


### Profile-owned running posture — checkpoint 35

A running recipe may opt into `posture_from_profile: true`. The shared resolver
then reads `locomotion.run.posture.frontBodyPitch` when present; otherwise the
recipe posture remains authoritative. The quantity requires a finite numeric
`value`, `unit: "deg"`, and a nonempty `source.citation`, within the existing
0–20 degree front-body pitch range. Positive pitch lowers the front; reducing
it raises chest and corresponding head carriage. Keep authored provenance clear.
The current Tarbosaurus candidate uses zero degrees. This field is an authored
posture preference, not a measured range of motion. Recipes without opt-in are
unchanged, and final rig articulation constraints still apply.
