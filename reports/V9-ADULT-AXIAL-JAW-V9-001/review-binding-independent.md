# Adult axial + neutral-jaw binding review — reviewer 2

Reviewed exact clean head `2c5dc911d15e60b4a37a0d6b9248fa547168672b` against `2c433df17fd7f8241565692b428c3e8a0fb82fe4`. Scope was the six-file candidate binding, selectors, and binding tests only. Closed axial-clock and neutral-jaw source implementations were not reopened. No files were changed.

Decision: **CLEAN**. No P0, P1, or concrete local P2 found.

- The V9 recipe changes V8 only in versioned identity, description/supersession, and the performance-profile binding. Source `2cdd901...`, rig, adult instance, V4 leg program, V10 contact profile, articulation profile, axes, cadence, and all other input bindings remain identical.
- The new performance V8 document is byte-for-byte equal to neutral-jaw V7 in classification, evidence reference, and every existing parameter; its only added parameter is `support_timed_axial_carrier: true`.
- Every V9 recipe input hash resolves exactly. Recipe SHA-256 is `f55da91847dc63489f9655cfc3641bee665bf8ce6122755a61748d98fabf3ccd`; performance-profile SHA-256 is `e133819dddf19bd224ddec7419687208e01abf8f3906fa147837813710dc2dfc`.
- CI compilation, native review, four-view routing, and `animal-benchmarks` register both V8 and V9 while preserving V3/V5/V6/V7 and fast-walk history. Each new name occurs in the expected three workflow sites.
- `git diff --check` and focused Ruff pass.
- `PYTHONPATH=src uv run --frozen --group test pytest -q tests/test_adult_axial_jaw_catalog.py tests/test_adult_body_weight_transfer_catalog.py --basetemp out/adult-axial-jaw-binding-review-3`: **8 passed in 1.77 s**.

The first local test invocation omitted the repository's test dependency group and failed collection for missing NumPy; the corrected frozen command above passed. This was environment setup, not a product failure.
