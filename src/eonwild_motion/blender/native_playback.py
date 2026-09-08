"""Task-owned exact source-time playback for imported glTF CUBICSPLINE TRS.

Blender 5.2's bundled glTF importer preserves channel values but discards the
serialized cubic tangents and creates AUTO Bezier handles.  Native review must
therefore sample the immutable glTF channels itself.  This module captures the
importer's per-node conversion state without modifying the installed add-on,
then applies exact sampled local TRS values before each requested render.

This is a render-time sampling adapter.  It does not create authoritative
Blender curves and cannot be used as evidence for FBX transport support.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
from typing import Any

from ..errors import ContractError
from ..glb.animation import TrsTrack, read_animation_tracks
from ..glb.container import Glb


def _source_animation(
    source: Path,
) -> tuple[Glb, dict[tuple[int, str], TrsTrack], tuple[float, ...]]:
    glb = Glb(source)
    animations = glb.document.get("animations")
    if not isinstance(animations, list) or len(animations) != 1:
        raise ContractError("native playback requires exactly one glTF animation")
    name = animations[0].get("name") if isinstance(animations[0], dict) else None
    if not isinstance(name, str) or not name:
        raise ContractError("native playback animation requires a nonempty name")
    tracks, timeline = read_animation_tracks(glb, name, require_common_timeline=True)
    return glb, tracks, tuple(float(value) for value in timeline)


def requires_exact_cubic_playback(source: Path) -> bool:
    """Return whether strict playback finds any serialized CUBICSPLINE TRS."""
    _, tracks, _ = _source_animation(Path(source))
    return any(track.interpolation == "CUBICSPLINE" for track in tracks.values())


def reject_stock_cubic_playback(source: Path, *, consumer: str) -> None:
    """Fail closed for a Blender consumer that has no exact sampling adapter."""
    if requires_exact_cubic_playback(source):
        raise ContractError(
            f"{consumer} cannot use Blender's approximate CUBICSPLINE import; "
            "use the task-owned exact native playback renderer"
        )


@dataclass
class ExactCubicPlayback:
    """Apply strict glTF samples through the importing Blender instance's map."""

    source: Path
    glb: Glb
    tracks: dict[tuple[int, str], TrsTrack]
    timeline: tuple[float, ...]
    importer: Any
    vnode_type: Any
    detached_action_owner_count: int = 0

    def _converted_value(self, node: int, path: str, raw: Any) -> tuple[Any, Any]:
        # These are the same local conversions used by BlenderNodeAnim for key
        # values.  Capturing the importer state is necessary because bone
        # prettification adds per-node before/after rotations.
        from mathutils import Vector

        vnode = self.importer.vnodes[node]
        if path == "translation":
            value = vnode.base_locs_to_final_locs(
                [self.importer.loc_gltf_to_blender(raw)]
            )[0]
        elif path == "rotation":
            value = vnode.base_rots_to_final_rots(
                [self.importer.quaternion_gltf_to_blender(raw)]
            )[0]
        elif path == "scale":
            value = vnode.base_scales_to_final_scales(
                [self.importer.scale_gltf_to_blender(raw)]
            )[0]
        else:  # The strict reader already rejects this; retain local fail-closedness.
            raise ContractError(f"native playback path is unsupported: {path!r}")

        if (
            vnode.type == self.vnode_type.Object
            and path == "translation"
            and vnode.parent is not None
            and self.importer.vnodes[vnode.parent].type == self.vnode_type.Bone
        ):
            value = value + Vector(
                (0.0, -self.importer.vnodes[vnode.parent].bone_length, 0.0)
            )

        if vnode.type == self.vnode_type.Bone:
            armature = self.importer.vnodes[vnode.bone_arma].blender_object
            if armature is None or vnode.blender_bone_name not in armature.pose.bones:
                raise ContractError("native playback cannot resolve an imported pose bone")
            target = armature.pose.bones[vnode.blender_bone_name]
            if path == "translation":
                value = vnode.editbone_rot.conjugated() @ (
                    value - vnode.editbone_trans
                )
            elif path == "rotation":
                value = vnode.editbone_rot.conjugated() @ value
        elif vnode.type == self.vnode_type.Object:
            target = vnode.blender_object
            if target is None:
                raise ContractError("native playback cannot resolve an imported object")
        else:
            raise ContractError("native playback animation targets an unsupported virtual node")
        return target, value

    def apply(self, time_s: float) -> None:
        """Apply one exact source-second sample after Blender sets its frame."""
        if isinstance(time_s, bool) or not isinstance(time_s, (int, float)):
            raise ContractError("native playback time must be a finite number")
        time = float(time_s)
        if not math.isfinite(time):
            raise ContractError("native playback time must be a finite number")
        # glTF timestamps are FLOAT accessors while runtime duration metadata
        # is JSON double precision.  Match the existing transport endpoint
        # tolerance without admitting a neighboring animation interval.
        tolerance = max(
            2.0e-6, 64.0 * math.ulp(max(1.0, abs(self.timeline[-1])))
        )
        if time < self.timeline[0] - tolerance or time > self.timeline[-1] + tolerance:
            raise ContractError("native playback time is outside the serialized timeline")
        time = min(max(time, self.timeline[0]), self.timeline[-1])

        for (node, path), track in self.tracks.items():
            target, value = self._converted_value(node, path, track.sample(time))
            if path == "translation":
                target.location = value
            elif path == "rotation":
                target.rotation_mode = "QUATERNION"
                target.rotation_quaternion = value
            else:
                target.scale = value

        import bpy

        bpy.context.view_layer.update()

    def receipt(self) -> dict[str, Any]:
        return {
            "mode": "TASK_OWNED_EXACT_SOURCE_TIME_SAMPLING",
            "scope": "native Blender render evaluation only; not native curve or FBX support",
            "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "adapter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "timeline_start_s": self.timeline[0],
            "timeline_end_s": self.timeline[-1],
            "track_count": len(self.tracks),
            "cubic_track_count": sum(
                track.interpolation == "CUBICSPLINE" for track in self.tracks.values()
            ),
            "detached_action_owner_count": self.detached_action_owner_count,
        }


