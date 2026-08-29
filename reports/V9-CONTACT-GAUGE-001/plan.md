# V9 contact/gauge extraction and validation plan

## Task

Implement the next bounded V9 slice in the canonical `src/eonwild_motion`
package: a deterministic, read-only contact/gauge measurement and validation
path. It will consume the immutable approved V8.2 relaxed-walk artifact and a
generic synthetic frame fixture, derive the local travel frame from measured
motion, compute sole/toe contact facts, and emit machine-readable measurements
plus evidence hashes. It will not alter GLB bytes, motion curves, profiles,
channels, or promotion state.

The newly uploaded evidence videos outside this checkout are explicitly out of
scope until their owner confirms that all files are present and stable. This
slice uses only the existing immutable V8.2 release evidence and checked-in
fixtures.

## Narrow review-fix scope

The implementation review requires two fail-closed admission fixes before
handoff: validate every configured GLB accessor index and its container shape
before any accessor dereference, translating malformed container/index errors
to `ContractError`; and require the GLB, source profile, and policy paths to
resolve inside the supplied repository before loading or extracting. Focused
negative tests will exercise out-of-range position/joint/weight accessors,
malformed accessor arrays, and external source-profile/policy/GLB paths.

This correction round additionally closes the domain review without widening
the slice: travel speed/tangent uses total displacement over elapsed time;
contact velocity uses forward/centered/backward finite differences; anatomical
lateral sign comes from named hip-left/right geometry; every normalized width
uses one window-canonical denominator; `stepWidthNormalized` is mandatory and
is explicitly measured or unevaluated; turn state is explicitly
`UNEVALUATED_UNSUPPORTED`; animation sampling honors nonzero timeline bounds;
and skin weights are finite, nonnegative, positive-sum and normalized before
skinning. Step-width events are paired only when adjacent, alternating
touchdowns have strictly positive elapsed time above `1e-12 s`; simultaneous
bilateral onsets are explicitly unevaluated. The GLB adapter also preserves
nonzero animation timeline bounds end to end.

## Intended files and ownership

- `src/eonwild_motion/contact_gauge.py` — canonical generic contact/gauge
  extraction, policy admission, vector math, deterministic serialization, and
  evidence generation. No species names, family branches, or GLB writes.
- `profiles/v9/contact-gauge-v8.2.json` — explicit checked-in measurement
  binding for the immutable V8.2 GLB (accessors, landmark nodes, and sole/toe
  masks); this is data policy, not species logic.
- `tests/test_v9_contact_gauge.py` — focused positive/negative coverage for
  policy admission, measured travel-axis derivation, axis rotations,
  zero-travel failure, contact windows, penetration/crossover facts, generic
  synthetic input, simultaneous-touchdown step rejection, nonzero GLB timeline
  bounds, and deterministic double-run hashes.
- `reports/V9-CONTACT-GAUGE-001/plan.md` — this pre-edit plan.
- `reports/V9-CONTACT-GAUGE-001/contact-gauge-report.json` — generated,
  reproducible machine result for the checked-in V8.2 source and generic
  fixture.
- `reports/V9-CONTACT-GAUGE-001/evidence.json` — source hashes, policy hash,
  output hashes, commands, acceptance results, and limitations.
- `reports/V9-CONTACT-GAUGE-001/commands.md` — exact verification commands
  and outputs.
- `reports/V9-CONTACT-GAUGE-001/limitations.md` — explicit measurement and
  non-claims boundary.

Existing V8.2/V8.3 profiles, channels, assets, release evidence, the CLI, and
all other workstream-owned implementation files remain out of scope. No new
dependency or renderer is planned; a fixed-camera renderer is omitted unless
the existing reader can provide it without mutation and it materially improves
this pre-solver evidence.

## Acceptance checks

1. Confirm exact implementation HEAD and that the approved V8.2 source GLB is
   read without changing its bytes. Recompute and record V8.2/V8.3 profile,
   channel, lock, and approved/candidate asset hashes.
2. Admit the checked-in narrow-gauge contract as policy input with explicit
   version/status/scientific boundary and required metric definitions; reject
   missing schema, unknown policy fields, non-finite values, stale axis aliases,
   and ambiguous units.
3. Extract contact/gauge facts using one generic code path: measured travel
   tangent and stabilized lateral axis, hip-height/hip-width normalization,
   per-foot sole/toe centroid, foot heading, crossover, floor gap/penetration,
   contact/toe-off windows, and quantiles. Separate measured facts from the
   policy's engineering envelopes and never present envelopes as measurements.
4. Run focused positive/negative tests, including arbitrary yaw rotations of
   the same input, zero-travel fail-closed behavior, and a materially distinct
   synthetic body/frame fixture through the same generic path.
5. Run two identical calls and compare byte-level report and canonical hashes;
   ensure all emitted numbers are finite and JSON is stable.
6. Run the existing full regression suite with no skipped tests (76 tests in
   the current checkout). Confirm the V8.2/V8.3 release hashes are unchanged
   after the slice.
7. Re-run the focused review-fix negatives and regenerate the deterministic
   report/evidence hashes after the admission hardening.
8. Probe irregular timestamps, an initial large toe jump, initially crossed
  feet, variable hip height, missing step-width policy, simultaneous touchdown
  events, unsupported turn state, nonzero animation timeline bounds (including
  the GLB adapter), and non-normalized/invalid skin weights; verify each
  disposition is explicit and fail-closed where
   required.

## Assumptions and boundaries

- V9 analysis coordinates are metres, seconds, kilograms, right-handed Y-up,
  forward `-Z`; motion travel is measured from root/COM samples and is never
  inferred from a stale static axis label. Synthetic rotated inputs preserve
  this contract by applying an explicit rigid yaw transform to all points.
- Contact centroids use deterministic sole/toe point masks supplied by the
  input measurement fixture; ankle or toe-root origins alone are forbidden.
  The existing V8.2 witness geometry is reported as measured evidence,
  including inherited floor penetration, not silently corrected.
- `hip_height_m` and `hip_width_m` are independent measured normalizers. The
  report includes both width-over-height (the accepted audit contract) and
  width-over-hip-width (the requested gauge view); neither is substituted for
  the other.
- Contact and toe-off thresholds are explicit engineering-envelope policy
  inputs, not fossil facts. This slice validates and reports them but does not
  claim physical support feasibility, friction, support polygons, dynamics,
  whole-body solve, or gait promotion.
- V8.2 animation evaluation may require the repository's already-supported
  local reader/tooling. If its exact skin/animation provenance cannot be
  reproduced without a new dependency or a motion mutation, report the block
  and retain the generic fixture tests rather than weakening the gate.
