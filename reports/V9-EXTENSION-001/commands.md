# V9-EXTENSION-001 command record

## User-supplied narrow-gauge sheet ingest

The supplied PNG was copied byte-for-byte to the report reference directory.
`file`, `sips`, and `shasum -a 256` recorded PNG/RGB, 1448 x 1086, and SHA-256
`d8416309bab3a7fa48d4f15659cef15504304c5e94490fc5b2b5317615fb1b2d`.
No conversion or recompression was performed.

Five additional 1448 x 1086 RGB PNG sheets were copied byte-for-byte. Their
SHA-256 values are recorded in
`references/user-generated/tarbosaurus-v9-reference-sheets.provenance.json`.

Commands were run from:

`/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip`

The report is documentation-only. No engine or motion command was run.

## Scope and preservation checks

```sh
git status --short --branch
```

Observed in an intermediate status snapshot before editing:

```text
## codex/procedural-engine...origin/main [ahead 10]
?? uv.lock
```

This was a transient untracked path. No ownership is inferred; it was not
inspected or edited and was absent from the final snapshot.

During concurrent validation, these additional untracked paths were visible
and were also preserved without inspection or modification:

```text
reports/V9-EXTENSION-CONTRACTS-001/
reports/V9-GAIT-FOOT-AUDIT-001/
schemas/motion/v9/
```

```sh
mkdir -p reports/V9-EXTENSION-001
```

## JSON and coverage checks

```sh
python3 -m json.tool reports/V9-EXTENSION-001/reference-coverage.json >/dev/null && echo 'json_parse=PASS'
```

Observed:

```text
json_parse=PASS
```

```sh
ruby -rjson -e 'j=JSON.parse(File.read("reports/V9-EXTENSION-001/reference-coverage.json")); a=j.fetch("animations"); b=j.fetch("bridges"); abort "animation_count" unless a.length == 29; abort "bridge_count" unless b.length == 16; abort "animation_ids" unless a.map{|x|x.fetch("id")}.uniq.length == 29; abort "bridge_ids" unless b.map{|x|x.fetch("id")}.uniq.length == 16; allowed=%w[A B C D E]; abort "animation_class" unless a.all?{|x|allowed.include?(x.fetch("class"))}; abort "bridge_class" unless b.all?{|x|allowed.include?(x.fetch("class"))}; shots=j.fetch("capture_packages").map{|x|x.fetch("id")}; refs=(a+b).flat_map{|x|x.fetch("required_capture_packages")}; abort "missing_shot_ref" unless (refs-shots).empty?; puts "animations=#{a.length} bridges=#{b.length} classes=#{(a+b).group_by{|x|x["class"]}.transform_values(&:length)} shots=#{shots.length} reference_links=#{refs.length}"'
```

Observed:

```text
animations=29 bridges=16 classes={"A"=>11, "C"=>11, "B"=>2, "D"=>9, "E"=>12} shots=6 reference_links=23
```

```sh
if rg -n '[[:blank:]]+$' reports/V9-EXTENSION-001; then exit 1; else echo 'trailing_whitespace=PASS'; fi
```

Observed:

```text
trailing_whitespace=PASS
```

```sh
git diff --check -- reports/V9-EXTENSION-001
```

Observed exit status: `0`.

```sh
find reports/V9-EXTENSION-001 -maxdepth 1 -type f -print | sort
git status --short --branch
```

Expected final report files:

```text
reports/V9-EXTENSION-001/commands.md
reports/V9-EXTENSION-001/plan.md
reports/V9-EXTENSION-001/reference-coverage.json
reports/V9-EXTENSION-001/reference-coverage.md
```

The final status observed after concurrent work was:

