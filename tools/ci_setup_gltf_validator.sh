#!/usr/bin/env bash
# Install the actual Khronos validator, not an acceptance stub.
# v2.0.0-dev.3.10 is the upstream prerelease with published native CLI assets.
set -euo pipefail
: "${RUNNER_TEMP:?}"
: "${GITHUB_PATH:?}"
case "$(uname -s)" in
  Darwin) platform=macos64 ;;
  Linux) platform=linux64 ;;
  *) printf 'Unsupported glTF validator platform\n' >&2; exit 1 ;;
esac
version='2.0.0-dev.3.10'
destination="$RUNNER_TEMP/gltf-validator-$version"
mkdir -p "$destination"
archive="gltf_validator-$version-$platform.tar.xz"
curl --fail --location --retry 2 "https://github.com/KhronosGroup/glTF-Validator/releases/download/$version/$archive" -o "$destination/$archive"
python - "$destination/$archive" <<'PY'
import hashlib, pathlib, sys
path=pathlib.Path(sys.argv[1])
print('KHRONOS_ARCHIVE_SHA256',hashlib.sha256(path.read_bytes()).hexdigest(),path.name,flush=True)
PY
tar -xJf "$destination/$archive" -C "$destination"
test -f "$destination/gltf_validator"
chmod +x "$destination/gltf_validator"
"$destination/gltf_validator" --version
echo "$destination" >> "$GITHUB_PATH"
