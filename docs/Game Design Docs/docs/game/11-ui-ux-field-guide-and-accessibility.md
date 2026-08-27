# UI, UX, Field Guide, and Accessibility

Status: **Canonical principles**, working direction for final interface design.

## 1. UI philosophy

The world should communicate before the HUD does.

The interface should help the player understand:

- their body;
- urgent needs;
- known ecological information;
- calls and senses;
- Lineage and life history;
- settings and accessibility.

It should not turn Eonwild into a conventional quest tracker or spreadsheet overlay.

## 2. HUD hierarchy

### Always or frequently visible

Only information that needs immediate action:

- critical condition;
- stamina/exertion feedback;
- injury state;
- contextual interaction;
- essential group/call information where applicable.

### Contextual

- hydration or food quality details;
- sensory observations;
- species capability readiness;
- route/landmark memory;
- environmental warnings already detected by the animal.

### Out of active play

- Lineage;
- field guide;
- life summary;
- species mastery;
- settings;
- detailed evidence/science notes.

## 3. Communicating body condition

Use several channels:

- animation and posture;
- breathing;
- sound;
- movement response;
- screen/HUD indication;
- controller feedback where available.

Do not require the player to stare at multiple bars to know the animal is exhausted or injured.

## 4. Sensory interface

A sensory/instinct action can:

- emphasize recent tracks;
- indicate broad scent direction;
- isolate calls;
- reveal known water/food suitability;
- identify group signals;
- summarize information the animal plausibly perceives.

It should not:

- reveal every animal through terrain;
- show an exact objective route;
- remove uncertainty;
- remain permanently active without tradeoff;
- present human scientific labels during immediate danger.

## 5. Navigation

Potential navigation aids:

- remembered landmarks;
- a stylized mental map;
- discovered water/route knowledge;
- sun, wind, river, and terrain orientation;
- optional stronger assistance accessibility mode.

Avoid a permanent GPS line to migration.

A map should represent what the player/animal has learned rather than expose the entire world immediately.

## 6. Onboarding

The first session should:

- allow movement within seconds;
- teach one input at a time through context;
- show food/water/sense interactions naturally;
- avoid a long text tutorial;
- allow experienced players to skip guidance;
- reveal ecology through an early readable change.

A safe tutorial enclosure should not misrepresent the open-world game.

## 7. Species selection

The selection screen should communicate:

- ecological role;
- movement style;
- food/water pressure;
- social tendency;
- difficulty;
- major strengths and costs;
- scientific period and geography;
- current unlock/mastery state.

Do not present species as a damage/health tier list.

## 8. Field guide

The field guide is both educational and progression content.

For each species, distinguish:

### Scientific record

- name and classification;
- geological age;
- geography/formation;
- size ranges and evidence;
- known material;
- integument evidence;
- diet/locomotion evidence;
- uncertainty and disputes.

### Eonwild interpretation

- fictional ecosystem role;
- gameplay-tuned values;
- chosen social/hunting interpretation;
- capabilities;
- deviations made for play.

### Player observations

- discovered calls;
- food sources;
- tracks;
- routes;
- encounters;
- mastery records.

The guide should never blur gameplay invention into scientific fact.

## 9. Life summary

At the end of a life, present:

- route map;
- timeline of major events;
- environment changes;
- herd/group interactions;
- hunts, escapes, injuries, and discoveries;
- cause of death or success;
- Lineage earned and why;
- species mastery;
- another-life options.

Tone should resemble a natural-history life record, not a kill/death scoreboard.

## 10. Menus and application shell

Svelte owns low-frequency interfaces:

- home/start;
- species selection;
- Lineage;
- field guide;
- settings;
- playtest/telemetry consent;
- pause;
- life summary;
- store/platform surfaces later.

The real-time renderer and simulation remain outside Svelte reactivity.

## 11. Input support

Committed desktop direction:

- keyboard and mouse;
- controller;
- full remapping where practical;
- consistent abstract action map;
- separate camera and movement sensitivity;
- toggle/hold alternatives;
- no essential hover-only interaction.

Mobile touch is not a committed target, but the action model should avoid needless complexity that makes future adaptation impossible.

## 12. Accessibility baseline

### Visual

- scalable UI/text;
- contrast controls;
- color not the sole information channel;
- subtitle/call indicators;
- reduced bloom/fog intensity where needed;
- optional outline or cue assistance;
- safe-area and resolution support.

### Motion and camera

- camera shake control;
- motion blur toggle;
- head bob control;
- FOV/camera-distance options within gameplay limits;
- recenter behavior;
- reduced sudden camera movement;
- pause in solo.

### Audio

- categorized captions;
- directional indicators;
- separate volume groups;
- low-frequency reduction.

### Motor/cognitive

- remapping;
- hold/toggle options;
- auto-run;
- sensitivity/dead-zone control;
- optional stronger environmental cue assistance;
- clear cause-and-effect feedback.

Accessibility assistance should communicate more clearly without automatically trivializing the ecological choice.

## 13. Telemetry and privacy

During development playtests:

- use anonymous local session IDs;
- identify build, content hash, seed, renderer, and quality profile;
- collect gameplay/performance events only;
- export locally by default;
- do not collect name, email, precise location, microphone, camera, or unrelated files without explicit need and consent.

## 14. UX-quality questions

The interface is aligned when:

- players move quickly;
- they understand at least one environmental cue without exposition;
- HUD use does not replace looking at the world;
- species selection communicates roles;
- the field guide is scientifically honest;
- life summaries create replay desire;
- accessibility uses multiple channels;
- the interface feels like Eonwild, not a generic survival template.
