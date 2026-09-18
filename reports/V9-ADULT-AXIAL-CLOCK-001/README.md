# V9 adult grounded axial clock

This closed source stage adds one opt-in grounded axial clock for the existing pelvis yaw, chest counteryaw and centered-tail yaw. The clock advances the semantic hemipelvis of the leading foot at declared double support and reaches zero at declared single-support midpoint. Its sign comes from each hip relative to the bilateral hip midpoint in the declared frame, and canonical gait-event witnesses make admission independent of the finite output grid. It is authored kinematic coordination, without a COM, mass, load, force, work, energy or biological claim.

The option is omitted by default. It requires positive grounded choreography, centered-tail semantics, and distinct semantic hips below the yawed pelvis; intervening helpers are allowed. Airborne and reverse motion are rejected. Existing leg recovery, contacts, articulation, root travel, amplitudes, tail lag, thresholds, source geometry and rig roles are unchanged.

## Frozen source and review

The published parent was `26ec06837cd03d59bd03d6bf948ae6e7d8cf4212`. The initial implementation was `483e006b1ddd20617b75e32b2e660b31e5ed0853`; the closed post-fix code head is `21dc78042a4580104784ff28a6b23c7b7cf0c92f`.

The final head passed 154 focused motion-performance, phase-local, grounded-placement and transition tests, plus 26 catalog/legacy tests. Both round-one reviewers reported no P0/P1 and independently found the same two local P2s: missing hip ancestry admission and reassociated binary64 arithmetic in the omitted tail path. The final head fixed both. Both round-two reviews are clean; a 300-row partial-gain comparison went from 181 binary64 rotation differences before the compatibility fix to zero.

- [Root round one](review-round1-root.md), SHA-256 `7a77fa2434106f014d55afc643b6f60cd3645fba37e3d58b94dcf76a1e56a4e0`
- [Independent round one](review-round1-independent.md), SHA-256 `e7b7e08af120f0eb529d63e342c27f54bb672561f29fc940e82b396178ad454b`
- [Root round two](review-round2-root.md), SHA-256 `14e26efc5b299258b5480ebd8510186008f7eb8c3b5b0b9a872bb68fe8d8d7ef`
- [Independent round two](review-round2-independent.md), SHA-256 `b4c663979b8a5b637ba75fd5c7451b14c522ad5617a478c3052c2feba6d9d1e7`

## Diagnostic package

The ignored diagnostic binding enables only `support_timed_axial_carrier` on adult V8. The copied [performance profile](diagnostic-performance.json) has SHA-256 `580d45ec09e62fc0226be580ff095fa168dee0c5b500cda0bead8767787506cd`; the copied [recipe](diagnostic-recipe.json) has SHA-256 `2748c3b6e9dd7ba798cad800027dc78706e46a21ed8e450ac61d36fd9109da44`.

The closed-source package is recorded by the [manifest](postfix-manifest.json), SHA-256 `364abd8b1bc510fb8c0f9f7037f06882eb7b7b25ca4d5cb483cf6ae8e516ebea`, [input lock](postfix-inputs.lock.json), SHA-256 `5787a78e8c09d4870613327c7ed91f8a9fbe913251c5cb3de0d19f7f9f271212`, and [validation](postfix-validation.json), SHA-256 `4341487eb6f88f180289647b9dfb3f26e1e02cb400595161f9df649abcdc3ecb`. Package payload hashes include:

- root-motion GLB `84c36a3e88129b5a2427167be80cbb85ad6efc5d733ab9c6a1cb6c5dad1fb08d`
- in-place GLB `51990803d3d35442d4a08cc9f28069f9afcfb979bcd58b952a7d1ceed66e32ff`
- plan `3655729eaf863f67d60b9bbad18c1fb6d69d64c969490173875b983158f34406`
- runtime `5531cb91a969e975a3fdbfbbebaf2cfd99ca79007dab23e03bc7cef89a7f1176`
- solver receipt `600d380803811e72d65598da55ccc9cc5bfe87d1fd4fc547ef7cc32b94ba00b5`

The [post-fix equivalence receipt](postfix-equivalence.json), SHA-256 `fc212f7fb6b8e9f39eadc2bec8b3e2f8c211af9c30428b276374c4bd9b5f1404`, proves that every package payload except the expected source-bound manifest and input lock is byte-identical between the initial and final-source compiles.

Factory verification reports integrity PASS. Final skinned contact, articulation, clearance, rotation-rate and output gates pass in both modes. Exact local cyclic continuity remains correctly **BLOCKED**: linear mismatch is `0.00323101227406632 m/s` against `0.001 m/s`; angular mismatch is `2.2502600720859265 deg/s` against `10 deg/s`. This stage does not claim exact runtime C1 continuity and changes no threshold.

## Reopened emitted measurements

The [emitted audit](emitted-audit.json), SHA-256 `300c660614c869d8a003ef022693d271eaecfbb70a4cd7c3387b23fea62fcff9`, and its [reproduction script](emitted-audit.py), SHA-256 `8c0e977225571e41c8b2e6e94b5814455a4e7a89dec0795112e62895908d05ae`, reopen all 297 serialized keys in both GLBs with all normalized skin influences.

- Zero skin penetration; maximum stance gap `0.00013062454401512866 m`.
- Interior swing full-foot patch gaps: `0.06039201066865732 m` left and `0.060256082750571954 m` right.
- Zero hard/preferred scalar articulation departure; solved foot-pitch peak `284.76605083481553 deg/s` under `600`; serialized rotation peak `375.9124397804565 deg/s` under `1200`.
- Nearest double-support keys show pelvis yaw about `+1.99982/-1.99982 degrees` and leading-hip advancement. Nearest single-support midpoint keys are within `0.00553 degrees` of zero yaw.
- Existing sagittal phase is retained: pelvis rotation-log lateral components are about `+1.19968 degrees` at double support and `-1.19974 degrees` at single support. Axial quaternion interaction changes that component by at most `0.02684 degrees` over all keys and head lateral rotation by at most `0.000564 degrees`.
- Chest lateral position changes relative to V8 by about `+29.775/-29.859 mm` at double support and `-44.314/+44.397 mm` at single-support midpoint, removing the diagnosed legacy chest-orbit cancellation.
- Tail timing changes substantially: sampled tail-tip lateral differences reach about `0.475 m`; the all-key/all-vertex maximum skin difference is `0.74814 m`. This remains a visual-review risk rather than evidence of biological effort.

The independently reproduced [host body measurements](host-body-measurements.json), SHA-256 `40b8f4b41f54a642acbe9d54b411eff607e16c31d99c24cdfb10b46739538f7a`, and [script](host-body-measurements.py), SHA-256 `8707154d9ea9b1292ac521c5e7cf076c09ca94f657bd35c28b0b10d41e4af831`, confirm that pelvis lateral peak-to-peak travel stays `0.082229 m`, while chest/head/tail-tip ranges change from `0.040381/0.054596/0.976207 m` to `0.117046/0.148277/1.049147 m`. At paired single-support landmarks, the mean lateral position of 4,907 trunk-weighted surface vertices changes from `+0.010851/+0.028240 m` to `-0.017070/+0.056345 m`. All positions are root-relative. Surface and uniform-volume measurements are descriptive geometry proxies, not COM, mass distribution, force, balance, stability or biological evidence.

## Remaining boundary

This source stage is closed, but integration with the neutral-jaw stage, a combined full suite, candidate binding, CI registration, native-time rendering, user visual review, Unity parity and production approval remain pending. No GLB or video is duplicated in this report, and no selector or promoted recipe changes here.
