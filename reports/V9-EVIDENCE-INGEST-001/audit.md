# V9 evidence ingest audit

Status: **BLOCKED_PENDING_RIGHTS_CONFIRMATION**

This is an external technical receipt manifest, not a media-ingest approval.
The ten user-supplied MP4s were observed in the source checkout, technically
probed, and recorded by exact source path, SHA-256, byte size, stream facts,
and filename-derived candidate mappings. The duplicate productized copies
were removed after the receipt checks. No stored media remains in the
productized worktree, and no row is usable as engine or reference input until
the user confirms project ownership or reuse rights.

## Scope and repository identity

| Field | Observed value |
|---|---|
| Source root (preserved) | `/Volumes/m2-extended-disk/Repos/eonwild-factory/assets/examples/tarbosaurus/v9_evidence` |
| Productized worktree | `/Volumes/m2-extended-disk/Repos/eonwild-factory-v8-3-hip` |
| Productized stored root | **none; ten duplicate MP4s removed** |
| Target HEAD before ingest | `85de1f2ceaa75427f74090a47d2b6a1ca3c6022a` |
| Earlier V8.3 audit HEAD | `195a8b4707997b3309f86f8821217ed1d7e9c22a` (ancestor of target HEAD) |
| Source HEAD observed | `aca1eab3f6e9f6970cf8a8281f4440a74f8551d3` |
| Expected / received / stored files | `10 / 10 / 0` regular MP4s |
| Historical copy processing | `cp -p` followed by `chmod 0644`; no re-encoding |
| Current media disposition | external receipt only; rights unresolved; not usable as motion input |
| Engine, motion, GLB changes | `false` |

The external source directory is the authority and remains untouched. The
productized directory is intentionally not an archive or a usable media
source. `audit.json` is authoritative for the complete per-file record and
explicitly sets `stored_path` and `stored_path_absolute` to `null`,
`copied`/`committed`/`usable_as_motion_input` to `false`, and rights to
`unresolved` for every row.

## Exact technical inventory

Metadata was collected with `ffprobe` 9.0.1 from the source bytes. The hashes
and byte sizes were rechecked after probing and before the historical copy;
the source files were rehashed after the productized duplicates were removed.

| File | SHA-256 | Bytes | Codec | Dimensions | FPS / frames | Duration (s) | Audio |
|---|---|---:|---|---:|---:|---:|---|
| `BITE MISS + RECOVERY — front three-quarter.mp4` | `9fe404e4075c206a251c853d026dcf648b2fe16aa020233b67a0f95486db5629` | 6,192,005 | H.264 / avc1 | 1280×704 | 24/1 · 193 | 8.041667 | AAC, 44.1 kHz, mono |
| `BODY SHOVE → SMALL STUMBLE → RECOVERY.mp4` | `9bc5d7925617daf9af23a48b5206ea6f2fcb2e123c665b356d0b601ece38a143` | 3,423,440 | H.264 / avc1 | 736×400 | 24/1 · 193 | 8.041667 | AAC, 48 kHz, stereo |
| `FEEDING + TEAR:PULL — fixed side.mp4` | `e56f2dc9ecc22716892b36d7559bf5cb348dee3459ca725dc7ae4205d98c7e43` | 2,321,904 | H.264 / avc1 | 736×400 | 24/1 · 145 | 6.041667 | AAC, 48 kHz, stereo |
| `GROUNDED COMMITTED BITE — fixed side.mp4` | `fcc0076f06b2b4c1f59afdb0b28e1d2d1067d6ceeb5c55f06f1866e12e9688e8` | 2,528,271 | H.264 / avc1 | 736×400 | 24/1 · 193 | 8.041667 | AAC, 48 kHz, stereo |
| `LISTEN REACTION — front three-quarter.mp4` | `4c93b18c8482e440ce3d13be57a4986cbb929652031561acb68f0863415bce27` | 1,653,853 | H.264 / avc1 | 736×400 | 24/1 · 193 | 8.041667 | AAC, 48 kHz, stereo |
| `RUN START-RUN-RUN STOP.mp4` | `2abe624212986285f22d2ee4b3f3e579e2ad7637ca2cba635af92b211c58a478` | 3,120,966 | H.264 / avc1 | 736×400 | 24/1 · 193 | 8.041667 | AAC, 48 kHz, stereo |
| `running-sustained-left.mp4` | `d1ba1e31e0cbf9ee8a4c0a24c877f2797b22ecb376124d529193eee975d6c9eb` | 1,808,155 | H.264 / avc1 | 736×400 | 24/1 · 145 | 6.041667 | AAC, 48 kHz, stereo |
| `sprint-left.mp4` | `6f32bc7ac3a51db67b08a8904f732e168513fa11b0ae94da4b336cce09e518b1` | 3,100,395 | H.264 / avc1 | 736×400 | 24/1 · 145 | 6.041667 | AAC, 48 kHz, stereo |
| `walking-back-gauge.mp4` | `318e9bbd5e9e0d0c9872e9a0f76e067ef94e5bc28a1329adc7f84ce9af22a65a` | 1,174,906 | H.264 / avc1 | 736×400 | 24/1 · 145 | 6.041667 | AAC, 48 kHz, stereo |
| `walking-front-gauge.mp4` | `2f6ad8626eebf01cd92b58f6cc75e342cff784130f265ccc0d2cee099b9af22e` | 1,326,486 | H.264 / avc1 | 736×400 | 24/1 · 145 | 6.041667 | AAC, 48 kHz, stereo |

