#!/usr/bin/env bash
# Verify and install the recorded Blender release without changing assets.
set -euo pipefail
: "${RUNNER_TEMP:?GitHub runner temporary directory is required}"
: "${GITHUB_PATH:?GitHub runner path file is required}"
download="$RUNNER_TEMP/blender-download"
mkdir -p "$download"
cd "$download"
base='https://download.blender.org/release/Blender5.2'
case "$(uname -s)/$(uname -m)" in
  Linux/x86_64) archive='blender-5.2.0-linux-x64.tar.xz' ;;
  Darwin/arm64) archive='blender-5.2.0-macos-arm64.dmg' ;;
  *) printf 'Unsupported verified Blender platform\n' >&2; exit 1 ;;
esac
curl --fail --location --retry 2 "$base/$archive" -o "$archive"
curl --fail --location --retry 2 "$base/blender-5.2.0.sha256" -o blender-5.2.0.sha256
grep -F "$archive" blender-5.2.0.sha256 > selected.sha256
test "$(wc -l < selected.sha256 | tr -d ' ')" -eq 1
if [[ "$archive" == *.dmg ]]; then
  shasum -a 256 --check selected.sha256
  mount="$RUNNER_TEMP/blender-volume"
  hdiutil attach "$archive" -nobrowse -readonly -mountpoint "$mount"
  trap 'hdiutil detach "$mount" >/dev/null 2>&1 || true' EXIT
  mkdir -p "$RUNNER_TEMP/blender-app"
  ditto "$mount/Blender.app" "$RUNNER_TEMP/blender-app/Blender.app"
  hdiutil detach "$mount"
  trap - EXIT
  echo "$RUNNER_TEMP/blender-app/Blender.app/Contents/MacOS" >> "$GITHUB_PATH"
  command -v ffmpeg >/dev/null || brew install ffmpeg
else
  sha256sum --check selected.sha256
  tar -xJf "$archive" -C "$RUNNER_TEMP"
  echo "$RUNNER_TEMP/blender-5.2.0-linux-x64" >> "$GITHUB_PATH"
  sudo apt-get update -qq
  sudo apt-get install -y ffmpeg libxrender1 libxi6 libxfixes3 libxkbcommon0 libsm6
fi
