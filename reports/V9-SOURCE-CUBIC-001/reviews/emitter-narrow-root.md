# Emitter midpoint shape: root narrow closure

Reviewed only `36f311e4cfc67cd73eb684a21f353d0c804ff5fb..7cc9886283cf5de43b246bb05c3f073f121e4531`. PASS: remaining top-level midpoint receipt-shape P1 closed, no new P0/P1 in this narrow change. The result now requires the actual supported fields, exact sample count, finite numeric scalars, fixed classification, and per-foot verdict consistency. This is shallow evidence contract validation, not regeneration of nested phase histories or a redesign of legacy verification.

The actual retained walk package, copied normally, rejects verdict-only PASS payloads. Previous interpolation/explicit FAIL/malformed verdict probes remain rejected and truthful BLOCKED evidence stays accepted. Original inventory is byte-for-byte unchanged. Two affected regressions passed in 6.45 s. The author also reopened both actual walk and adult packages under this commit.

This closes the exceptional narrow correction following the two full review rounds; no third full review was performed. Integration/full-suite and native playback acceptance remain separate.

- `root-source-cubic-narrow-7cc9886-probes.json`: SHA-256 `d4ecd47346c8f23e20b44f2ceb67e176eaa982da484f18da84253da15946db7e`.
- `root-source-cubic-narrow-7cc9886-pytest.log`: SHA-256 `5eef7bfc76458397ec73bb38e9f703fd87fb8d17b3330adcb35fdb635a51e53d`.
- `root-source-cubic-narrow-7cc9886-junit.xml`: SHA-256 `970057aa1487d8360c8c67985caa4e6d55379f6873ff4cd3631cb26e01f185f9`.
