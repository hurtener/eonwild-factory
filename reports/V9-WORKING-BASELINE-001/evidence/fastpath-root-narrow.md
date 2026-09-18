# Source-query offset fastpath: narrow P1 closure

Reviewed `ff85ddd59da5da8d62f769b447f8accb87800124`, tree
`d51cc3b54a74e465a9aef3e7815aa8e53c37f743`, against reviewed parent `f125e97`.
This is the exceptional narrow P1 closure, not another whole-branch review.

The one-line exact-type guard routes every SourceMotionQuery subclass through
the existing per-foot observer fallback, including subclasses that override
the new private evaluator while inheriting the public methods. Existing
instance public-method override checks remain. The stock query's corrected
pose solve and all biomechanical/export gates are unchanged.

The added regression exercises a subclass that refuses combined-offset
evaluation, verifies that the constant law still returns AVAILABLE, and
asserts that the combined-offset path is never called. The author reports the
four relevant override/default-path tests passing. Root read the entire
two-file diff; no remaining P0/P1 or local P2 was found in this correction.
Reviewer 2's independent reproducer closure remains required before release.

The earlier root 40-test run at f125 and the corrected actual-parent benchmark
retain their exact-head boundaries. Neither is relabelled as a new full-suite
run at ff85. Native fast-walk motion acceptance remains separate.
