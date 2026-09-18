# Support-resultant diagnostic round 2 — independent reviewer 2

- Final reviewed head: `b4e54d48d067307d6a8c5017f4eaeba303299eb7`
- Postfix code head: `860233f339ff0b49cb3a1e9f525aa4b3e5d28119`
- Published base: `83aa5e5391848493c902af0c6bd4ecab6228afe6`
- Decision: **PASS — P0 0, P1 0.**

I reread both round-1 reports, inspected the complete bounded postfix diff and
the final retained report/evidence, and independently ran the eight focused
module and CLI tests. The two round-1 P1 families are closed.

The CLI now includes `biomechanics.json` in the exact expected/actual identity
map before any geometry scale, semantic height, inertia, or resultant
calculation. Its regression changes the consumed biomechanics payload after
sealing and proves nonzero exit with no output.

The validated `contact_load_alternatives` now generate the actual evaluated
single- and double-support arithmetic. A 90/10 leading/trailing declaration
produces the 90/10 weighted point and key. The validated
`local_com_alternatives` likewise generate only their requested model set; a
joint-origin-only request produces only `baseline_joint_origin`. Invalid or
incomplete load rows, unsupported COM choices, non-finite/negative weights,
and weights that do not sum to one reject before evaluation.

The final report retains the formerly external support audit, requires explicit
package and audit paths, removes the unsupported robustness and conservative-
bound language, quantifies the conditional proxy distances, and keeps the
sampled engineering/pressure/biological limitations explicit. No motion,
runtime, recipe, emitter, threshold, or approval state changes.

Independent verification:

```text
tests/test_support_resultant.py tests/test_support_resultant_cli.py
8 passed in 0.47s
Ruff: PASS
git diff --check 83aa5e5..b4e54d4: PASS
```

Verified SHA-256:

- CLI: `57626ef91897ad376eaba1a319ffc8257f9ee06c9432b2950b7aa8a0830ab1ca`
- CLI tests: `782216cf33a7529390ffda95fc73f9612c0cabf8f688dbe895cd193360699bb0`
- assumptions: `119a88e8fdcb765500a693742c333aa28a3495d277b9b7039aa1a187300334ba`
- result: `eae74608267fd618a13446406e92ffc61a9fb2fc6ba2511a359a59adc31cdb30`
- retained support audit: `03c1b83103ce4f72d9542a7dc320cc181a50a1ff53cdccf030b1220f2c96251f`
