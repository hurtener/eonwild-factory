# Body carrier mechanics review: 9d5ae0f

Scope: narrow read-only review of `9d5ae0fe873507e6088714727943dfd8b293b2c2` against `63b87b3e140314c051c92ffa901eb407b79a986a`. Reviewed only opt-in stance-vault proxy, semantic signed sway/lean, legacy preservation, grounded/start-stop clock behavior, recipe locks, and focused test adequacy.

Result: no concrete P0/P1/P2 mechanics or contract finding.

Evidence checked:

- `GroundedGait.pelvis_height_carrier` accepts only `stance_vault_proxy` or `None`. Its phase `time / step_period - duty_factor` reaches high at declared sole-support midpoints and low at declared double-support midpoints; the analytic vertical velocity uses that same phase.
- `Performance.support_directed_pelvis_carrier` is grounded-only and optional. The carrier derives signed lateral direction from the bilateral semantic hip separation projected on `cross(up, forward)`; it rejects absent/laterally coincident hips. Its cosine transfer is continuous through double support, and the inverted roll carrier tips the pelvis top toward the supporting hip.
- Omitted fields retain the recorded hashes: raw plan `d072715a03d517df64c43553d69311fec94b020b002bce46ce1a0215ca9e066c`; decorated plan `cb07b756443ee231d12bec2a5e948a23f8a31ea8048a937966c0ed2e90e4dce3`.
- Direct malformed probes rejected `pelvis_height_carrier='bounce'` and `support_directed_pelvis_carrier=1`. The focused suite passed 35 tests, including non-axis and mirrored semantic-role cases and start/stop interface matching.
- Recipe locks resolve and the emitted package verifies integrity plus technical PASS. Manifest `3b26f33d3cc1f248775c861b84153d51bfb5db3c211822a37f15a8747ee4d7d9`; final root/in-place skin contact, articulation, cyclic continuity, and solver feasibility all pass. Visual review remains PENDING and Unity parity NOT_RUN.

No mass, COM, GRF, or specimen biological claim was introduced. No source was modified during this review.
