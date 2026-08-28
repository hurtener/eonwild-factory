# Fail-closed negative test matrix

Each case below was executed by the single verification command. Every case
returned the expected non-success result at the tested contract or Blender
stage, so the unittest itself passed.

| Negative mutation | Expected failure boundary | Result |
|---|---|---|
| Bad semantic expected parent | hierarchy contract | PASS |
| `STEP` interpolation | accessor contract | PASS |
| `CUBICSPLINE` interpolation | accessor contract | PASS |
| `commonTimeline: false` | rig contract | PASS |
| Mismatched channel timeline | timeline equality | PASS |
| Bad accessor component type | accessor contract | PASS |
| Bad accessor value type | accessor contract | PASS |
| Bad accessor byte stride | accessor contract | PASS |
| Small file below `__pycache__` | source-package inventory/forbidden path | PASS |
| 100 MiB + 1 byte `.pyc` | source-package size/forbidden path | PASS |
| Zero chest and neck local-delta bounds | Blender build stage, nonzero exit | PASS |
| Dirty referenced profile member | profile hash lock | PASS |
| Existing promotion destination | no-overwrite gate | PASS |
| Dirty current source | source-lock gate | PASS |
| Mutated candidate byte | approved artifact hash gate | PASS |
| Empty validation evidence `{}` | evidence schema | PASS |
| Malformed validation JSON | evidence parser | PASS |
| Failing evidence status | evidence schema/status | PASS |
| Cross-run comparison evidence | run binding | PASS |
| Wrong-artifact render evidence | artifact binding | PASS |
| Missing required render evidence | required profile media | PASS |
| Stripped contact facts with forged `PASS` | recomputed evidence equality | PASS |
| Missing profile before normal run context | common failure envelope | PASS |
| Missing promotion run before normal context | common failure envelope | PASS |
