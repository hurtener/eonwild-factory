# Verification commands and results

All commands ran from
`/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip` on 2026-08-28.

| Check | Command | Exit | Result |
|---|---|---:|---|
| Full suite | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v` | 0 | 19 passed, 0 skipped |
| Install | `python3 -m venv --system-site-packages <tmp>/venv && <tmp>/venv/bin/pip install --no-deps .` | 0 | wheel installed |
| Console entry | `<tmp>/venv/bin/eonwild-motion --help` | 0 | five commands listed |
| Build A | `python3 -m eonwild_motion build --profile profiles/v8.2/profile.json --work-root <tmp>/build-a` | 0 | PASS, exact approved SHA |
| Build B | same with `<tmp>/build-b` | 0 | PASS, byte-identical to A |
| Validate | `python3 -m eonwild_motion validate --profile profiles/v8.2/profile.json --artifact <build-a.glb> --work-root <tmp>/validate` | 0 | PASS |
| Compare | `python3 -m eonwild_motion compare --profile profiles/v8.2/profile.json --baseline 'procedural-animation-toolkit(v8.2)/input/tarbosaurus_v8_2_iteration_b_base.glb' --candidate <build-a.glb> --work-root <tmp>/compare` | 0 | PASS |
| Render | `python3 -m eonwild_motion render --profile profiles/v8.2/profile.json --artifact <build-a.glb> --work-root <tmp>/render` | 0 | PASS, real Blender PNG |
| Byte parity | `cmp <build-a.glb> <build-b.glb>` | 0 | identical |
| Engine neutrality | `rg -n -i 'Bone_|PROC_|Tarbosaurus|a2cf73|v8\\.2|v8_2|iteration|procedural-animation-toolkit' src/eonwild_motion` | 1 | no matches, expected |
| Diff hygiene | `git diff --check` | 0 | clean |

The install smoke uses the host's already installed `jsonschema` dependency
while still installing the package wheel without network access. `pyproject.toml`
declares the exact runtime dependency for a normal resolver-driven install.

## Tool versions

| Tool | Version / condition |
|---|---|
| Python | 3.14.6 |
| Blender | 5.2.0 LTS, build 2026-07-14 |
| Blender NumPy | 2.3.4 |
| jsonschema | 4.26.0 |
| glTF Validator | 2.0.0-dev.3.10 |
| FFmpeg | 9.0.1, Homebrew build with GPL codecs enabled |

Python is PSF-licensed, Blender is GPL, `jsonschema` and setuptools are MIT,
and Khronos glTF Validator is Apache-2.0. These are developer/build tools and
the slice adds no copied third-party model, texture, animation, or media.