The first file has its primary H.264 video and AAC audio stream. The other
nine also contain an attached-picture MJPEG stream at stream index 2,
736×400, with `attached_pic=1`; it is auxiliary container metadata, not a
second motion video. The full stream records are retained in `audit.json`.

All ten primary streams are 24 fps, not the requested 60 fps. These bytes are
therefore lower-confidence timing references and are insufficient for 60 fps,
sub-frame, or native-speed phase validation. No retiming or frame synthesis
was performed.

## Filename-derived candidate bindings

Bindings are bookkeeping only. This ingest did not visually review or
adjudicate choreography, contacts, gait, stance, foot heading, COM, forces,
or biological behavior.

| File | Package | Candidate labels | Binding status |
|---|---|---|---|
| `BITE MISS + RECOVERY — front three-quarter.mp4` | `R-BITE` | `tarbosaurus_bite_miss_recovery` / `quick_bite_miss_recovery` | filename-only; not adjudicated |
| `BODY SHOVE → SMALL STUMBLE → RECOVERY.mp4` | `R-SHOVE-STUMBLE` | `tarbosaurus_body_shove`, `tarbosaurus_stumble` / `body_shove`, `stumble` | filename-only; not adjudicated |
| `FEEDING + TEAR:PULL — fixed side.mp4` | `R-FEED` | `tarbosaurus_head_down_feeding`, `tarbosaurus_tear_pull` / `head_down_feeding`, `tear_pull` | filename-only; not adjudicated |
| `GROUNDED COMMITTED BITE — fixed side.mp4` | `R-BITE` | `tarbosaurus_committed_power_bite` / `committed_grounded_bite` | filename-only; not adjudicated |
| `LISTEN REACTION — front three-quarter.mp4` | `R-LISTEN` | `tarbosaurus_listen_reaction` / `listen_reaction` | filename-only; not adjudicated |
| `RUN START-RUN-RUN STOP.mp4` | `R-GAIT` | `tarbosaurus_run_start`, `tarbosaurus_run`, `tarbosaurus_run_stop` / `run_start`, `run_loop`, `run_stop` | filename-only; not separate-take proof |
| `running-sustained-left.mp4` | `R-GAIT` | `tarbosaurus_run` / `run_loop` | filename-only; not adjudicated |
| `sprint-left.mp4` | `R-GAIT` | `tarbosaurus_sprint` / `sprint_loop` | filename-only; not adjudicated |
| `walking-back-gauge.mp4` | `R-GAIT` | `tarbosaurus_walk`, `tarbosaurus_fast_walk` / gauge-labeled walking reference | filename-only; not state/metric proof |
| `walking-front-gauge.mp4` | `R-GAIT` | `tarbosaurus_walk`, `tarbosaurus_fast_walk` / gauge-labeled walking reference | filename-only; not state/metric proof |

## Coverage and provenance disposition

The filenames cover candidate namespaces `R-GAIT`, `R-LISTEN`, `R-BITE`,
`R-FEED`, and `R-SHOVE-STUMBLE` for receipt bookkeeping. They do not close
any requested capture or acceptance gate. Remaining gaps are:

- native-speed 60 fps timing and sub-frame validation for every dynamic take;
- independent fixed-camera pairing, scale/lens consistency, full-body framing,
  floor/contact visibility, and phase-boundary adjudication;
- separately evidenced `fast_walk_loop`, `quick_bite_hit`, and
  `low_downward_bite` takes;
- any accepted gait, support-width, foot-heading, COM, force, contact, or
  biological claim.

The clips are **user-supplied art-direction/choreography evidence**, not
scientific truth, fossil measurements, or proof of Tarbosaurus kinetics.
Generator/tool, original source, creator identity, license, commercial-use
status, prompt, seed, human modifications, reviewer, and AI-content disclosure
are unresolved. No rights are inferred from receipt or filename. The clips
remain unavailable for engine/reference use until the user confirms project
ownership or reuse rights.

## Non-modification statement

The source files were preserved. Only the ten productized duplicate media
files and the report files listed in `plan.md` are in this remediation scope.
No engine, motion program, schema, GLB, animation asset, or source research
file was changed. Changes are intentionally uncommitted for review.
