# Local review byte-range server

This bounded utility replaces the prior SimpleHTTP review host with an explicit-root, loopback-default server that supports one HTTP byte range. It lets browser video controls seek and replay retained evidence without changing the HTML, media, animation source or review status.

## Frozen source

The server commit is `343ff071c90747377cd9f8a6bdee4c0c482626c8`, based directly on publication head `1df29998502299e17e45d52fa315918d4a402826`. It adds only `tools/serve_review.py` and `tests/test_serve_review.py`. The root reviewer reported the exact commit **CLEAN**, with 12 focused tests passing in 6.25 seconds.

Run it from the intended document root:

```sh
uv run python tools/serve_review.py --root . --bind 127.0.0.1 --port 8877
```

The server preserves ordinary file/directory behavior and adds `Accept-Ranges: bytes`, bounded `206` responses for closed, open-ended and suffix ranges, range-aware `HEAD`, and `416` with `Content-Range: bytes */size` for malformed, multiple or unsatisfiable ranges. The CLI rejects invalid roots and ports. The default bind is loopback.

## Browser observation

Root exercised the unchanged V8/V9 comparison page in actual Chrome through the server at `127.0.0.1:8877`. All five paired views completed seek, play, pause, replay and restart checks. This is direct browser-tool observation only: the browser tool could not persist files because its allowed roots exclude this workspace. No screenshot, browser log or other saved browser artifact is claimed.

The observation verifies control behavior and HTTP media access. It does not constitute normal-speed perceptual approval, Unity parity, production hosting validation or animation approval. The unchanged page and media retain their existing hashes and review classifications.

## Publication baseline

The copied [hosted CI receipt](ci-contracts-1df2999.json), SHA-256 `64266e762b82b2bad1b825a3b677058e5c3a043b83f1ba64177ed6badaa2dba7`, binds the baseline to PR head `1df2999` and tree `e97a02ec`: 907 tests plus 21 subtests passed in 437.40 seconds on macOS arm64 with Python 3.13.15 and Khronos Validator 2.0.0-dev.3.10. The complete external job log remains at `audits/ci-contracts-1df2999.log`, SHA-256 `9c34bf378e9d3211521dc35a4db3bbd6fc88def51fbe0a7828b433ffd08fd435`.

A final local full suite is intentionally deferred until the separately reviewed canonical-anchor provider is authorized into this integration. Documentation changes do not trigger an extra broad run.
