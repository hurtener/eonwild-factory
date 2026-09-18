# Root SourceMotionQuery and adult-jaw integration review

Exact reviewed head: `b31bcf655d72883d98e899e70f86213d3cec9730`; base: closed axial and jaw source `2c433df17fd7f8241565692b428c3e8a0fb82fe4`.

Decision: **CLEAN**, no P0/P1 or concrete local P2 in this integration. Scope is compatibility between the closed SourceMotionQuery stage and the separately closed adult axial/jaw source. No third audit of either closed stage.

The final tree includes the initial context extraction from `6d3f8e3` (integrated as `1dcd1cf`) as well as its closed SourceMotionQuery fixes. The earlier mistaken phase-local cherry-pick attempt was aborted and has no resulting commit. `solve_airborne_plan_sample` is AST-identical to the closed axial/jaw source. Query source differs from its closed stage only by a complete detached deep copy preserving original raw source identity, current document, binary, topology and local-rest caches. Cached/current-state admissions remain fail-closed. The extracted final context owns the neutral-jaw fields, calibration and single admission; the provisional geometry context excludes performance metadata.

Root independently ran the five SourceMotionQuery, neutral-jaw, phase-local, source-identity and articulated-contact-partition modules: **53 passed in 43.06 seconds**, no failures/errors/skips. JUnit and log hashes are below. The first invocation named two nonexistent test files and ran no tests; the corrected invocation is the result recorded here. Ruff for the query and its tests, and `git diff --check`, pass.

Root compiled the exact adult V9 recipe/input bindings from `2c5dc91` using this integration's actual source module (explicit `PYTHONPATH=src`). Both complete GLBs, plan, solver receipt, validation and runtime metadata are byte-identical to the retained V9 candidate. Thus the query extraction does not alter this adult motion or its existing blocked loop status. Legacy heavy-biped and renamed/frame-transformed full payload pins also passed in the focused suite.

This does not authorize source derivatives, continuous refined material targets, a new emitter, new gait acceptance, native playback, Unity parity or production promotion. The known huge-integer input error-type P2 remains closed-stage follow-up debt.

Evidence:

- focused log SHA-256: `0295e6bf900470faafa0e06fae44cbb7d7609f20f650908b14d246a835373291`
- JUnit SHA-256: `3290a651148a4fb0469bef92f69e8d28351ed10f134aa537cb2da6932d29a338`
- adult V9 emitted parity receipt: `root-source-query-v9-parity-b31bcf6.json`
- parity receipt SHA-256: `6af8bc37a724e711475dde092b476c3ebc967e2613f217402a25bea3cd0d73f7`
