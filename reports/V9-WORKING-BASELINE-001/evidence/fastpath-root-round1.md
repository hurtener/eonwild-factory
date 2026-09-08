# Source-query offset fastpath: root review

Reviewed commit `f125e97ec857ac006ab84126f1b052232cd66693`, tree
`e87ede6b466f827482a4f66ff6fb2df19276ff75`, against published parent
`6e3080196182688cad49a4b441753e27064824fc`.

## Scope and outcome

Read the complete four-file implementation/test diff, surrounding query
evaluation and constant-law admission, both fallback paths, and the corrected
parent/child benchmark driver and receipts. No code P0/P1 or reachable local
P2 remains. The optimization preserves standalone evaluation and applies both
owned offsets before the single corrected solve. Constant-law build still
rejects refined queries, validates its actual query/provider bindings, and
retains pointwise material, clearance, IK and articulation checks.

Root focused verification: `tests/test_source_motion_query.py`,
`tests/test_constant_skin_targets.py`, `tests/test_source_cubic_emission.py`:
**40 passed in 140.31 seconds**. Output is retained in
`root-source-query-fastpath-f125-tests.log` beside this review.

## Local evidence finding, closed

The original benchmark injected the per-foot fallback observer, measuring four
solves per time rather than the published parent's default two. Its claimed
4.309x comparison was therefore not a parent-path speedup. The author preserved
that receipt and supplied a separate-process comparison of the actual default
paths at the two immutable heads.

Root checked the corrected driver and both bound receipt hashes. All eight
sample records and all seven input hashes match exactly, including row, pose,
material and observation hashes. The true solve counts are **16 to 8**; the
representative timings are **5.249131 to 2.904980 seconds (1.806942x)**.
This is a representative query-operation benchmark, not a full-compile forecast.

Corrected comparison SHA-256:
`6f6d7e407c231ba8791db71616a08b8b073fda8c0d223817c2dfc8f83f51dc7b`.

No whole-branch re-review was performed. Real fast-walk compilation and native
motion review remain separate production evidence; this review grants no
visual, biological, Unity or whole-catalog approval.
