# V8.2 signed release technical review

## Verdict

**FAIL pending one package-integrity fix. P0 = 0, P1 = 1, P2 = 1.**

Reviewed commit:
`ae69233d4014bb0bd795730cf07edc0b87e064db` (`feat: release reproducible v8.2 balance transfer`).
The approved GLB itself is exact and reproducible, the commit is correctly
signed, and the release diff is cleanly scoped. The blocking defect is that the
advertised package verifier does not verify the package manifest or most of the
package.

## Verified release facts

### Commit, identity, signature, and ancestry

- Commit: `ae69233d4014bb0bd795730cf07edc0b87e064db`.
- Tree: `da2a7e048e108dbf9f7cd5d2ba9c31ee5db9dbcc`.
- Author and committer: `Santiago Benvenuto
  <117486687+hurtener@users.noreply.github.com>`.
- Raw commit object contains an SSH signature.
- `git verify-commit`, using the configured personal public key as the allowed
  signer, reports a good signature for
  `117486687+hurtener@users.noreply.github.com` with RSA fingerprint
  `SHA256:89wMdoHCHjswAf5f4ZX8L0jk8lgxaiI0/c1NHbdJN7U`.
- Repository signing configuration is SSH, signing key
  `/Users/santiagobenvenuto/.ssh/id_hurtener.pub`, with `commit.gpgsign=true`.
- Remote is `git@github.com-personal:hurtener/eonwild-factory.git`.
- Live `git ls-remote origin refs/heads/main` returned
  `e04c6a36fbea2b135d5f0c6b3ca1b04c6ebea04d`.
- The reviewed commit's sole parent and local `origin/main` are that exact SHA;
  the release is therefore one direct commit ahead of current remote main.

### Scope and hygiene

- Diff versus remote main: 19 new files, all under
  `procedural-animation-toolkit(v8.2)/` or `reports/V8-2-RELEASE/`.
- No unrelated tracked modification or deletion is present.
- `git diff --check origin/main...HEAD`: clean.
- Worktree was clean before this review report was created.
- Package size: 88 MB.
- Largest files:
  - included iteration-b base: 45,331,840 bytes
  - approved V8.2 GLB: 45,331,840 bytes
- No file exceeds 100 MB.
- No rejected/failed candidate, iteration history, render-frame cache,
  `__pycache__`, `.pyc`, or `.DS_Store` is in the release diff.

### Approved asset and clean reproduction

- Packaged approved GLB:
  `procedural-animation-toolkit(v8.2)/asset/tarbosaurus_v8_2_approved.glb`.
- Actual/config/manifest/evidence SHA-256:
  `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`.
- Included base actual/config/manifest SHA-256:
  `bfe8e833721f1dc0b8b4a1df72a6ea933debb1c6d76ac6d7970ae3ed6c8f4bc2`.
- Upstream approved V8.1 provenance SHA:
  `1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e`.

The documented Blender 5.2 command was rerun with
`--python-exit-code 1` into a new temporary directory. Generation exited 0,
produced the expected SHA, and the rebuilt GLB was byte-identical to the
packaged approved GLB (`cmp` exit 0). Verification of both the packaged and
rebuilt GLBs exited 0.

The verified base-to-approved delta is the non-empty 12-accessor set:
`Bone_002` and `Bone_037..Bone_041` rotations in each of the two RESPIN walk
clips. It is a subset of the declared seven-node allowlist; `Bone_036` is
allowed but byte-identical in this exact solve. The full output SHA additionally
binds every protected translation, non-walk channel, timeline, tail, pelvis,
root, leg, foot, toe, and GLB-structure byte.

### Official evidence and media

- `evidence/official-balance.json` SHA matches the manifest and contains
  Candidate-A gate `PASS` bound to the approved candidate SHA.
- `evidence/structural-mechanical.json` SHA matches the manifest, status is
  `PASS`, all five structural/mechanical checks are true, and it is bound to
  the approved candidate SHA.
- Media SHA-256 values match the manifest.
- Side media: H.264, 960x540, 24 fps, 240 frames, 10.000 s.
- Three-quarter comparison: H.264, 1920x540, 24 fps, 240 frames, 10.000 s.
- Both packaged media hashes match their exact iteration-g source files in the
  factory checkout.

## Findings

### P1 — `verify_release.py` is not a package verifier and the release manifest is incomplete

`procedural-animation-toolkit(v8.2)/scripts/verify_release.py:10-19` reads only
`config/release.json`, the included base GLB, and the candidate GLB. It never
reads `RELEASE_MANIFEST.json`; it does not check evidence or media presence,
hashes, dimensions, file-size policy, exclusions, or inventory. Consequently a
release missing or containing altered evidence/media/scripts can still produce
the committed `package verification PASS` result.

