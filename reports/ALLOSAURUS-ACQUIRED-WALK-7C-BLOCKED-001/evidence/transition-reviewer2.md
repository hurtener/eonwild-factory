# Allosaurus acquired steady transition seam — reviewer2 narrow closure

Verdict: **PASS for the bounded source/provenance closure**. P0=0, P1=0, local P2=0.

## Boundary

- Exact head: `45c50cb7a48219ee2242e3918bfaa1e039883812`
- Tree: `a98202ee2cefd764a28f39752264befe947c49ba`
- Parent/review boundary: `16a72efd6693f21f1b04ce58ccc46cdd29d45819`
- Worker clean.
- Review was limited to the three reviewer2 findings plus root's full-gain contact guard and the new one-sided boundary evidence.

## Closure

- Offline reconstruction now requires the named steady snapshot to use motion-intent v2, matching live resolution. The retained coherent v1-schema mutation rejects.
- A transition adapter now requires the steady query to contain the exact supplied adapter at construction and runtime, and binds the steady adapter digest. The retained A/B substitution probe rejects before producing mismatched feet.
- Direct non-transition recipes now reject `steady_motion`.
- Full-gain transition contact/support/flight must match the named steady result; the transition retains its own contact authority below full gain.
- Existing and new focused coverage passes: `35 passed in 29.75s`.
- `git diff --check 16a72ef..45c50cb` passes.

## Source-law evidence and limits

The author evidence `allosaurus-acquired-transition-seam-45c50cb-001/result.json` has SHA-256 `27829ab0392351dbf2eaff5b72f47b252aded4a89568cd28e260eeea92685f7b`. It binds the exact named steady intent/reference and checks start approach-to-full-gain and stop separation-from-full-gain at 480 Hz one-sided stencils. At the sampled boundaries, non-root local pose and root velocity match the named steady law to numerical precision, while transition contacts/root/stage remain owned by the transition.

This is non-emitting source-query evidence. Serialized CUBICSPLINE continuity, package handoff, visual review, and production approval remain NOT_RUN/PENDING.
