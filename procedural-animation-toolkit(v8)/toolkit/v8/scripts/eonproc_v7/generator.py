"""End-to-end Tarbosaurus V7 animation factory."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any
import json
import math
import sys
import time

from eonproc_v3.gltf_io import GlbAsset, sha256_file
from eonproc_v3.rig import SemanticMap
from eonproc_v4.clip import AnimationClip
from eonproc_v4.locomotion import constant_schedule, speed_transition_schedule
from eonproc_v4.path import EasedArcPath
from eonproc_v4.terrain import FlatTerrain, PlaneTerrain, ProceduralTerrain

from .actions import TarbosaurusV7ActionGenerator
from .locomotion import TarbosaurusV7LocomotionGenerator
from .profile import BipedV7Profile
from .transitions import pose_transition, phase_matched_loop_transition


class TarbosaurusV7Generator:
    def __init__(self, asset: GlbAsset, semantics: SemanticMap, profile: BipedV7Profile):
        self.asset = asset
        self.semantics = semantics
        self.profile = profile
        self.locomotion = TarbosaurusV7LocomotionGenerator(asset, semantics, profile)
        self.actions = TarbosaurusV7ActionGenerator(self.locomotion)
        self.clips: list[AnimationClip] = []
        self.report: dict[str, Any] = {}

    def _add_locomotion(self, schedule):
        started = time.time()
        print(f"[v7] generating {schedule.name}", file=sys.stderr, flush=True)
        result = self.locomotion.generate_schedule(schedule, keep_world_matrices=False)
        elapsed = time.time() - started
        print(f"[v7] completed {schedule.name} in {elapsed:.1f}s", file=sys.stderr, flush=True)
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
            "PROC_WALK_RELAXED_V7_ROOTMOTION",
            g,
            cycles=2.0,
            terrain=flat,
            cycle_hz=p.cycle_hz,
            stride_scale=1.0,
            loop=True,
            tags=("walk", "relaxed", "reference_fitted", "contact_locked", "v7"),
        ))

        uneven = ProceduralTerrain(
            amplitude=g.hip_height * p.uneven_terrain_amplitude_hip_fraction,
            wavelength=p.uneven_terrain_wavelength_m,
            secondary_amplitude=g.hip_height * p.uneven_terrain_amplitude_hip_fraction * 0.22,
            secondary_wavelength=p.uneven_terrain_wavelength_m * 0.52,
        )
        terrain_root, terrain_inplace = self._add_locomotion(constant_schedule(
            "PROC_WALK_UNEVEN_TERRAIN_V7_ROOTMOTION",
            g,
            cycles=2.0,
            terrain=uneven,
            cycle_hz=p.cycle_hz * 0.92,
            stride_scale=0.88,
            loop=False,
            tags=("walk", "terrain", "uneven", "vertex_sole", "contact_locked"),
        ))

        slope = PlaneTerrain.from_slopes(forward_slope=0.075, height=g.mesh_ground)
        slope_root, slope_inplace = self._add_locomotion(constant_schedule(
            "PROC_WALK_UPSLOPE_V7_ROOTMOTION",
            g,
            cycles=2.0,
            terrain=slope,
            cycle_hz=p.cycle_hz * 0.90,
            stride_scale=0.84,
            loop=False,
            tags=("walk", "terrain", "upslope", "contact_locked"),
        ))

        def arc_factory(sign: float):
            def factory(total_distance: float):
                return EasedArcPath(
                    g.root_rest_world,
                    g.base_basis,
                    total_distance=total_distance,
                    angle_radians=math.radians(p.turn_default_degrees) * sign,
                )
            return factory

        turn_left_root, turn_left_inplace = self._add_locomotion(constant_schedule(
            "PROC_TURN_LEFT_35_V7_ROOTMOTION",
            g,
            cycles=2.0,
            path_factory=arc_factory(+1.0),
            terrain=flat,
            cycle_hz=p.cycle_hz * p.turn_cycle_hz_scale,
            stride_scale=p.turn_stride_scale,
            loop=False,
            tags=("turn", "left", "locomotion", "head_neck_lead", "mass_counterweight"),
        ))
        turn_right_root, turn_right_inplace = self._add_locomotion(constant_schedule(
            "PROC_TURN_RIGHT_35_V7_ROOTMOTION",
            g,
            cycles=2.0,
            path_factory=arc_factory(-1.0),
            terrain=flat,
            cycle_hz=p.cycle_hz * p.turn_cycle_hz_scale,
            stride_scale=p.turn_stride_scale,
            loop=False,
            tags=("turn", "right", "locomotion", "head_neck_lead", "mass_counterweight"),
        ))

        start_root, start_inplace = self._add_locomotion(speed_transition_schedule(
            "PROC_START_WALK_V7_ROOTMOTION",
            g,
            p.start_duration_seconds,
            p.start_cycles,
            accelerating=True,
            terrain=flat,
            tags=("start", "acceleration", "locomotion", "contact_locked"),
        ))
        stop_root, stop_inplace = self._add_locomotion(speed_transition_schedule(
            "PROC_BRAKE_TO_IDLE_V7_ROOTMOTION",
            g,
            p.stop_duration_seconds,
            p.stop_cycles,
            accelerating=False,
            terrain=flat,
            tags=("stop", "braking", "locomotion", "contact_locked"),
        ))

        alert_root, alert_inplace = self._add_locomotion(constant_schedule(
            "PROC_ALERT_WALK_V7_ROOTMOTION",
            g,
            cycles=2.0,
            terrain=flat,
            alert_amount=1.0,
            cycle_hz=p.alert_cycle_hz,
            stride_scale=p.alert_stride_scale,
            loop=True,
            tags=("walk", "alert", "attention", "contact_locked"),
        ))

        action_factories = (
            ("idle", self.actions.idle),
            ("alert_idle", self.actions.alert_idle),
            ("eat", self.actions.eating_loop),
            ("bite_left", lambda: self.actions.bite_attack("l")),
            ("bite_right", lambda: self.actions.bite_attack("r")),
            ("roar", self.actions.roar),
        )
        action_clips: list[AnimationClip] = []
        for label, factory in action_factories:
            started = time.time()
            print(f"[v7] generating action {label}", file=sys.stderr, flush=True)
            action_clips.append(factory())
            print(f"[v7] completed action {label} in {time.time() - started:.1f}s", file=sys.stderr, flush=True)
        idle, alert_idle, eat, bite_left, bite_right, roar = action_clips
        self.clips.extend(action_clips)

        assert walk_inplace is not None and alert_inplace is not None
        root = g.root
        transitions = [
            pose_transition(
                "PROC_IDLE_TO_WALK_V7", idle, walk_inplace,
                1.75, p.export_sample_hz, 0.0, 0.0, root,
                ("transition", "idle", "walk", "pelvis_continuity"),
            ),
            pose_transition(
                "PROC_WALK_TO_IDLE_V7", walk_inplace, idle,
                1.75, p.export_sample_hz, 0.50, 0.0, root,
                ("transition", "walk", "idle", "pelvis_continuity"),
            ),
            phase_matched_loop_transition(
                "PROC_WALK_TO_ALERT_WALK_V7", walk_inplace, alert_inplace,
                1.0 / p.cycle_hz, p.export_sample_hz, root,
                ("transition", "walk", "alert", "phase_matched", "pelvis_continuity"),
            ),
            phase_matched_loop_transition(
                "PROC_ALERT_WALK_TO_WALK_V7", alert_inplace, walk_inplace,
                1.0 / p.cycle_hz, p.export_sample_hz, root,
                ("transition", "alert", "walk", "phase_matched", "pelvis_continuity"),
            ),
            pose_transition(
                "PROC_IDLE_TO_ALERT_IDLE_V7", idle, alert_idle,
                1.30, p.export_sample_hz, 0.0, 0.0, root,
                ("transition", "idle", "alert_idle"),
            ),
            pose_transition(
                "PROC_ALERT_IDLE_TO_IDLE_V7", alert_idle, idle,
                1.30, p.export_sample_hz, 0.0, 0.0, root,
                ("transition", "alert_idle", "idle"),
            ),
            pose_transition(
                "PROC_IDLE_TO_EAT_V7", idle, eat,
                2.00, p.export_sample_hz, 0.0, 0.0, root,
                ("transition", "idle", "eat", "whole_body_lower"),
            ),
            pose_transition(
                "PROC_EAT_TO_IDLE_V7", eat, idle,
                2.00, p.export_sample_hz, 0.0, 0.0, root,
                ("transition", "eat", "idle", "whole_body_rise"),
            ),
            pose_transition(
                "PROC_IDLE_TO_ROAR_READY_V7", idle, roar,
                0.95, p.export_sample_hz, 0.0, 0.0, root,
                ("transition", "idle", "roar"),
            ),
            pose_transition(
                "PROC_ROAR_TO_IDLE_V7", roar, idle,
                1.50, p.export_sample_hz, 1.0, 0.0, root,
                ("transition", "roar", "idle", "recovery"),
            ),
            pose_transition(
                "PROC_WALK_TO_BITE_READY_V7", walk_inplace, bite_left,
                0.95, p.export_sample_hz, 0.50, 0.0, root,
                ("transition", "walk", "bite", "lead_left", "urgent"),
            ),
            pose_transition(
                "PROC_BITE_TO_WALK_V7", bite_left, walk_inplace,
                1.55, p.export_sample_hz, 1.0, 0.0, root,
                ("transition", "bite", "walk", "lead_left", "recovery"),
            ),
            pose_transition(
                "PROC_WALK_TO_BITE_READY_MIRRORED_V7", walk_inplace, bite_right,
                0.95, p.export_sample_hz, 0.0, 0.0, root,
                ("transition", "walk", "bite", "lead_right", "urgent"),
            ),
            pose_transition(
                "PROC_BITE_MIRRORED_TO_WALK_V7", bite_right, walk_inplace,
                1.55, p.export_sample_hz, 1.0, 0.50, root,
                ("transition", "bite", "walk", "lead_right", "recovery"),
            ),
            pose_transition(
                "PROC_WALK_TO_ROAR_READY_V7", walk_inplace, roar,
                1.35, p.export_sample_hz, 0.50, 0.0, root,
                ("transition", "walk", "roar"),
            ),
            pose_transition(
                "PROC_ROAR_TO_WALK_V7", roar, walk_inplace,
                1.90, p.export_sample_hz, 1.0, 0.0, root,
                ("transition", "roar", "walk", "recovery"),
            ),
            pose_transition(
                "PROC_WALK_TO_EAT_V7", walk_inplace, eat,
                2.05, p.export_sample_hz, 0.50, 0.0, root,
                ("transition", "walk", "eat", "settle"),
            ),
            pose_transition(
                "PROC_EAT_TO_WALK_V7", eat, walk_inplace,
                2.05, p.export_sample_hz, 0.0, 0.0, root,
                ("transition", "eat", "walk", "rise"),
            ),
        ]
        self.clips.extend(transitions)

        names = [clip.name for clip in self.clips]
        if len(names) != len(set(names)):
            duplicates = sorted({name for name in names if names.count(name) > 1})
            raise ValueError(f"Duplicate V7 clip names: {duplicates}")

        gate_summary = {clip.name: clip.diagnostics.get("quality_gates", {}) for clip in self.clips}
        critical = [
            gates for name, gates in gate_summary.items()
            if gates and (
                any(token in name for token in ("WALK", "TURN", "START", "BRAKE"))
                or any(token in name for token in ("IDLE_BREATH", "ALERT_IDLE", "EAT_LOOP", "BITE_ATTACK", "ROAR_V7"))
                or "_TO_" in name
            )
        ]
        automated_pass = bool(critical) and all(bool(value) for gates in critical for value in gates.values())
        self.report = {
            "status": "PASS_WITH_PERCEPTUAL_REVIEW_REQUIRED" if automated_pass else "FAIL_AUTOMATED_QUALITY_GATES",
            "automated_quality_pass": automated_pass,
            "version": "7.0.0",
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
            "quality_gate_summary": gate_summary,
            "implementation": {
                "v6_regression_removed": True,
                "pelvis_solved_before_leg_ik": True,
                "reference_fitted_relaxed_walk": True,
                "vertex_level_sole_collision": True,
                "terrain_height_and_normal_adaptation": True,
                "head_neck_led_turning": True,
                "asymmetric_turn_steps": True,
                "tail_turn_countershape": True,
                "acceleration_and_braking": True,
                "alert_locomotion": True,
                "whole_body_eating": True,
                "hindlimb_driven_bite_left_right": True,
                "roar": True,
                "pelvis_complete_transitions": True,
                "runtime_event_markers": True,
            },
        }
        return self.clips

    def animation_specs(self):
        if not self.clips:
            self.generate_all()
        return [clip.gltf_spec() for clip in self.clips]

    def _event_markers(self, clip: AnimationClip) -> list[dict[str, Any]]:
        name = clip.name
        duration = float(clip.duration)
        events: list[dict[str, Any]] = []
        diagnostics = clip.diagnostics or {}
        cycles = float(diagnostics.get("phase_advance_cycles", 0.0) or 0.0)
        if any(token in name for token in ("WALK_RELAXED", "WALK_UNEVEN", "WALK_UPSLOPE", "TURN_LEFT", "TURN_RIGHT", "ALERT_WALK")) and cycles > 0.0:
            for step in range(int(math.floor(cycles + 1e-9)) + 1):
                lt = duration * step / cycles
                if lt < duration - 1e-6 or not clip.extras.get("loop", False):
                    events.append({"timeSeconds": lt, "type": "foot_contact", "side": "left", "phase": float(step)})
                rp = step + 0.5
                if rp <= cycles + 1e-9:
                    rt = duration * rp / cycles
                    if rt < duration - 1e-6 or not clip.extras.get("loop", False):
                        events.append({"timeSeconds": rt, "type": "foot_contact", "side": "right", "phase": rp})
        if "TURN_LEFT" in name or "TURN_RIGHT" in name:
            events.extend([
                {"timeSeconds": duration * 0.08, "type": "turn_attention_lead"},
                {"timeSeconds": duration * 0.30, "type": "turn_mass_commit"},
                {"timeSeconds": duration * 0.82, "type": "turn_settle"},
            ])
        elif "START_WALK" in name:
            events.extend([{"timeSeconds": 0.0, "type": "locomotion_start"}, {"timeSeconds": duration * 0.62, "type": "locomotion_committed"}])
        elif "BRAKE_TO_IDLE" in name:
            events.extend([{"timeSeconds": 0.0, "type": "brake_start"}, {"timeSeconds": duration, "type": "idle_settled"}])
        elif "BITE_ATTACK" in name:
            events.extend([
                {"timeSeconds": duration * self.profile.bite_anticipation_fraction, "type": "attack_release"},
                {"timeSeconds": duration * self.profile.bite_contact_fraction, "type": "bite_contact", "windowSeconds": 0.10},
                {"timeSeconds": duration * self.profile.bite_recovery_fraction, "type": "recovery_start"},
            ])
        elif name == "PROC_ROAR_V7":
            events.extend([
                {"timeSeconds": duration * self.profile.roar_inhale_fraction, "type": "inhale_complete"},
                {"timeSeconds": duration * self.profile.roar_peak_fraction, "type": "roar_peak"},
                {"timeSeconds": duration * self.profile.roar_release_fraction, "type": "roar_release"},
            ])
        elif name == "PROC_EAT_LOOP_V7":
            for index in range(self.profile.eating_bite_count):
                events.append({"timeSeconds": duration * (index + 0.58) / self.profile.eating_bite_count, "type": "feeding_bite", "index": index})
        if clip.extras.get("transition"):
            events.append({"timeSeconds": duration, "type": "transition_commit"})
        return sorted(events, key=lambda item: (float(item["timeSeconds"]), str(item["type"])))

    def manifest(self, asset_name: str) -> dict[str, Any]:
        return {
            "schema": "eonwild.animation-manifest.v7",
            "version": "7.0.0",
            "asset": asset_name,
            "family": "heavy_predatory_biped",
            "speciesProfile": self.profile.name,
            "sampleHz": self.profile.export_sample_hz,
            "runtimeContracts": {
                "pelvisContactOrder": "root/path -> pelvis translation -> leg IK -> sole validation -> export exact pelvis track",
                "authoredTransitionHandoff": "switch exactly at transition endpoint; do not apply a second crossfade",
                "directClipSelection": "minimum-jerk snapshot blend with root continuity",
                "loopingRootMotion": "accumulate per-cycle root delta instead of jumping to the first sample",
                "turning": "head/neck/chest lead path heading; pelvis commits later; tail countershapes",
            },
            "clips": [
                {
                    "name": clip.name,
                    "durationSeconds": clip.duration,
                    "loop": bool(clip.extras.get("loop", False)),
                    "rootMotion": bool(clip.extras.get("rootMotion", False)),
                    "tags": clip.extras.get("tags", []),
                    "terrain": clip.extras.get("terrain"),
                    "path": clip.extras.get("path"),
                    "transition": bool(clip.extras.get("transition", False)),
                    "sourceClip": clip.extras.get("sourceClip"),
                    "targetClip": clip.extras.get("targetClip"),
                    "sourcePhase": clip.extras.get("sourcePhase"),
                    "targetPhase": clip.extras.get("targetPhase"),
                    "exactRuntimeHandoff": clip.extras.get("exactRuntimeHandoff", False),
                    "events": self._event_markers(clip),
                }
                for clip in self.clips
            ],
            "stateGraph": {
                "initial": "idle",
                "states": {
                    "idle": {"clip": "PROC_IDLE_BREATH_V7"},
                    "walk": {"clip": "PROC_WALK_RELAXED_V7_INPLACE", "speedMps": self.locomotion.speed},
                    "alert_idle": {"clip": "PROC_ALERT_IDLE_V7"},
                    "alert_walk": {"clip": "PROC_ALERT_WALK_V7_INPLACE"},
                    "eat": {"clip": "PROC_EAT_LOOP_V7"},
                },
                "oneShots": {
                    "bite_left": {"clip": "PROC_BITE_ATTACK_V7", "priority": 70},
                    "bite_right": {"clip": "PROC_BITE_ATTACK_MIRRORED_V7", "priority": 70},
                    "roar": {"clip": "PROC_ROAR_V7", "priority": 60},
                },
                "actionSequences": {
                    "bite_left": ["PROC_WALK_TO_BITE_READY_V7", "PROC_BITE_ATTACK_V7", "PROC_BITE_TO_WALK_V7", "PROC_WALK_RELAXED_V7_INPLACE"],
                    "bite_right": ["PROC_WALK_TO_BITE_READY_MIRRORED_V7", "PROC_BITE_ATTACK_MIRRORED_V7", "PROC_BITE_MIRRORED_TO_WALK_V7", "PROC_WALK_RELAXED_V7_INPLACE"],
                    "roar": ["PROC_WALK_TO_ROAR_READY_V7", "PROC_ROAR_V7", "PROC_ROAR_TO_WALK_V7", "PROC_WALK_RELAXED_V7_INPLACE"],
                    "eat": ["PROC_WALK_TO_EAT_V7", "PROC_EAT_LOOP_V7", "PROC_EAT_TO_WALK_V7", "PROC_WALK_RELAXED_V7_INPLACE"],
                    "alert": ["PROC_WALK_TO_ALERT_WALK_V7", "PROC_ALERT_WALK_V7_INPLACE"],
                },
            },
        }

    def write(self, output_dir: str | Path, source_path: str | Path, bone_map_path: str | Path):
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        if not self.clips:
            self.generate_all()
        glb_path = output / "tarbosaurus_procedural_v7_animation_pack.glb"
        self.asset.write_animations(glb_path, self.animation_specs(), replace_existing=True)
        manifest = self.manifest(glb_path.name)
        manifest_path = output / "animation-manifest.v7.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        profile_path = output / "resolved-profile-v7.json"
        self.profile.to_json(profile_path)
        report = {
            **self.report,
            "input": {
                "asset": str(Path(source_path).resolve()),
                "asset_sha256": sha256_file(source_path),
                "bone_map": str(Path(bone_map_path).resolve()),
                "bone_map_sha256": sha256_file(bone_map_path),
            },
            "output": {
                "animated_glb": str(glb_path.resolve()),
                "animated_glb_sha256": sha256_file(glb_path),
                "clip_count": len(self.clips),
            },
        }
        report_path = output / "procedural-v7-report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return {"glb": glb_path, "manifest": manifest_path, "profile": profile_path, "report": report_path}
