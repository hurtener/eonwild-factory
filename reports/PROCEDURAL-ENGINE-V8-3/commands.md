# Verification commands

Run all tests from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Focused channel contracts:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_channels -v
```

The combined suite covers exact double build and render, stable/working/direct
resolution, schema and stale-state failures, metadata lock changes, ordinary
command immutability, explicit approved stable transition, immutable history,
promotion evidence, and all retained negative cases.

Installed entry-point smoke (in an isolated virtual environment with the
declared dependency available):

```sh
eonwild-motion --help
```
