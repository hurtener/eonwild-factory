# Root narrow closure: exact emitted tangents

Frozen head: `52e826ccd7e05dd2e82c37e889af8cf0a977c7a0`; clean worktree.
Root inspected the 6370df1..52e826c batch diff and relevant tests. The multi-clip false PASS now rejects, witness vectors/times/units and quadratic indices are retained, nonconstant cyclic scale rejects without inventing a threshold, and production handoffs require exact evidence with matching counts and unique labels. Sampled and exact production rows share the node/material enumeration; named topology is checked separately. The deliberately explicit sampled helper route is confined to synthetic tests and carries a different classification.

Root focused execution: 70 tests passed in 2.23 seconds. Diff check passed. Independent root replay of the earlier four-gait FK/LBS probe was byte-identical to its source result (2d7ff35eae708ee47005568bda12e96ca623be8012a871dc457ddb5cf804dc16); Sol independently compared the production helper with that probe. No generation, threshold, or interpolation changes are in this patch. The checker improves measurement; it does not fix the diagnosed joins.

Narrow closure: CLEAN. No further full-branch review requested. Existing packages remain immutable and their old estimator PASS must not be presented as exact runtime C1.
