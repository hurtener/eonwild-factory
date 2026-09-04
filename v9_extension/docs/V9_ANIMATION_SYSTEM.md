# V9 animation-system design

The 29 Tarbosaurus animations should remain distinct semantic contracts, but not become 29 unrelated algorithms.

## Twelve reusable motion programs

| Program | Animation contracts |
|---|---|
| `stationary_support` | 01 neutral idle, 02 alert idle, 25 wounded idle |
| `alternating_gait` | 03 walk, 04 fast walk, 05 run, 06 sprint |
| `gait_transition` | 07 walk start, 08 walk stop, 09 run start, 10 run stop |
| `attention_reaction` | 11 investigate/scent, 12 listen reaction |
| `bite_action` | 13 quick bite, 14 committed bite, 15 low bite |
| `recovery_failure` | 16 bite miss, 26 stumble |
| `body_pressure` | 17 shove |
| `feeding_interaction` | 18 feeding, 19 tear/pull, 20 swallow, 21 drink |
| `ground_posture` | 22 lie down, 23 rest, 24 rise |
| `vocal_display` | 27 threat call, 28 long-distance call |
| `terminal_fall` | 29 collapse/death |
| `dynamic_launch_attack` | separate V9 airborne/grounded power-attack benchmark |

## Weight-tier selection

The authored motion-family tier is selected primarily from resolved structural mass/weight, with hysteresis. Age fraction, segment proportions, leg length, inertia, relative strength, and condition continue to parameterize the motion inside that tier. This avoids both a scaled-adult juvenile and a fragile age-only rule in which two differently built individuals are forced into the same family.

## Artifact distinctions

- **AnimationSpec**: semantic contract for one animation.
- **MotionProgram**: reusable algorithmic phase graph.
- **BiomechanicalPlan**: one solved execution for a body, state, terrain, and target.
- **Baked clip**: sampled skeletal output at a parameter point.
- **Runtime metadata**: phase, contacts, events, windows, root/COM curves, overlays.

The baked clip cannot be the only truth; the generic program cannot erase intended performance.

## Locomotion

Walk through sprint share alternating support semantics but differ in duty factor, possible aerial phase, stride/cadence, contact placement relative to COM, compression, propulsion, torso bias, stabilization, tail bandwidth, exertion, and turning/braking capacity.

Playback-speed scaling is allowed only inside a validated local envelope. Crossing regimes selects/blends another solved family while preserving contact phase and velocities.

## Starts and stops

Starts are support transfer + unload + shortened first step + acceleration. Stops are a braking horizon driven by incoming speed, friction, strength, fatigue, injury, and final support. A crossfade may polish a compatible handoff; it cannot manufacture root displacement or impulse.

## Bites

```text
acquire → align → retract/anticipate → commit → gape → contact window
→ hit/miss/hold/yield/resist branch → follow-through → recovery
```

Quick bite keeps pelvis displacement small. Committed bite starts in the hindlimbs. Low bite shares lowering across pelvis/thorax/cervical chain. Miss recovery continues through expected contact space and creates a recovery step when necessary.

## Interactions

Feeding, tearing, swallowing, and drinking use target-relative constraints. Water height and carcass point are runtime inputs. The carcass simulation owns `TEAR_RELEASE`; animation responds to the resistance change.

## Rest and death

Lie-down and rise are separate effort/support programs, not reversed clips. Collapse is authored through irreversible support loss and first major contact, then handed to constrained physical settling—not pure standing ragdoll.

## Implementation waves

### V9.0 — body/regression
Body schemas, COM/support debug view, V8.1/V8.2 adult walk regression, growth fixtures, and second body profile.

### V9.1 — locomotion/condition
01–10, 25, 26.

### V9.2 — interactions and dynamic benchmark
11–21 plus power attack.

### V9.3 — ground posture, calls, terminal
22–24, 27–29.
