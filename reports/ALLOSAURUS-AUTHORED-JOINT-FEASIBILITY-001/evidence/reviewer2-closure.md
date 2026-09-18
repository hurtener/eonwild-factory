# Authored-material local joint-feasibility narrow review

Verdict: **PASS — P0 0, P1 0, P2 0**

Reviewed final head `24c0651e6d815f946049c516899c2bebe8539bab`, tree `310af9feb7419a8ed5bedd3946bfef0a7936a246`, relative to parent `81274b75526c3f9f3e64d4cbabea0d8c97227116`. The complete implementation descends from `ee8e0e5354736bd5afde29e3988b7c5fb03f3417`.

The authored-material-only fallback preserves the ordinary monotone-floor path. On the exact nonmonotone exception it starts from the immutable declared source-row height, searches upward deterministically, and admits a sample only when material gap, target residual, unreachable extension, and articulation limits all pass unchanged. It remeasures the final sample and the existing query performs the final complete solve and repeats those gates. No global minimum, first-feasible, monotonicity, continuous-domain, or biological claim is made. If a safe sampled bracket is absent or the final gates disagree, it returns unavailable.

The corrected regression uses the measured lower/middle/upper reversal: the middle requested height is below the upper height while its material gap exceeds the upper gap by more than the existing `1e-8 m` monotonicity tolerance. The final provenance model is `material_floor_and_local_joint_feasibility.v3`; its binding digest differs from the former minimum-material wording.

Independent checks:

- `tests/test_authored_material_contact.py`: 20 PASS in 18.05 s.
- Exact public compiler/query replay at center, `nextafter` on both sides, and ±1 microsecond: all five rows AVAILABLE; residual, extension, and articulation remain within existing gates.
- I independently reran the exact `81274b7` behavioral head: all five rows AVAILABLE. The final `24c0651` replay payload is byte-equivalent as parsed JSON after removing only head, tree, and classification identity fields.
- `git diff --check` passes and the reviewed worktree is clean.

Evidence:

- Final replay `ARC/audits/allosaurus-authored-joint-feasibility-001/neighbors-24c0651.json`, SHA-256 `76f60bb123a0d49119353adf83c194fc177fc69aa4c379e2b60437926abeab60`.
- Final replay driver `capture-neighbors-24c0651.py`, SHA-256 `7bbb0efd2923b2b0712d97d851bcea230d805fd8b59bc68c20eb020615044f26`.
- Final replay log `capture-neighbors-24c0651.log`, SHA-256 `04b38e16de041853480c8064a754584563661e0e0b7c60410d34c3228de96f93`.
- Independent replay driver copy `ARC/audits/allosaurus-authored-joint-feasibility-reviewer2-81274b7/replay.py`; its output and log are retained beside it.

This closes the local source-query rejection only. Emitted continuous-time gates, package technical validation, visual review, and Unity validation remain pending.
