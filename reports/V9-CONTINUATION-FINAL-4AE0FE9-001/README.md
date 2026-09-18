# V9 continuation final evidence at 4ae0fe9

Status: **local implementation verification complete; draft PR #2 remains DO NOT
MERGE.** This report does not grant user art-direction approval, biological
validation, Unity parity, production approval, or acceptance of the remaining
sprint handoffs. Hosted CI for the final published documentation head is
pending.

## Exact source and local suite

The final local source is
`4ae0fe92ec3ffd49dfeca14085756cc7cbe7d852`. On a clean tracked macOS arm64
checkout, the mandatory suite passed **683 tests plus 21 subtests in 212.65
seconds** with Blender 5.2.0 LTS and Khronos glTF Validator
2.0.0-dev.3.10. The JUnit count including subtests is 704. The copied
[host-validation.json](host-validation.json) is the authoritative receipt.

The post-fix host probe reopened all 14 retained packages: adult recovery v3,
fast-walk v2, and the twelve start/steady/stop packages for walk,
reverse-walk, run, and sprint. Every package retained integrity and technical
`PASS`, `visual_review: PENDING`, `unity_parity: NOT_RUN`, and
`production_approved: false`. The same probe rejected both original P1
reproductions: a forged approval manifest and a grounded plan with no sampled
swing. See [host-postfix-probes.json](host-postfix-probes.json).

## Final review closure

The full review head was
`3219d65d66f4408e1eaf05d4eccec39409b474e1`. Two independent reviews found one
P1 each:

- [integrity.md](integrity.md) found that a package manifest could falsely
  claim approval while `verify_package` returned integrity `PASS`.
- [mechanics.md](mechanics.md) found that a cyclic grounded plan could pass its
  articulation profile without sampling swing.

Both findings were fixed without relaxing gates. Each fix received the allowed
narrow diff-only re-review, and both returned clean with no remaining P0/P1:
[integrity-postfix.md](integrity-postfix.md) and
[mechanics-postfix.md](mechanics-postfix.md). The original forged manifest and
absent-swing triggers are rejected at the final head. No third full review was
performed.

## Transition pairs

The independent package reopening and direct-join re-verification at
`3219d65d66f4408e1eaf05d4eccec39409b474e1`, using packages generated at
`9d6974d75c5832e3c0bc3a2e8903588684228dc5`, records the following in both
root-motion and reconstructed-world in-place modes:

| Gait | Start | Stop | Overall |
| --- | --- | --- | --- |
| walk v3 | PASS | PASS | PASS |
| reverse-walk v4 | PASS | PASS | PASS |
| run v4 | PASS | PASS | PASS |
| sprint v4 | BLOCKED | BLOCKED | BLOCKED |

The complete hashes and results are in
[pair-verification.json](pair-verification.json). The original walk and
reverse-walk generation commands exited 120 after their handoff receipts had
completed because the internal temporary volume reached `ENOSPC`. That original
status remains preserved. The copied receipt is the separate host reopening and
pair verification; it does not rewrite the original run into a success. The
later final-head probe at `4ae0fe92ec3ffd49dfeca14085756cc7cbe7d852`
verifies all 14 retained package identities and metadata, including these
twelve pair packages.

## Actual FBX transport

The real Blender transport check reopened both adult-v3 and walk-v3 FBX files.
Each retained its exact source duration of `2.4600001017252606 s`, used NLA
scale `1.0`, and preserved the start, middle, and end bone origins with maximum
error below `0.000006 m`. The exact per-sample values and transport hashes are
in [actual-fbx-verification.json](actual-fbx-verification.json). This is Blender
transport evidence. Unity remains `NOT_RUN`.

## Visual evidence boundaries

Adult recovery v3 remains **accepted as the revised factory recovery
candidate** after the host inspected 444 rendered review frames across six
native-time views, twelve exact-time stills, and six complete 1x playbacks.
This is the scoped factory-candidate decision already recorded in
[V9-ADULT-RECOVERY-V3-HOST-001](../V9-ADULT-RECOVERY-V3-HOST-001/README.md).
User art direction, biological validation, Unity parity, and production approval
remain open.

Fast-walk v2 is not accepted as the adult benchmark. The host inspected all 192
frames across four native views and completed all four 1x playbacks. The
recovery remains folded and relatively flat, and the pose remains more crouched
than adult v3. It requires motion polish. The copied
[fast-walk-host-review.json](fast-walk-host-review.json) records that decision
without changing the immutable candidate.

The reviewed Linux fast-walk GLB
`cb7fe1e79febedb9130695b23275713baf80f85175d65ae38f24bf406ae0b330`, rendered
from checkout `6a7d23c4bafc6818f26188ce1297b32b487118b9`, is not byte-identical to the
separate macOS GLB
`38c8ccd04d944f355d038e523b1769756a4e855b439fd82c803c1beb8e9f5a87` generated
at `3219d65`. The recipe is the same and compared plan values differ by at most
`7.105427357601002e-15`, but the two GLBs remain separate platform artifacts.
The earlier `c43d426` workflow completed with failures and is not final-head CI
evidence.

## Evidence inventory

| File | SHA-256 |
| --- | --- |
| `host-validation.json` | `c8ad16f1e1bfb20efa068f04072f66060e671200ef563e34f6a6a88dd2ab3a48` |
| `host-postfix-probes.json` | `d73ffc12e995e24ca9a385b567461729d652f45dbf43d05681ad55b370906d73` |
| `integrity.md` | `16aef7961c8162c7da709e11bf88136b22ba0d5f61beab5007594c02604cae88` |
| `integrity-postfix.md` | `53ede4b09aa157f2c278090ca55caae39daa9f7494782afc9934ce533409e8e7` |
| `mechanics.md` | `10aea53021fc3575558905677025741f2f7ec1d4b693723661bb1abc3e6469ca` |
| `mechanics-postfix.md` | `a0eac3637b3b858a193b8ea8bec6e56c6ff98a6b64d1c801c55c1566dd3f5387` |
| `actual-fbx-verification.json` | `f5a3f2445ee06a122d8b0c0876391ef20d0cfd77d2abd84aed7e07d41956a130` |
| `pair-verification.json` | `cdc0a80b2247cd10dd76e97bfb8a71d6d85c67fc61186eebf1a52bb5244d8569` |
| `fast-walk-host-review.json` | `d5c1e1d042cc37574beb19e8883aa626ff59f302ed4ba2da5257af19dec99df2` |

## Remaining gates

Sprint start and stop remain blocked by the unchanged direct-join gate. Fast
walk requires visual polish. User art-direction approval and biological
validation remain pending; Unity parity is `NOT_RUN`; production approval is
false. The `4ae0fe9` receipt records hosted CI as `NOT_RUN`; hosted CI for the
ensuing published documentation head remains pending. Draft PR #2 must not be
merged on the strength of this local evidence alone.
