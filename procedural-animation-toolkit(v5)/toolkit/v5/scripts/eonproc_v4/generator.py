"""High-level V4 Tarbosaurus animation factory."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import json
import math

import numpy as np

from eonproc_v3.gltf_io import GlbAsset, sha256_file
from eonproc_v3.rig import SemanticMap

from .actions import ActionGenerator
from .clip import AnimationClip
from .locomotion import (
    TerrainAwareLocomotionGenerator,
    constant_schedule,
    speed_transition_schedule,
)
from .path import EasedArcPath
from .profile import BipedV4Profile
from .terrain import FlatTerrain, PlaneTerrain, ProceduralTerrain
from .transitions import pose_transition, phase_matched_loop_transition


class TarbosaurusV4Generator:
    def __init__(self, asset: GlbAsset, semantics: SemanticMap, profile: BipedV4Profile):
        self.asset = asset
        self.semantics = semantics
        self.profile = profile
        self.locomotion = TerrainAwareLocomotionGenerator(asset, semantics, profile)
        self.actions = ActionGenerator(self.locomotion)
        self.clips: list[AnimationClip] = []
        self.report: dict[str, Any] = {}

    def _add_locomotion(self, schedule) -> tuple[AnimationClip, AnimationClip | None]:
        import sys, time
        started = time.time()
        print(f"[v4] generating {schedule.name}", file=sys.stderr, flush=True)
        result = self.locomotion.generate_schedule(schedule, keep_world_matrices=False)
        print(f"[v4] completed {schedule.name} in {time.time()-started:.1f}s", file=sys.stderr, flush=True)
        self.clips.append(result.clip)
        if result.in_place_clip is not None:
            self.clips.append(result.in_place_clip)
        return result.clip, result.in_place_clip

    def generate_all(self) -> list[AnimationClip]:
        self.clips = []
        g = self.locomotion
        p = self.profile
        flat = FlatTerrain(g.mesh_ground)

        walk_root, walk_inplace = self._add_locomotion(constant_schedule(
            "PROC_WALK_RELAXED_V4_ROOTMOTION", g, cycles=2.0, terrain=flat,
            cycle_hz=p.cycle_hz, stride_scale=1.0, loop=True,
            tags=("walk", "relaxed", "reference_fitted"),
        ))

        uneven = ProceduralTerrain(
            amplitude=g.hip_height * p.uneven_terrain_amplitude_hip_fraction,
            wavelength=p.uneven_terrain_wavelength_m,
            secondary_amplitude=g.hip_height * p.uneven_terrain_amplitude_hip_fraction * 0.24,
            secondary_wavelength=p.uneven_terrain_wavelength_m * 0.48,
        )
        terrain_root, terrain_inplace = self._add_locomotion(constant_schedule(
            "PROC_WALK_UNEVEN_TERRAIN_V4_ROOTMOTION", g, cycles=2.0, terrain=uneven,
            cycle_hz=p.cycle_hz * 0.94, stride_scale=0.90, loop=False,
            tags=("walk", "terrain", "uneven", "sole_collision"),
        ))

        slope = PlaneTerrain.from_slopes(forward_slope=0.075, height=g.mesh_ground)
        slope_root, slope_inplace = self._add_locomotion(constant_schedule(
            "PROC_WALK_UPSLOPE_V4_ROOTMOTION", g, cycles=2.0, terrain=slope,
            cycle_hz=p.cycle_hz * 0.92, stride_scale=0.86, loop=False,
            tags=("walk", "terrain", "upslope"),
        ))

        def arc_factory(sign: float):
            def factory(total_distance: float):
                theta = math.radians(p.turn_default_degrees) * sign
                return EasedArcPath(
                    g.root_rest_world, g.base_basis,
                    total_distance=total_distance, angle_radians=theta,
                )
            return factory

        turn_left_root, turn_left_inplace = self._add_locomotion(constant_schedule(
            "PROC_TURN_LEFT_35_V4_ROOTMOTION", g, cycles=2.0,
            path_factory=arc_factory(1.0), terrain=flat, cycle_hz=p.cycle_hz * 0.82,
            stride_scale=0.86, loop=False, tags=("turn", "left", "locomotion"),
        ))
        turn_right_root, turn_right_inplace = self._add_locomotion(constant_schedule(
            "PROC_TURN_RIGHT_35_V4_ROOTMOTION", g, cycles=2.0,
            path_factory=arc_factory(-1.0), terrain=flat, cycle_hz=p.cycle_hz * 0.82,
            stride_scale=0.86, loop=False, tags=("turn", "right", "locomotion"),
        ))

        start_root, start_inplace = self._add_locomotion(speed_transition_schedule(
            "PROC_START_WALK_V4_ROOTMOTION", g, p.start_duration_seconds, p.start_cycles,
            accelerating=True, terrain=flat, tags=("start", "acceleration", "locomotion"),
        ))
        stop_root, stop_inplace = self._add_locomotion(speed_transition_schedule(
            "PROC_BRAKE_TO_IDLE_V4_ROOTMOTION", g, p.stop_duration_seconds, p.stop_cycles,
            accelerating=False, terrain=flat, tags=("stop", "braking", "locomotion"),
        ))

        alert_root, alert_inplace = self._add_locomotion(constant_schedule(
            "PROC_ALERT_WALK_V4_ROOTMOTION", g, cycles=2.0, terrain=flat,
            alert_amount=1.0, cycle_hz=p.alert_cycle_hz, stride_scale=p.alert_stride_scale,
            loop=True, tags=("walk", "alert", "attention"),
        ))

        import sys, time
        action_clips = []
        for action_name, factory in (("idle", self.actions.idle), ("alert_idle", self.actions.alert_idle), ("eat", self.actions.eating_loop), ("bite", self.actions.bite_attack), ("roar", self.actions.roar)):
            started = time.time()
            print(f"[v4] generating action {action_name}", file=sys.stderr, flush=True)
            action_clips.append(factory())
            print(f"[v4] completed action {action_name} in {time.time()-started:.1f}s", file=sys.stderr, flush=True)
        idle, alert_idle, eat, bite, roar = action_clips
        self.clips.extend([idle, alert_idle, eat, bite, roar])

        assert walk_inplace is not None and alert_inplace is not None
        transitions = [
            pose_transition(
                "PROC_IDLE_TO_WALK_V4", idle, walk_inplace,
                p.transition_long_seconds, p.export_sample_hz,
                source_phase=0.0, target_phase=0.0, root_name=g.root,
                tags=("transition", "idle", "walk"),
            ),
            pose_transition(
                "PROC_WALK_TO_IDLE_V4", walk_inplace, idle,
                p.transition_long_seconds, p.export_sample_hz,
                source_phase=0.5, target_phase=0.0, root_name=g.root,
                tags=("transition", "walk", "idle"),
            ),
            phase_matched_loop_transition(
                "PROC_WALK_TO_ALERT_WALK_V4", walk_inplace, alert_inplace,
                1.0 / p.cycle_hz, p.export_sample_hz, g.root,
                tags=("transition", "walk", "alert"),
            ),
            phase_matched_loop_transition(
                "PROC_ALERT_WALK_TO_WALK_V4", alert_inplace, walk_inplace,
                1.0 / p.cycle_hz, p.export_sample_hz, g.root,
                tags=("transition", "alert", "walk"),
            ),
            pose_transition(
                "PROC_IDLE_TO_ALERT_IDLE_V4", idle, alert_idle,
                p.transition_medium_seconds, p.export_sample_hz,
                source_phase=0.0, target_phase=0.0, root_name=g.root,
                tags=("transition", "idle", "alert"),
            ),
            pose_transition(
                "PROC_ALERT_IDLE_TO_IDLE_V4", alert_idle, idle,
                p.transition_medium_seconds, p.export_sample_hz,
                source_phase=0.0, target_phase=0.0, root_name=g.root,
                tags=("transition", "alert", "idle"),
            ),
            pose_transition(
                "PROC_IDLE_TO_EAT_V4", idle, eat,
                p.transition_long_seconds, p.export_sample_hz,
                source_phase=0.0, target_phase=0.0, root_name=g.root,
                tags=("transition", "idle", "eat"),
            ),
            pose_transition(
                "PROC_EAT_TO_IDLE_V4", eat, idle,
                p.transition_long_seconds, p.export_sample_hz,
                source_phase=0.0, target_phase=0.0, root_name=g.root,
                tags=("transition", "eat", "idle"),
            ),
            pose_transition(
                "PROC_IDLE_TO_ROAR_READY_V4", idle, roar,
                p.transition_short_seconds, p.export_sample_hz,
                source_phase=0.0, target_phase=0.0, root_name=g.root,
                tags=("transition", "idle", "roar"),
            ),
            pose_transition(
                "PROC_ROAR_TO_IDLE_V4", roar, idle,
                p.transition_medium_seconds, p.export_sample_hz,
                source_phase=1.0, target_phase=0.0, root_name=g.root,
                tags=("transition", "roar", "idle"),
            ),
            # Direct action/locomotion bridges. Runtime may still route through
            # braking/idle when more space is available, but these clips make
            # urgent browser interactions deterministic and phase-safe.
            pose_transition(
                "PROC_WALK_TO_BITE_READY_V4", walk_inplace, bite,
                p.transition_short_seconds, p.export_sample_hz,
                source_phase=0.50, target_phase=0.0, root_name=g.root,
                tags=("transition", "walk", "bite", "urgent"),
            ),
            pose_transition(
                "PROC_BITE_TO_WALK_V4", bite, walk_inplace,
                p.transition_medium_seconds, p.export_sample_hz,
                source_phase=1.0, target_phase=0.0, root_name=g.root,
                tags=("transition", "bite", "walk", "recovery"),
            ),
            pose_transition(
                "PROC_WALK_TO_ROAR_READY_V4", walk_inplace, roar,
                p.transition_medium_seconds, p.export_sample_hz,
                source_phase=0.50, target_phase=0.0, root_name=g.root,
                tags=("transition", "walk", "roar"),
            ),
            pose_transition(
                "PROC_ROAR_TO_WALK_V4", roar, walk_inplace,
                p.transition_long_seconds, p.export_sample_hz,
                source_phase=1.0, target_phase=0.0, root_name=g.root,
                tags=("transition", "roar", "walk", "recovery"),
            ),
            pose_transition(
                "PROC_WALK_TO_EAT_V4", walk_inplace, eat,
                p.transition_long_seconds, p.export_sample_hz,
                source_phase=0.50, target_phase=0.0, root_name=g.root,
                tags=("transition", "walk", "eat", "settle"),
            ),
            pose_transition(
                "PROC_EAT_TO_WALK_V4", eat, walk_inplace,
                p.transition_long_seconds, p.export_sample_hz,
                source_phase=0.0, target_phase=0.0, root_name=g.root,
                tags=("transition", "eat", "walk", "rise"),
            ),
        ]
        self.clips.extend(transitions)

        names = [clip.name for clip in self.clips]
        if len(names) != len(set(names)):
            duplicates = sorted({name for name in names if names.count(name) > 1})
            raise ValueError(f"Duplicate V4 clip names: {duplicates}")

        gates = {}
        for clip in self.clips:
            gates[clip.name] = clip.diagnostics.get("quality_gates", {})
        critical_gate_sets = [
            values for name, values in gates.items()
            if values and (
                any(token in name for token in ("WALK", "TURN", "START", "BRAKE"))
                or any(token in name for token in ("IDLE_BREATH", "ALERT_IDLE", "EAT_LOOP", "BITE_ATTACK", "ROAR_V4"))
            )
        ]
        automated_pass = bool(critical_gate_sets) and all(
            bool(value) for gate_set in critical_gate_sets for value in gate_set.values()
        )
        self.report = {
            "status": "PASS_WITH_PERCEPTUAL_REVIEW_REQUIRED" if automated_pass else "FAIL_AUTOMATED_QUALITY_GATES",
            "automated_quality_pass": automated_pass,
            "version": "4.0.0",
            "profile": asdict(p),
            "rig": {
                "node_count": len(self.asset.nodes),
                "skin_joint_count": len(self.asset.skin_data()[0]),
                "semantic_tag_count": len(self.semantics.tags),
                "unique_semantic_bones": len(set(self.semantics.tags.values())),
                "driven_bone_count": len(g.driven_bones),
                "sole_model": g.sole.metadata(),
            },
            "clips": {
                clip.name: {
                    "duration_seconds": clip.duration,
                    "sample_count": len(clip.times),
                    "root_motion": clip.extras.get("rootMotion", False),
                    "loop": clip.extras.get("loop", False),
                    "tags": clip.extras.get("tags", []),
                    "diagnostics": clip.diagnostics,
                }
                for clip in self.clips
            },
            "quality_gate_summary": gates,
            "implementation": {
                "reference_fitted_timing": True,
                "vertex_level_sole_collision": True,
                "terrain_height_and_normal_adaptation": True,
                "curved_path_turning": True,
                "acceleration_and_braking": True,
                "alert_locomotion": True,
                "eating": True,
                "bite_attack": True,
                "roar": True,
                "action_locomotion_transitions": True,
                "runtime_event_markers": True,
            },
        }
        return self.clips

    def animation_specs(self) -> list[dict[str, Any]]:
        if not self.clips:
            self.generate_all()
        return [clip.gltf_spec() for clip in self.clips]

    def write(self, output_dir: str | Path, source_path: str | Path, bone_map_path: str | Path) -> dict[str, Path]:
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        if not self.clips:
            self.generate_all()
        glb_path = output / "tarbosaurus_procedural_v4_animation_pack.glb"
        self.asset.write_animations(glb_path, self.animation_specs(), replace_existing=True)
        report = {
            **self.report,
            "input": {
                "asset": str(Path(source_path).resolve()),
                "asset_sha256": sha256_file(source_path),
                "bone_map": str(Path(bone_map_path).resolve()),
                "bone_map_sha256": sha256_file(bone_map_path),
            },
            "output": {
                "animated_glb": str(glb_path),
                "animated_glb_sha256": sha256_file(glb_path),
                "clip_count": len(self.clips),
            },
        }
        report_path = output / "procedural-v4-report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        self.profile.to_json(output / "resolved-profile-v4.json")
        manifest = self.manifest(glb_path.name)
        manifest_path = output / "animation-manifest.v4.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return {"glb": glb_path, "report": report_path, "manifest": manifest_path}

    def _event_markers(self, clip: AnimationClip) -> list[dict[str, Any]]:
        """Deterministic runtime cues for audio, VFX, hit windows and state commits."""
        name = clip.name
        duration = float(clip.duration)
        events: list[dict[str, Any]] = []
        diagnostics = clip.diagnostics or {}
        cycles = float(diagnostics.get("phase_advance_cycles", 0.0) or 0.0)
        constant_gait = any(token in name for token in (
            "WALK_RELAXED", "WALK_UNEVEN", "WALK_UPSLOPE", "TURN_LEFT",
            "TURN_RIGHT", "ALERT_WALK",
        ))
        if constant_gait and cycles > 0.0:
            stop = int(math.floor(cycles + 1e-9))
            for step in range(stop + 1):
                left_t = duration * step / cycles
                if left_t < duration - 1e-6 or not clip.extras.get("loop", False):
                    events.append({"timeSeconds": left_t, "type": "foot_contact", "side": "left", "phase": float(step)})
                right_phase = step + 0.5
                if right_phase <= cycles + 1e-9:
                    right_t = duration * right_phase / cycles
                    if right_t < duration - 1e-6 or not clip.extras.get("loop", False):
                        events.append({"timeSeconds": right_t, "type": "foot_contact", "side": "right", "phase": right_phase})
        if name == "PROC_START_WALK_V4_ROOTMOTION" or name == "PROC_START_WALK_V4_INPLACE":
            events.extend([
                {"timeSeconds": 0.0, "type": "locomotion_start"},
                {"timeSeconds": duration * 0.62, "type": "locomotion_committed"},
            ])
        elif name == "PROC_BRAKE_TO_IDLE_V4_ROOTMOTION" or name == "PROC_BRAKE_TO_IDLE_V4_INPLACE":
            events.extend([
                {"timeSeconds": 0.0, "type": "brake_start"},
                {"timeSeconds": duration, "type": "idle_settled"},
            ])
        elif name == "PROC_BITE_ATTACK_V4":
            events.extend([
                {"timeSeconds": duration * self.profile.bite_anticipation_fraction, "type": "attack_release"},
                {"timeSeconds": duration * self.profile.bite_contact_fraction, "type": "bite_contact", "windowSeconds": 0.10},
                {"timeSeconds": duration * self.profile.bite_recovery_fraction, "type": "recovery_start"},
            ])
        elif name == "PROC_ROAR_V4":
            events.extend([
                {"timeSeconds": duration * self.profile.roar_inhale_fraction, "type": "inhale_complete"},
                {"timeSeconds": duration * self.profile.roar_peak_fraction, "type": "roar_peak"},
                {"timeSeconds": duration * self.profile.roar_release_fraction, "type": "roar_release"},
            ])
        elif name == "PROC_EAT_LOOP_V4":
            for index in range(self.profile.eating_bite_count):
                cycle_center = (index + 0.58) / self.profile.eating_bite_count
                events.append({"timeSeconds": duration * cycle_center, "type": "feeding_bite", "index": index})
        if "_TO_" in name:
            events.append({"timeSeconds": duration, "type": "transition_commit"})
        events.sort(key=lambda item: (float(item["timeSeconds"]), str(item["type"])))
        return events

    def manifest(self, asset_name: str) -> dict[str, Any]:
        return {
            "schema": "eonwild.animation-manifest.v4",
            "version": "4.0.0",
            "asset": asset_name,
            "family": "large_theropod_biped",
            "speciesProfile": self.profile.name,
            "sampleHz": self.profile.export_sample_hz,
            "clips": [
                {
                    "name": clip.name,
                    "durationSeconds": clip.duration,
                    "loop": bool(clip.extras.get("loop", False)),
                    "rootMotion": bool(clip.extras.get("rootMotion", False)),
                    "tags": clip.extras.get("tags", []),
                    "terrain": clip.extras.get("terrain"),
                    "path": clip.extras.get("path"),
                    "events": self._event_markers(clip),
                }
                for clip in self.clips
            ],
            "stateGraph": {
                "initial": "idle",
                "states": {
                    "idle": {"clip": "PROC_IDLE_BREATH_V4"},
                    "walk": {"clip": "PROC_WALK_RELAXED_V4_INPLACE", "speedMps": self.locomotion.speed},
                    "alert_idle": {"clip": "PROC_ALERT_IDLE_V4"},
                    "alert_walk": {"clip": "PROC_ALERT_WALK_V4_INPLACE"},
                    "eat": {"clip": "PROC_EAT_LOOP_V4"},
                },
                "oneShots": {
                    "bite": {"clip": "PROC_BITE_ATTACK_V4", "return": "previous_locomotion_or_idle", "priority": 70},
                    "roar": {"clip": "PROC_ROAR_V4", "return": "previous_locomotion_or_idle", "priority": 60},
                },
                "transitions": [
                    {"from": "idle", "to": "walk", "clip": "PROC_IDLE_TO_WALK_V4"},
                    {"from": "walk", "to": "idle", "clip": "PROC_WALK_TO_IDLE_V4"},
                    {"from": "walk", "to": "alert_walk", "clip": "PROC_WALK_TO_ALERT_WALK_V4", "phaseMatched": True},
                    {"from": "alert_walk", "to": "walk", "clip": "PROC_ALERT_WALK_TO_WALK_V4", "phaseMatched": True},
                    {"from": "idle", "to": "eat", "clip": "PROC_IDLE_TO_EAT_V4"},
                    {"from": "eat", "to": "idle", "clip": "PROC_EAT_TO_IDLE_V4"},
                    {"from": "walk", "to": "bite", "clip": "PROC_WALK_TO_BITE_READY_V4"},
                    {"from": "bite", "to": "walk", "clip": "PROC_BITE_TO_WALK_V4"},
                    {"from": "walk", "to": "roar", "clip": "PROC_WALK_TO_ROAR_READY_V4"},
                    {"from": "roar", "to": "walk", "clip": "PROC_ROAR_TO_WALK_V4"},
                    {"from": "walk", "to": "eat", "clip": "PROC_WALK_TO_EAT_V4"},
                    {"from": "eat", "to": "walk", "clip": "PROC_EAT_TO_WALK_V4"},
                ],
            },
            "runtimeContracts": {
                "terrainQuery": "heightNormal(x,z)->{height,normal}",
                "inPlaceLocomotion": "advance actor using recommended speed and preserve gait phase",
                "turning": "prefer curved-path root clips for authored turns; use runtime foot-IK overlay for arbitrary curvature",
                "actionPriority": ["bite", "roar", "eat", "alert", "locomotion", "idle"],
                "eventMarkers": "consume manifest clip.events for footstep audio, hit windows, vocal peaks and transition commits",
            },
        }
