# Current V9 continuity status at 83aa5e5

Current published source `83aa5e5391848493c902af0c6bd4ecab6228afe6`
keeps the exact emitted LINEAR/SLERP evaluator authoritative. Generic direct
joins and local steady loops remain `BLOCKED` where their exact serialized
velocity witnesses exceed unchanged limits. Adult V9's local loop is blocked
at `3.23101227406632 mm/s` against the `1 mm/s` limit. Earlier walk,
reverse-walk and run `PASS` results used the historical three-sample quadratic
estimator and remain diagnostic history only.

The source-identical local code checkpoint `806e3398c0f41a3c9c0a9dd2707887c284267611`
passed 928 tests plus 21 subtests in 408.98 seconds. Hosted macOS arm64 CI also
passed 928 tests plus 21 subtests in 571.06 seconds at commit
`62a9e10ee2cd677ea4c5bd551746fe4c37ea6536`, whose tree is identical to the
published 83aa tree. `ci-contracts-83aa5e5.json` records the run, runner, tree
identities, tool-scope boundary and log hash.

A later current-motion workflow at the same published 83aa source completed
the adult V9 and walk-pair jobs with blocked motion results; it was not a full
CI pass. Adult V9 remained integrity `PASS` and technical `BLOCKED` because
both exact local-loop modes exceeded the unchanged linear-velocity limit.
Walk v3 start and stop pairs likewise remained `BLOCKED` on exact emitted
linear and skinned velocity. Native review jobs could still be running when the
receipt was captured. The adult V9 native job subsequently completed with
render status `PASS`, technical status `BLOCKED`, exit 2, and an uploaded media
artifact; this is render/job evidence without a perception or frame-by-frame
review claim. The two current receipts preserve that evidence without replacing
the earlier source-identical suite receipt.

The bounded walk v3 source-interface experiment uses the actual walk v3,
walk-start v3 and walk-stop v3 recipes and independently evaluates their
unrefined source poses at the declared one-eighth-cycle interface. Exact
same-phase joint, material and local-rotation poses agree within floating-point
noise. First-order one-sided material-velocity mismatch falls from 15.2675 to
0.458080 mm/s as `h` decreases from 1 ms to 30 microseconds. An independent
second-order probe remains below 0.36507 mm/s for world joints and below
0.013822 mm/s for ordered material vertices across the tested steps.

Measurements are consistent with a shared continuous source trajectory at both
tested interfaces; no finite jump is resolved. This is not a formal continuity
or derivative theorem. The concrete next experiment is to estimate all-key
source tangents without copying boundary values, emit CUBICSPLINE channels, and
apply the exact serialized TRS, FK and LBS gates. Pointwise continuous skin
correction for refined plans remains prerequisite work. No package, recipe,
threshold, visual status, Unity status or production approval changes here.

The copied drivers are the exact executed archives and intentionally retain
their workstation paths and captured 83aa identity. Preserve these evidence
bytes. To rerun, use a clean 83aa checkout, adapt paths only in working copies,
and record new driver and output hashes; never carry the captured-head label
onto changed source.

## Evidence

- `ci-contracts-83aa5e5.json` — hosted CI receipt; SHA-256
  `72dff9ec0448e73b7648f8d73e8f3632c73d352b5b83cd88de265c8cd66722c3`.
- `ci-current-motion-failures-83aa5e5.json` — completed adult/pair motion-job
  failures at the same published source, not a full-suite receipt; SHA-256
  `dcfade5c79e305786436b46853b7dfbb8a6c33a45fd578e14c5d7d120497f31c`.
- `ci-adult-v9-native-83aa5e5.json` — completed native render job and uploaded
  media artifact, with technical status still blocked; SHA-256
  `ba2dbdd6933821301a5340f9a2067825f8826adca53a54403ff4943f36ec4ce6`.
- `walk-v3-source-interface-README.md` — bounded method and interpretation;
  SHA-256 `229dd4e15010d4be1f6b5a0516e06138437ec386f850648e2e970b66bc773343`.
- `walk-v3-source-interface-result.json` — full first-order results; SHA-256
  `8fc1be56080aad3484c15f262005d42791a1b3fd768d01eb09c983a38d70486b`.
- `walk-v3-source-interface-analyze.py` — executable driver; SHA-256
  `ca7545b46571ad46aa08a6adbfd034324d6c6a69f4fe2aa14649dab958f64738`.
- `root-source-quadratic-probe.py` and `.json` — independent second-order
  probe; SHA-256 `efd720d26cf0879ecf67d3ae56d37a87d3b9d8128d12aa7047f34b3edbad393c`
  and `9e78293ea8f9c17b770e96a44d8af55681c8fba183a1336216e8a03d2a4862a9`.
- `root-source-quadratic-inputs-83aa5e5.py` — frozen probe input builder;
  SHA-256 `ca7545b46571ad46aa08a6adbfd034324d6c6a69f4fe2aa14649dab958f64738`.
