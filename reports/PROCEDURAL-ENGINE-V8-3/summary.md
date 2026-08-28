# PROCEDURAL-ENGINE-V8-3 — implementation summary

## Result

The permanent `eonwild-motion` engine now builds an executable V8.3 working
candidate from the immutable approved V8.2 input. The declared order is
`pelvis_balance_pre_ik@1`, `leg_contact_resolve@1`, then
`chest_tail_head_stabilization@1`. Engine code resolves semantic rig roles; all
concrete rig and motion values remain in catalog/profile documents.

The complete amplitude sweep selected `0.5`, the strongest candidate that
passes every revised hard gate. Scales `0.625`, `0.75`, `0.875`, and `1.0`
fail one or more declared bounds and were not selected.

Stable remains exact approved V8.2. Working points to V8.3 iteration 1,
revision 2. The top-level channel generation remains 1 because a working-only
change does not advance stable or stable history.

## Selected measurements

- V8.3 artifact SHA-256: `b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03`
- Stable V8.2 artifact SHA-256: `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`
- Pelvis lateral/vertical range: `0.030924 H` / `0.019733 H`
- Pelvis pitch/yaw/roll: `1.124906°` / `3.148266°` / `4.094129°`
- Chest relative pitch/yaw/roll: `5.791259°` / `2.752822°` / `5.558301°`
- Tail yaw base/mid/tip: `7.435105°` / `20.664978°` / `28.882205°`
- Head world pitch/yaw/roll: `2.580073°` / `1.528813°` / `0.966135°`
- Chest/pelvis roll correlation: `-0.942674`
- Maximum solved foot world error: `2.5823e-15 m`
- Final-skinned worst axis/Euclidean regression: `0.000103951 m` / `0.000119310 m`
- Stride/speed: `2.59999997 m` / `4.59999986 km/h`

## Visual evidence

Three synchronized, fixed-camera 10-second comparisons at 24 fps and 240
frames show V8.2 on the left and V8.3 on the right: side, front, and fixed
front-three-quarter. Nine full-body and nine foot-detail phase crops cover
contact through receiving. The static review page labels visual approval as
pending; this implementation does not self-approve.

The evidence scene now includes a neutral matte floor and readable Eevee
contact shadows derived from the primary skinned mesh floor. The 10-second
files intentionally preserve the requested duration and stop cleanly at the
end; the review page does not loop their non-integral 2.46 native cycles.

The validator now runs the normative evidence cross-check rather than trusting
PASS selectors alone. It binds artifact/baseline identity, shared layer scale,
the complete strongest-pass sweep, thresholds, finite metrics, semantic
rotation-only ownership manifests, final-skinned witnesses, and media/review
hashes. Controlled corruptions fail closed.

Representative frames were inspected locally. Direct `file://` navigation in
the in-app browser was blocked by its security policy, and no alternate-server
workaround was attempted.

## Status

Machine validation is PASS. Visual approval and stable promotion remain pending
independent review. No stable channel state, stable history, or approved V8.2
bytes were changed.

The final full suite passed 29 tests in 60.622 seconds with zero failures,
skips, or disabled cases.