def _detach_approximate_imported_actions(
    importer: Any,
    vnode_type: Any,
    tracks: dict[tuple[int, str], TrsTrack],
) -> int:
    """Detach stock-imported actions from every exact playback target owner.

    Blender's render dependency graph reevaluates active AUTO curves even after
    direct pose assignment.  The action datablocks remain in ``bpy.data`` for
    source-clock inspection; only their bindings to CUBICSPLINE target owners
    are removed.  This adapter does not claim to create native cubic curves.
    """
    owners: dict[int, Any] = {}
    for node, _ in tracks:
        vnode = importer.vnodes[node]
        if vnode.type == vnode_type.Bone:
            owner = importer.vnodes[vnode.bone_arma].blender_object
        elif vnode.type == vnode_type.Object:
            owner = vnode.blender_object
        else:
            raise ContractError(
                "native playback animation targets an unsupported virtual node"
            )
        if owner is None:
            raise ContractError("native playback cannot resolve an animation owner")
        owners[id(owner)] = owner

    detached = 0
    for owner in owners.values():
        animation_data = owner.animation_data
        if animation_data is None:
            continue
        if animation_data.action is not None:
            animation_data.action = None
            detached += 1
        active_strips = [
            strip
            for track in animation_data.nla_tracks
            if not track.mute
            for strip in track.strips
            if not strip.mute and strip.action is not None
        ]
        if animation_data.action is not None or active_strips:
            raise ContractError(
                "native playback could not detach approximate imported animation"
            )
    if detached == 0:
        raise ContractError(
            "native playback found no imported action to detach from cubic targets"
        )
    return detached


def import_gltf_for_native_playback(source: Path) -> ExactCubicPlayback | None:
    """Import one GLB and return an exact adapter only when cubic TRS exists."""
    source = Path(source).resolve()
    glb, tracks, timeline = _source_animation(source)
    if not any(track.interpolation == "CUBICSPLINE" for track in tracks.values()):
        import bpy

        bpy.ops.import_scene.gltf(filepath=str(source))
        return None

    import bpy
    from io_scene_gltf2.blender.imp.animation_node import BlenderNodeAnim
    from io_scene_gltf2.blender.imp.vnode import VNode

    captured: dict[str, Any] = {}
    original = BlenderNodeAnim.do_channel

    def capture(importer: Any, animation_index: int, node_index: int, channel: Any) -> Any:
        prior = captured.get("importer")
        if prior is not None and prior is not importer:
            raise ContractError(
                "native playback import unexpectedly used multiple importer states"
            )
        captured["importer"] = importer
        return original(importer, animation_index, node_index, channel)

    BlenderNodeAnim.do_channel = staticmethod(capture)
    try:
        bpy.ops.import_scene.gltf(filepath=str(source))
    finally:
        BlenderNodeAnim.do_channel = staticmethod(original)
    importer = captured.get("importer")
    if importer is None:
        raise ContractError("native playback could not capture Blender's import mapping")
    for node, _ in tracks:
        if node not in importer.vnodes:
            raise ContractError("native playback import mapping omits an animated node")
    detached = _detach_approximate_imported_actions(importer, VNode, tracks)
    return ExactCubicPlayback(source, glb, tracks, timeline, importer, VNode, detached)