```text
## codex/procedural-engine...origin/main [ahead 10]
?? profiles/v9/contact.left-foot.loaded.json
?? profiles/v9/contact.right-foot.loaded.json
?? profiles/v9/intent.stationary-support.json
?? profiles/v9/program.stationary-support.json
?? profiles/v9/synthetic-heavy-biped.json
?? profiles/v9/tarbosaurus-provisional.json
?? reports/V9-EXTENSION-001/commands.md
?? reports/V9-EXTENSION-001/plan.md
?? reports/V9-EXTENSION-001/reference-coverage.json
?? reports/V9-EXTENSION-001/reference-coverage.md
?? reports/V9-EXTENSION-CONTRACTS-001/plan.md
?? reports/V9-GAIT-FOOT-AUDIT-001/audit.json
?? reports/V9-GAIT-FOOT-AUDIT-001/audit.md
?? reports/V9-GAIT-FOOT-AUDIT-001/commands.md
?? reports/V9-GAIT-FOOT-AUDIT-001/narrow-gauge-contract.json
?? reports/V9-GAIT-FOOT-AUDIT-001/plan.md
?? schemas/motion/v9/body-instance-profile.v1.schema.json
?? schemas/motion/v9/centroidal-contact-plan.v1.schema.json
?? schemas/motion/v9/contact-state.v1.schema.json
?? schemas/motion/v9/motion-intent.v1.schema.json
?? schemas/motion/v9/motion-program.v1.schema.json
?? schemas/motion/v9/stationary-support-evidence.v1.schema.json
?? src/eonwild_motion/contracts/v9_loader.py
?? src/eonwild_motion/contracts/v9_migration.py
?? src/eonwild_motion/contracts/v9_models.py
```

The transient `uv.lock` was not present in this final snapshot and was not
edited or attributed to a user. All other non-report entries above were pre-existing or
concurrent and were not touched. No path outside `reports/V9-EXTENSION-001/`
was modified by this task.

## Final verification rerun

```sh
python3 -m json.tool reports/V9-EXTENSION-001/reference-coverage.json >/dev/null && echo 'json_parse=PASS'
```

Observed: `json_parse=PASS`.

```sh
ruby -rjson -ryaml -e 'r=JSON.parse(File.read("reports/V9-EXTENSION-001/reference-coverage.json")); c=YAML.load_file("/Volumes/m2-extended-disk/Repos/eonwild-factory/v9_extension/motions/tarbosaurus/catalog.yaml"); a=r.fetch("animations"); b=r.fetch("bridges"); abort "animation IDs" unless a.map{|x|x.fetch("id")}==c.fetch("animations").map{|x|x.fetch("id")}; expected=%w[PROC_IDLE_TO_WALK_V8_3 PROC_WALK_TO_IDLE_V8_3 PROC_WALK_TO_ALERT_WALK_V8_3 PROC_ALERT_WALK_TO_WALK_V8_3 PROC_IDLE_TO_ALERT_IDLE_V8_3 PROC_ALERT_IDLE_TO_IDLE_V8_3 PROC_IDLE_TO_FEED_V8_3 PROC_FEED_TO_IDLE_V8_3 PROC_IDLE_TO_THREAT_READY_V8_3 PROC_THREAT_TO_IDLE_V8_3 PROC_WALK_TO_BITE_READY_V8_3 PROC_BITE_TO_WALK_V8_3 PROC_WALK_TO_THREAT_READY_V8_3 PROC_THREAT_TO_WALK_V8_3 PROC_WALK_TO_FEED_V8_3 PROC_FEED_TO_WALK_V8_3]; abort "bridge IDs" unless b.map{|x|x.fetch("id")}==expected; ids=r.fetch("capture_packages").map{|x|x.fetch("id")}; links=(a+b).flat_map{|x|x.fetch("required_capture_packages")}; abort "capture links" unless (links-ids).empty?; abort "bad classes" unless (a+b).all?{|x|%w[A B C D E].include?(x.fetch("class"))}; puts "animations=#{a.length} bridges=#{b.length} exact_catalog_order=PASS capture_links=#{links.length} classes=#{(a+b).group_by{|x|x["class"]}.transform_values(&:length)}"'
```

Observed:

```text
animations=29 bridges=16 exact_catalog_order=PASS capture_links=23 classes={"A"=>11, "C"=>11, "B"=>2, "D"=>9, "E"=>12}
```

```sh
if rg -n '[[:blank:]]+$' reports/V9-EXTENSION-001; then exit 1; else echo 'trailing_whitespace=PASS'; fi
git diff --check -- reports/V9-EXTENSION-001
```

Observed: `trailing_whitespace=PASS`; tracked diff-check exit status `0`.

The final report directory contains exactly four files: `plan.md`,
`reference-coverage.md`, `reference-coverage.json`, and `commands.md`.
