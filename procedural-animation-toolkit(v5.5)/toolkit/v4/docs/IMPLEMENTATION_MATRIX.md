# V4 Implementation Matrix

| Requested capability | Primary implementation | Baked output | Runtime support | Validation evidence |
|---|---|---|---|---|
| Reference-fitted timing/posture | `reference_fit.py`, profile | relaxed/alert clips | manifest cadence + phase | fit JSON/contact sheet |
| Vertex-level sole collision | `sole.py`, locomotion residual pass | all locomotion/action contacts | `terrain-residual.ts` | fixture + sole-debug review |
| Terrain height/normal | `terrain.py`, support planner | uneven + upslope clips | runtime terrain sampler | contact metrics + terrain videos |
| Turning | `path.py`, locomotion factory | 35° left/right root clips | motion graph/steering metadata | endpoint + visual turn review |
| Acceleration/braking | speed envelopes + path integration | start and brake clips | state graph | monotonic root/transition gates |
| Alert locomotion | alert profile + attention overlays | alert walk in-place/root | alert state | alert review video |
| Eating | action controller + fixed contacts | eat loop | action queue | action constraints + video |
| Bite attacks | parameterized action kernel | ready + snap/lunge/heavy | action queue/events | action constraints + bite review |
| Roars | staged inhale/open/hold/recover | roar + display | action queue/events | jaw/head limits + roar review |
| Action transitions | transition compiler | 16 bridge clips | `motion-graph.ts` | endpoint equality/phase matching |
| Browser playback | custom WebGL2 viewer | same GLB | interactive controls/crossfade | browser contract JSON |
| Browser-production density | 60 Hz solve/export | all validated clips | direct playback | sample-rate gate |
| Ultra authoring option | 120 Hz solve / 60 Hz export | optional rebuild | same runtime contract | profile + tests |
