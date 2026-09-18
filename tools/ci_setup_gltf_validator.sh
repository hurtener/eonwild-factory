#!/usr/bin/env bash
# Install and smoke-test the actual Khronos validator, never an acceptance stub.
set -euo pipefail
: "${RUNNER_TEMP:?}"
: "${GITHUB_PATH:?}"
case "$(uname -s)" in
  Darwin) platform=macos64; expected='bce89ceea00b4d3191a8779018f41744b84a4539b127465d63ba83ad0f243fef' ;;
  Linux) platform=linux64; expected='' ;;
  *) printf 'Unsupported glTF validator platform\n' >&2; exit 1 ;;
esac
version='2.0.0-dev.3.10'
destination="$RUNNER_TEMP/gltf-validator-$version"
mkdir -p "$destination"
archive="gltf_validator-$version-$platform.tar.xz"
curl --fail --location --retry 2 "https://github.com/KhronosGroup/glTF-Validator/releases/download/$version/$archive" -o "$destination/$archive"
python - "$destination/$archive" "$expected" <<'PY'
import hashlib, pathlib, sys
path=pathlib.Path(sys.argv[1]); actual=hashlib.sha256(path.read_bytes()).hexdigest()
if sys.argv[2] and actual != sys.argv[2]: raise SystemExit('Khronos archive checksum mismatch')
path.with_suffix('.sha256').write_text(actual+'  '+path.name+'\n')
print('KHRONOS_ARCHIVE_SHA256',actual,path.name,flush=True)
PY
tar -xJf "$destination/$archive" -C "$destination"
test -f "$destination/gltf_validator"
chmod +x "$destination/gltf_validator"
# Upstream CLI does not support --version; it returns usage/error for it.
# Exercise a valid file and require its genuine structured validation result.
python - "$destination" <<'PY'
import json,pathlib,subprocess,sys
root=pathlib.Path(sys.argv[1]); source=root/'installation-smoke.gltf'
source.write_text(json.dumps({'asset':{'version':'2.0'}}))
result=subprocess.run([str(root/'gltf_validator'),'-o',str(source)],capture_output=True,text=True,check=True)
report=json.loads(result.stdout)
assert report['validatorVersion']=='2.0.0-dev.3.10'
assert report['issues']['numErrors']==0
(root/'installation-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('KHRONOS_CLI_SMOKE_PASS',report['validatorVersion'],flush=True)
PY
echo "$destination" >> "$GITHUB_PATH"
