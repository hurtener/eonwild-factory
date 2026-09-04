# Balance evaluator

`evaluate_balance.py` is the independent 120-phase basis-normalized evaluator
for the frozen V8.1 balance-transfer contract. It requires Blender 5.2+ as
the packaged Python/NumPy runtime; it does not open a scene, alter the GLBs,
or execute engine code.

Run from the repository root:

```sh
blender --background --python reports/V8-2-BALANCE-TRANSFER/evaluation/tools/evaluate_balance.py -- \
  --approved candidates/v8.1-walk-respin-2/generated/iteration-38/tarbosaurus_procedural_v8_1_walk_respin.glb \
  --candidate candidates/v8.2-balance-transfer/generated/iteration-b/tarbosaurus_procedural_v8_2_balance_transfer.glb \
  --expected reports/V8-2-BALANCE-TRANSFER/evaluation/evaluation-metrics.json \
  --gate-mode candidate-a-upper-only \
  --output /tmp/v8-2-iteration-b-balance.json
```

The command exits non-zero when the approved baseline fails to reproduce the
frozen evaluator values within its supplied tolerance. Its JSON output also
evaluates one explicit acceptance mode:

- `candidate-a-upper-only`: architecture-safe upper-body overlay. It freezes
  pelvis/lower-body values and checks a safe chest/tail-only improvement.
- `candidate-b-full-balance`: original full balance-transfer envelopes,
  including the deliberately deferred pelvis targets.

Add `--enforce-gate` for a non-zero exit on a failed selected gate. This tool
is not a replacement for the contact/rocker validator.