The manifest itself does not close this gap. Of 14 package files, it hash-binds
only six payload files (base, approved asset, two authoritative evidence files,
and two media files). Seven package files are not hash-bound by its entries:

- `README.md`
- `config/release.json`
- `scripts/glb_math.py`
- `scripts/release_generate.py`
- `scripts/verify_release.py`
- `evidence/package-verify.json`
- `evidence/reproduction-verify.json`

In particular, the reproduction evidence entry at
`RELEASE_MANIFEST.json:26` has no SHA. This directly contradicts
`reports/V8-2-RELEASE/summary.md:36-37`, which says exact package paths and
hashes are in the release manifest, and leaves acceptance check 4's package
inventory unimplemented.

Required fix: make the manifest a complete inventory of every shipped package
file except the manifest itself (path, bytes, SHA-256, and media facts where
applicable), then make a package verifier load that manifest and fail closed on
missing, extra, oversized, hash-mismatched, cache/temp/rejected files and media
probe mismatches. Keep the existing exact GLB/accessor verification as a
separate component of that aggregate gate.

### P2 — Packaged media provenance omits its render/input records

The two media files have correct final hashes and dimensions, and their exact
iteration-g sources were located in the factory checkout. However, the release
package keeps only final MP4 facts. It does not include or hash the source
`render-run.json` records that identify candidate/approved input hashes, clip,
camera/bounds policy, renderer, and the comparison's left/right inputs. This is
enough for final-file integrity but weaker than self-contained provenance.
Include a compact release-owned media provenance record or the bounded original
render records in the complete inventory.

## Review disposition

No release implementation or media was modified. Because P1 is non-zero, this
review report is intentionally not committed or signed. After the package
manifest/verifier is fixed, rerun the exact reproduction and package checks,
then request a narrow re-review of the new signed release commit.

## Round-two exact-head re-pin — `51bd9823cc1e9f19922062da8fba7c60b2955489`

### Verdict

**FAIL pending one remaining exclusion fix. P0 = 0, P1 = 1.** The previous P2
remains follow-up debt and was not reopened in this narrow review.

The fix commit is the direct child of the reviewed release commit
`ae69233d4014bb0bd795730cf07edc0b87e064db`. Live remote main remains
`e04c6a36fbea2b135d5f0c6b3ca1b04c6ebea04d`, which is an ancestor of this
head. The fix commit has a good SSH signature for
`117486687+hurtener@users.noreply.github.com`, using RSA fingerprint
`SHA256:89wMdoHCHjswAf5f4ZX8L0jk8lgxaiI0/c1NHbdJN7U`.

The approved asset and both media payloads are unchanged:

- approved GLB: `a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5`
- side media: `a29a14dcbcab3b6963c03966755e274419acb43704f26a71da2b055f0eaa8bac`
- three-quarter comparison: `5e11692890b18166cea169c61894c0cb3824a69fea79c932ebfffbba00045d10`

The v2 verifier now reads the manifest, requires the normal package inventory,
checks inventory hashes and the 100 MB limit, probes media facts, and recognizes
the documented manifest self-hash convention. With Blender 5.2.0 LTS, the
unchanged package passed; deleting `evidence/official-balance.json`, replacing
`README.md`, and adding a normal unexpected file each produced exit 1 and
`FAIL` as required.

### P1 — Cache files are silently excluded instead of rejected

`procedural-animation-toolkit(v8.2)/scripts/verify_release.py:10` removes every
file below a `__pycache__` directory from the observed package inventory. A
controlled package copy containing
`scripts/__pycache__/unexpected.pyc` therefore exited 0 with `status: PASS`.
The real review worktree also contained a generated
`scripts/__pycache__/glb_math.cpython-313.pyc`, and the positive package run
still passed.

This violates acceptance check 4 in `reports/V8-2-RELEASE/plan.md:42`, which
requires rejection of any cache/temp/failed candidate, and contradicts the
claim at `reports/V8-2-RELEASE/summary.md:42-44` that the verifier requires an
exact inventory and rejects extras. It also allows an arbitrarily large file
under `__pycache__` to bypass both inventory and size checks.

Required fix: prevent verifier execution from generating bytecode caches, then
enumerate every package file except the manifest itself. Explicitly fail if a
cache/temp/rejected path is present; do not filter prohibited paths out before
the exact-inventory comparison. Re-run the positive case and the cache-negative
case on the exact fixed head.

### Re-pin disposition

No implementation or media was modified by this review. Because P1 remains
non-zero, this appended review is intentionally uncommitted and unsigned.
