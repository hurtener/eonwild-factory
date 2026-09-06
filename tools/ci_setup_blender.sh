#!/usr/bin/env bash
# CI toolchain setup, not a source-recovery or repository-write workflow.
# Use the same Blender release as the recorded native-motion verification.
set -euo pipefail
: "${RUNNER_TEMP:?GitHub runner temporary directory is required}"
: "${GITHUB_PATH:?GitHub runner path file is required}"
download="$RUNNER_TEMP/blender-download"
mkdir -p "$download"
cd "$download"
base='https://download.blender.org/release/Blender5.2'
curl --fail --location --retry 2 "$base/blender-5.2.0-linux-x64.tar.xz" -o blender-5.2.0-linux-x64.tar.xz
curl --fail --location --retry 2 "$base/blender-5.2.0.sha256" -o blender-5.2.0.sha256
grep -E ' [*]?blender-5.2.0-linux-x64.tar.xz$' blender-5.2.0.sha256 > selected.sha256
test "$(wc -l < selected.sha256)" -eq 1
sha256sum --check selected.sha256
tar -xJf blender-5.2.0-linux-x64.tar.xz -C "$RUNNER_TEMP"
echo "$RUNNER_TEMP/blender-5.2.0-linux-x64" >> "$GITHUB_PATH"
sudo apt-get update -qq
sudo apt-get install -y ffmpeg libxrender1 libxi6 libxfixes3 libxkbcommon0 libsm6
