# Root phase-local solver review, round 1

Head: e6c0b6f6daefba490305a79722ebb1644ffd1a41; base cc7b3d9e199d1679d28bbcbefb61bcea5407b129.

The solve body is extracted with original operation ordering. The compiler still chooses matching body-response rows, sign-normalizes and serializes once, and reopens the output for existing witnesses. Three new focused tests pass, including actual heavy-biped and renamed/transformed complete payload byte pins. No emitter or continuous interval authority is claimed.

## Finding

- **P2, local required contract fix: context is neither isolated nor deeply read-only.** AirborneSolveContext at `solve/airborne_gait.py:326-360` is frozen only at field assignment. Construction at lines 852-866 directly aliases caller source, roles and plan; only base_w is made nonwriteable. Forward/up/lateral/origin and bend-normal arrays remain writable, while nested mappings/lists are mutable. The same row changes its solved result after modifying the caller roles dictionary or writing context.forward[0]. This violates the bounded extraction's explicit immutable/defensive-context requirement and can introduce cross-request state drift at the new public row seam. Use isolated frozen geometry/topology/roles/plan views and immutable copied arrays (retain byte output), and test caller mutation plus direct nested writes. A deliberate low-level escape from immutable backing need not be defended, but ordinary dictionary/list/array writes must not modify the context.

`root-phase-local-round1-mutation.json` records direct aliases, writeable flags and the two result changes. No current unchanged single-call output regression was observed. Since this fix is local to the new seam and required by the agreed contract, address it before this stage is published. Do not expand into arbitrary-time planning or derivatives in this patch.
