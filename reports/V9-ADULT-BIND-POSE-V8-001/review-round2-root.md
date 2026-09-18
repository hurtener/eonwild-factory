# Root bind-pose admission review, round 2

Exact head 1b5a13e9c703a67470288901291aff65aa9faa4a; parent16aab6232698c6f641c34624c0ea246c67f1684e. Second and final full review for generic recovery.

The NaN/Inf POSITION false-zero and strict index-type findings are fixed. Generic non-skin intermediary propagation and descendant mesh-world preservation are now implemented. Root's 37 focused bind/catalog/admission/animal tests passed in8.19 seconds. Frozen valid Tarbosaurus geometry and candidate identities are preserved.

One remaining P1 requires a narrow follow-up: `_accessor_index` validates positive view byteLength but not the actual accessor range within that view or the declared GLB buffer. The old generic reader only checks physical BIN length. Root independently changed only each of: inverse-bind view.byteLength=4, POSITION view.byteLength=4, and buffers[0].byteLength=4. All three invalid sources were accepted with skin reconstruction error1.1353242509093592e-6m, and the malformed declared ranges were preserved in emitted GLB. See root-bind-round2-bounds.json.

The narrow fix must validate used accessor span, stride/alignment and declared view/buffer/BIN bounds before reads; retain current valid source bytes and unchanged tolerances. This is a source-boundary fix, not a request for a new whole-branch review. After the patch, review only this diff and its negative/valid controls under the explicit P1 exception. No other root P0/P1 finding remains.
