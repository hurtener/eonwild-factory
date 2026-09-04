# V8.1 relaxed-walk respin candidate

## Intent

Create one isolated, reproducible V8.1 **relaxed-walk-only** candidate for perceptual approval. This is not a return to V5.5 and not a new V8.1 release. It retains the accepted V8.1 rig, neutral posture, 90% foot-pivot calibration, contact architecture, and all non-walk animation outputs. The candidate changes only the relaxed walking profile/solve necessary to test longer fore-aft reach, a slower relaxed cadence, and progressive late-stance toe contact.

The intended physical calibration is the user-supplied adult reference scale: 12 m nose-to-tail, 2.75 m hip height, and 4.5–4.8 km/h relaxed walking. Locked center values are 2.75 m same-foot stride, 0.465 Hz cadence (1.279 m/s; 4.60 km/h), 0.72 stance, +0.54 hip-height contact lead, 0.20 loading/toe-off windows, 9-degree foot rocker, and 12-degree toe push.

## Immutable boundaries

- `procedural-animation-toolkit(v8.1)/` is accepted source/release material and is read-only.
- `procedural-animation-toolkit(v8.1)/validated_result/` is read-only.
- `showcase/v8.1/` is read-only.
- No existing V8.1 GLB, profile, render, browser artifact, or non-walk animation is overwritten or regenerated.

Before and after generation, the candidate runner must prove the accepted V8.1 source-GLB/profile hashes and a deterministic tree digest of these boundaries are unchanged. The candidate reports these values rather than relying on visual similarity alone.

## Candidate-owned files

- `candidates/v8.1-walk-respin/**` — profile overlay, minimal reproduction/validation scripts, generated walk-only GLB and machine-readable evidence.
- `showcase/v8.1-walk-respin/**` — only the final 10-second, side-view, 24 fps H.264 approval film and its render metadata.
- `reports/V8-1-WALK-RESPIN/**` — plan, commands, hashes, validation output, visual-review notes, and final evidence summary.

The factory repository has no `config/ownership.yml` or `workstreams/` directory. This is therefore an explicitly task-scoped addition, analogous to the prior candidate lanes; it does not modify shared config, canonical docs, schemas, toolkits, accepted results, or existing showcases.

## Implementation shape

1. Apply a narrow candidate-owned walk overlay to the canonical V8.1 profile; the accepted profile is never edited.
2. Reuse V8.1 solver modules as read-only imports. Generate only the two relaxed-walk clips required for comparison (in-place and root-motion), or a walk-only GLB if the importer/exporter requires both.
3. Add candidate-local diagnostics for reference-scale velocity/stride, foot extrema relative to the hip, every baked key's selected-sole ground state, joint continuity, and the rear-foot/metatarsal-toe contact sequence. A bounded per-key toe-root bisection uses actual weighted distal toe vertices to retain contact through the visible rocker, then eases its correction to zero in release; it never moves the metatarsal/foot node.
4. Render only one 10.000 s fixed side-view MP4 at 24 fps from the candidate walk. No other clips, stills, montages, or HTML gallery are generated.

## Acceptance checks

1. Immutable proof passes: source GLB and canonical V8.1 profile hashes match their captured baselines, and immutable-boundary tree digests are identical before and after.
2. Candidate source/provenance is explicit: source GLB/profile SHA-256 values, tool versions, command lines, and candidate profile SHA-256 are recorded.
3. Reference-scale walk speed is 4.5–4.8 km/h, with actual baked root delivery, cadence, and same-foot stride measured from the generated clip rather than asserted from configuration.
4. Full-cycle front/rear foot extrema relative to the pelvis demonstrate materially longer fore-aft reach than accepted V8.1 without exceeding the accepted rear-extension anatomical limit.
5. Every exported key of both candidate relaxed-walk clips passes selected weighted-sole penetration/hover checks on flat ground; no frame has unsupported loaded contact.
6. Joint rotations are finite, channels/timelines are valid, sampled joint velocity/acceleration are continuous within profile gates, and the loop seam closes.
7. Late stance is ordered: rear metatarsal/foot lifts while a weighted toe patch remains in ground contact, then the toe/digit branches release before swing. The report records exact phase/frame intervals and fails if the order is absent.
8. Blender 5.2 imports the candidate GLB read-only and renders exactly one 10.000 s, 960x540, 24 fps H.264 MP4 with a full-body locked side camera. `ffprobe` verifies duration and frame rate.
9. Visual review covers full-body mass, fore-aft reach, rear toe-off, foot contact, and loop seam. The result remains a user-approval candidate, not an accepted release.

## Assumptions and unresolved items

- The supplied captures are visual timing/pose references, not calibrated motion capture or independent proof of Tarbosaurus kinetics.
- The user's specified 12 m / 2.75 m / 4.5–4.8 km/h values are the acceptance calibration for this candidate; no unsupported scientific precision will be claimed.
- The reference handoff treats listed values as centers with bounded tuning ranges. Iteration 15 uses the stated centers and a maximum solved toe-root correction of 3.104 degrees, below the 8-degree candidate-local solve bound.
- "Bead" is interpreted as the rear/metatarsal portion of the foot: it should begin lifting while a forward selected toe-contact patch is still loaded. The candidate diagnostics will make that interpretation testable.
