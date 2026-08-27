# V4 to V5 Migration

V4 remains valid and is retained unchanged. V5 may be adopted incrementally:

1. Replace the V4 animation GLB with the V5 GLB.
2. Update clip suffixes from `_V4` to `_V5`.
3. Replace double-crossfade action queues with the V5 exact-handoff contract.
4. Read `sourcePhase` and `targetPhase` from transition extras.
5. Apply root continuity offsets at handoff.
6. Update action UI from optimistic button text to player-observed state.

No skeleton reduction, mesh rebinding, or semantic-map rewrite is required.
