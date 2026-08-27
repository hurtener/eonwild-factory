# Independent review disposition

## Perceptual review

The first full review rejected candidate 3 with two P1 findings: attack still read as head-led, and feeding still read as neck-led. Candidate 4 corrected the body mechanics but revealed that the inherited V5 jaw calibration layer reopened the mouth before the new preload.

Candidate 5 received a narrow re-review. Result: **P0=0, P1=0**.

- Attack establishes a closed-jaw rear/down pelvis and leg brace before jaw opening and delivery.
- Feeding visibly settles through pelvis descent and hind-leg compression before/during the reach.
- The earlier neutral-support and walk findings remained passing and were not reopened.

## Technical review

The first review found three P1 release-truth defects: inherited V5 browser tests masquerading as V5.5 coverage, hard-coded site/browser PASS evidence, and a V5-only package verifier. It also found stale package records and generated Python bytecode as P2 hygiene issues.

After fixes, the final diff-only re-pin result is **P0=0, P1=0**.

- V5.5 tests exercise the V5.5 showcase and release manifest.
- The evidence writer runs the static checker and requires a coordinator browser record.
- The accepted Test 2 promotion received a bounded structural re-review: exactly two foot inverse-bind slots change, toe roots remain fixed, the undeformed skinned mesh remains invariant within `2.24e-8 m`, and the canonical GLB exactly matches the reviewed candidate SHA `4e6e85dc82e941a3fc10109ca781dd3dcbb084699dc19834bf8683c04b22fe65`.
- Browser acceptance is pinned to the current GLB and HTML hashes in `browser-acceptance.json`.
- Package verification, inventory, key checksums, copy manifest, and bytecode hygiene pass.
