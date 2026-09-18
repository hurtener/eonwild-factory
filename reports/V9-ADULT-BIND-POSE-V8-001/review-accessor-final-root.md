# Final narrow bind accessor closure

Reviewed code: 4fc8c9cb9e6f48a266c516f1c4328ad91a19b1a5. This closes the same used-accessor helper finding following two full review rounds; no third whole-branch review was performed.

Root inspected the ef1c305 and 4fc8c9c helper diffs and independently reproduced five cases: missing buffer reference; individually misaligned but mutually cancelling IBM offsets; value-preserving misaligned ubyte JOINTS accessor offset; four excess BIN padding bytes; and fully repacked value-preserving JOINTS rows at invalid stride 5. All five now raise ContractError. The three data-preserving cases were independently verified to retain all decoded values, so rejection is due to the malformed layout rather than incidental skin corruption.

Root ran tests/test_bind_pose_recovery.py, tests/test_factory_admission.py and tests/test_animal_instance.py: 43 passed in 8.22 seconds. Root regenerated the valid adult geometry: SHA-256 2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f, unchanged. Reopened maximum skin reconstruction error remains 1.1353242509093592e-6 m.

The exact remaining accessor-conformance finding is closed. No root P0/P1 remains in this bounded admission stage. This validates the supported recovery inputs and is not a substitute for full Khronos validation of every glTF field. No thresholds, source geometry, recipe, animations or review films changed. The 370-frame V8 review remains valid for these identical bytes; native-speed playback is still pending Mac unlock. Whole-body polish, jaw calibration and exact exported loop continuity remain unresolved.

Machine receipt: root-bind-accessor-final-4fc8c9c.json; SHA-256 353b932cf566933a8b82263b61cb6e0d33719538c61a824c8a3fc3e43be32d02. Earlier receipts are preserved as evidence of their original heads and findings.
