#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
EXPECTED_GIT_ENTRY_HASH="c4f4905f2974aa751a7fe0485a44d194898ead71280992c34d0129dc81362119"
PATHSPEC="procedural-animation-toolkit(v5)"

actual="$({ git -C "$REPO" ls-files -s -- "$PATHSPEC"; } | shasum -a 256 | awk '{print $1}')"
if [[ "$actual" != "$EXPECTED_GIT_ENTRY_HASH" ]]; then
  echo "V5 tracked-entry hash mismatch: expected $EXPECTED_GIT_ENTRY_HASH, got $actual" >&2
  exit 1
fi
if [[ -n "$(git -C "$REPO" status --porcelain=v1 --untracked-files=all -- "$PATHSPEC")" ]]; then
  echo "V5 has staged, unstaged, or untracked changes" >&2
  git -C "$REPO" status --short -- "$PATHSPEC" >&2
  exit 1
fi
echo "V5 immutable: $actual"
