from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from eonwild_motion.contact_gauge import (
    _animation_channels,
    _Channel,
    _finite_difference,
    _normalize_skin_weights,
    _source_frames,
    _uniform_times,
    analyze_frame_sequence,
    analyze_glb,
    load_contact_gauge_source,
    load_narrow_gauge_policy,
)
from eonwild_motion.errors import ContractError
from eonwild_motion.glb.container import Glb as ContainerGlb
from eonwild_motion.hashing import sha256_file


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "reports/V9-GAIT-FOOT-AUDIT-001/narrow-gauge-contract.json"
SOURCE_PROFILE_PATH = ROOT / "profiles/v9/contact-gauge-v8.2.json"
SOURCE_PATH = ROOT / "legacy/capsules/v8.2/asset/tarbosaurus_v8_2_approved.glb"
POLICY = load_narrow_gauge_policy(POLICY_PATH)
SOURCE = load_contact_gauge_source(SOURCE_PROFILE_PATH)


def _rotate_y(point: list[float], angle: float) -> list[float]:
    cosine = math.cos(angle)
    sine = math.sin(angle)
    x, y, z = point
    return [cosine * x + sine * z, y, -sine * x + cosine * z]


def _synthetic_frames(angle: float = 0.0) -> list[dict]:
    frames = []
    for index in range(8):
        root = [0.0, 0.0, index * 0.08]
        hip_left = [-0.36, 1.25, root[2]]
        hip_right = [0.36, 1.25, root[2]]
        left_axis = [-0.58, 0.18, root[2] + 0.08]
        right_axis = [0.58, 0.18, root[2] + 0.08]
        left_sole = [[-0.58, 0.01, root[2] + 0.05], [-0.52, 0.01, root[2] + 0.05]]
        right_sole = [[0.58, 0.01, root[2] + 0.05], [0.52, 0.01, root[2] + 0.05]]
        left_toe = [[-0.58, 0.0, root[2] + 0.32], [-0.52, 0.0, root[2] + 0.32]]
        right_toe = [[0.58, 0.0, root[2] + 0.32], [0.52, 0.0, root[2] + 0.32]]
        frame = {
            "time_s": index * 0.1,
            "root_m": _rotate_y(root, angle),
            "hip_left_m": _rotate_y(hip_left, angle),
            "hip_right_m": _rotate_y(hip_right, angle),
            "feet": {
                "left": {
                    "axis_origin_m": _rotate_y(left_axis, angle),
                    "sole_points": [{"point_m": _rotate_y(point, angle), "weight": 1.0} for point in left_sole],
                    "toe_points": [{"point_m": _rotate_y(point, angle), "weight": 1.0} for point in left_toe],
                },
                "right": {
                    "axis_origin_m": _rotate_y(right_axis, angle),
                    "sole_points": [{"point_m": _rotate_y(point, angle), "weight": 1.0} for point in right_sole],
                    "toe_points": [{"point_m": _rotate_y(point, angle), "weight": 1.0} for point in right_toe],
                },
            },
        }
        frames.append(frame)
    return frames


def _variable_height_frames() -> list[dict]:
    supports = (0.44, 0.44, 0.90)
    heights = (0.60, 1.00, 1.00)
    frames = []
    for index, (support, height) in enumerate(zip(supports, heights)):
        root_z = index * 0.05
        left_x = -support / 2.0
        right_x = support / 2.0
        def foot(x: float) -> dict:
            return {
                "axis_origin_m": [x, 0.10, root_z + 0.05],
                "sole_points": [
                    {"point_m": [x - 0.02, 0.0, root_z], "weight": 1.0},
                    {"point_m": [x + 0.02, 0.0, root_z], "weight": 1.0},
                ],
                "toe_points": [
                    {"point_m": [x - 0.02, 0.0, root_z + 0.10], "weight": 1.0},
                    {"point_m": [x + 0.02, 0.0, root_z + 0.10], "weight": 1.0},
                ],
            }
        frames.append(
            {
                "time_s": index * 0.1,
                "root_m": [0.0, 0.0, root_z],
                "hip_left_m": [-0.5, height, root_z],
                "hip_right_m": [0.5, height, root_z],
                "feet": {"left": foot(left_x), "right": foot(right_x)},
            }
        )
    return frames


def _swap_foot_x_positions(frames: list[dict]) -> list[dict]:
    crossed = copy.deepcopy(frames)
    for frame in crossed:
        for foot in frame["feet"].values():
            foot["axis_origin_m"][0] *= -1.0
            for group in ("sole_points", "toe_points"):
                for point in foot[group]:
                    point["point_m"][0] *= -1.0
    return crossed


class ContactGaugeTests(unittest.TestCase):
    def _assert_profile_variant_rejected(self, mutate, message):
        profile = copy.deepcopy(SOURCE)
        mutate(profile)
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            profile_path = Path(temporary) / "mutated-source-profile.json"
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, message):
                analyze_glb(
                    SOURCE_PATH,
                    profile_path,
                    POLICY_PATH,
                    repository=ROOT,
                )

    def test_policy_and_source_are_strict_and_explicit(self):
        self.assertEqual(POLICY["status"], "PROVISIONAL_ENGINEERING_CONTRACT")
        self.assertFalse(POLICY["scientificClaim"])
        self.assertFalse(POLICY["speciesHardcode"])
        self.assertEqual(SOURCE["coordinate_system"]["up_axis"], "Y")
        self.assertEqual(SOURCE["geometry"]["feet"]["left"]["weight_threshold"], 0.75)

        unknown_policy = copy.deepcopy(POLICY)
        unknown_policy["unexpected"] = True
        with tempfile.TemporaryDirectory() as temporary:
            policy_path = Path(temporary) / "unknown-policy.json"
            policy_path.write_text(json.dumps(unknown_policy), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "unknown fields"):
                load_narrow_gauge_policy(policy_path)

    def test_synthetic_measurement_is_generic_and_finite(self):
        result = analyze_frame_sequence(
            _synthetic_frames(),
            policy=POLICY,
            thresholds=SOURCE["thresholds"],
            source_id="fictional-body-frame-fixture",
            gait_state="straight_walk",
        )
        measured = result.report["measured"]
        self.assertEqual(result.report["schema"], "eonwild.motion.v9.contact-gauge-report.v1")
        self.assertEqual(result.report["sampling"]["count"], 8)
        self.assertAlmostEqual(measured["travel_tangent"][2], 1.0, places=10)
        self.assertAlmostEqual(measured["hip_width_m"]["median"], 0.72, places=10)
        self.assertGreater(measured["support_width_over_hip_width"]["median"], 0.0)
        self.assertFalse(measured["crossover"]["observed"])
        self.assertTrue(measured["feet"]["left"]["contact_windows"])
        self.assertEqual(measured["feet"]["left"]["toe_off_windows"], [])
        self.assertEqual(result.report["engineering_envelopes"]["scientific_claim"], False)

    def test_profile_position_accessor_out_of_range_fails_closed(self):
        self._assert_profile_variant_rejected(
            lambda profile: profile["geometry"].update({"position_accessor": 10**9}),
            r"source geometry position accessor index .* out of range",
        )

    def test_profile_joint_accessor_out_of_range_fails_closed(self):
        self._assert_profile_variant_rejected(
            lambda profile: profile["geometry"]["joint_accessors"].__setitem__(0, 10**9),
            r"source geometry joint\[0\] accessor index .* out of range",
        )

    def test_profile_weight_accessor_out_of_range_fails_closed(self):
        self._assert_profile_variant_rejected(
            lambda profile: profile["geometry"]["weight_accessors"].__setitem__(0, 10**9),
            r"source geometry weight\[0\] accessor index .* out of range",
        )

    def test_policy_requires_step_width_metric(self):
        policy = copy.deepcopy(POLICY)
        policy["metrics"].pop("stepWidthNormalized")
        with self.assertRaisesRegex(ContractError, "stepWidthNormalized"):
            analyze_frame_sequence(
                _synthetic_frames(),
                policy=policy,
                thresholds=SOURCE["thresholds"],
            )

    def test_malformed_glb_accessor_table_fails_closed(self):
        malformed = ContainerGlb(SOURCE_PATH)
        malformed.document["accessors"] = {}
        with patch("eonwild_motion.contact_gauge.Glb", return_value=malformed):
            with self.assertRaisesRegex(ContractError, "GLB accessors table must be an array"):
                analyze_glb(
                    SOURCE_PATH,
                    SOURCE_PROFILE_PATH,
                    POLICY_PATH,
                    repository=ROOT,
                )

    def test_external_glb_path_is_rejected_at_admission(self):
        with self.assertRaisesRegex(ContractError, "source artifact path must be inside the repository"):
            analyze_glb(
                Path("/tmp/v9-contact-gauge-external.glb"),
                SOURCE_PROFILE_PATH,
                POLICY_PATH,
                repository=ROOT,
            )

    def test_external_source_profile_path_is_rejected_at_admission(self):
        with self.assertRaisesRegex(ContractError, "source profile path must be inside the repository"):
            analyze_glb(
                SOURCE_PATH,
                Path("/tmp/v9-contact-gauge-external-profile.json"),
                POLICY_PATH,
                repository=ROOT,
            )

    def test_external_policy_path_is_rejected_at_admission(self):
        with self.assertRaisesRegex(ContractError, "narrow-gauge policy path must be inside the repository"):
            analyze_glb(
                SOURCE_PATH,
                SOURCE_PROFILE_PATH,
                Path("/tmp/v9-contact-gauge-external-policy.json"),
                repository=ROOT,
            )

    def test_measured_tangent_is_rotation_invariant(self):
        base = analyze_frame_sequence(
            _synthetic_frames(),
            policy=POLICY,
            thresholds=SOURCE["thresholds"],
            source_id="rotation-base",
        )
        rotated = analyze_frame_sequence(
            _synthetic_frames(math.pi / 2.0),
            policy=POLICY,
            thresholds=SOURCE["thresholds"],
            source_id="rotation-yaw",
        )
        self.assertAlmostEqual(rotated.report["measured"]["travel_tangent"][0], 1.0, places=10)
        self.assertAlmostEqual(rotated.report["measured"]["travel_tangent"][2], 0.0, places=10)
        self.assertAlmostEqual(
            base.report["measured"]["support_width_over_hip_width"]["median"],
            rotated.report["measured"]["support_width_over_hip_width"]["median"],
            places=10,
        )
        self.assertAlmostEqual(
            base.report["measured"]["feet"]["left"]["foot_heading_degrees"]["median"],
            rotated.report["measured"]["feet"]["left"]["foot_heading_degrees"]["median"],
            places=10,
        )

    def test_irregular_timestamps_use_total_displacement_over_elapsed_time(self):
        frames = _synthetic_frames()
        times = (0.0, 0.1, 1.0, 1.1, 2.0, 2.1, 3.0, 3.1)
        roots = (0.0, 0.05, 0.06, 0.16, 0.17, 0.27, 0.28, 0.38)
        for frame, time_s, root_z in zip(frames, times, roots):
            frame["time_s"] = time_s
            frame["root_m"] = [0.0, 0.0, root_z]
        result = analyze_frame_sequence(
            frames,
            policy=POLICY,
            thresholds=SOURCE["thresholds"],
        )
        self.assertAlmostEqual(
            result.report["measured"]["travel_speed_mps"],
            0.38 / 3.1,
            places=12,
        )

    def test_contact_velocity_uses_forward_difference_at_first_frame(self):
        normal = analyze_frame_sequence(
            _synthetic_frames(),
            policy=POLICY,
            thresholds=SOURCE["thresholds"],
        )
        normal_first = normal.report["frame_facts"][0]["feet"]["left"]
        self.assertGreater(normal_first["relative_contact_velocity_mps"], 0.0)

        jumped = _synthetic_frames()
        for point in jumped[0]["feet"]["left"]["toe_points"]:
            point["point_m"][2] += 5.0
        result = analyze_frame_sequence(
            jumped,
            policy=POLICY,
            thresholds=SOURCE["thresholds"],
        )
        first = result.report["frame_facts"][0]["feet"]["left"]
        self.assertGreater(first["relative_contact_velocity_mps"], 40.0)
        self.assertFalse(first["contact"])

    def test_anatomical_hip_lateral_sign_survives_initially_crossed_feet(self):
        result = analyze_frame_sequence(
            _swap_foot_x_positions(_synthetic_frames()),
            policy=POLICY,
            thresholds=SOURCE["thresholds"],
        )
        measured = result.report["measured"]
        self.assertLess(measured["lateral_axis"][0], -0.99)
        self.assertTrue(measured["crossover"]["observed"])

    def test_width_ratios_use_canonical_median_hip_height(self):
        result = analyze_frame_sequence(
            _variable_height_frames(),
            policy=POLICY,
            thresholds=SOURCE["thresholds"],
        )
        measured = result.report["measured"]
        self.assertAlmostEqual(measured["hip_height_m"]["median"], 1.0, places=12)
        self.assertAlmostEqual(
            measured["support_width_over_hip_height"]["median"],
            0.44,
            places=12,
        )
        self.assertAlmostEqual(
            measured["feet"]["left"]["track_to_midline_over_hip_height"]["median"],
            0.22,
            places=12,
        )

    def test_simultaneous_touchdowns_are_not_step_pairs(self):
        result = analyze_frame_sequence(
            _synthetic_frames(),
            policy=POLICY,
            thresholds=SOURCE["thresholds"],
        )
        step_width = result.report["measured"]["step_width_normalized"]
        self.assertEqual(step_width["status"], "UNEVALUATED")
        self.assertEqual(step_width["event_pair_count"], 0)
        self.assertIsNone(step_width["values"])
        self.assertIsNone(result.report["measured"]["step_width_m"])

    def test_turn_is_explicitly_unevaluated(self):
        result = analyze_frame_sequence(
            _synthetic_frames(),
            policy=POLICY,
            thresholds=SOURCE["thresholds"],
            gait_state="turn",
        )
        self.assertEqual(result.report["status"], "UNEVALUATED_UNSUPPORTED")
        self.assertIsNone(result.report["measured"])

    def test_nonzero_animation_timeline_bounds_are_preserved(self):
        self.assertEqual(_uniform_times(2.0, 5.0, 4, label="probe"), (2.0, 3.0, 4.0, 5.0))

    def test_source_frames_honor_nonzero_glb_timeline_bounds(self):
        animation_name = SOURCE["source"]["clips"]["root_motion"]
        glb = ContainerGlb(SOURCE_PATH)
        animation = glb.animation(animation_name)
        input_indices = {
            animation["samplers"][channel["sampler"]]["input"]
            for channel in animation["channels"]
        }
        self.assertEqual(len(input_indices), 1)
        timeline_accessor = next(iter(input_indices))
        offset, count, stride = glb.accessor_region(timeline_accessor)
        self.assertEqual(stride, 4)
        shift_s = 2.5
        raw = bytearray(glb.raw)
        for row in range(count):
            byte_offset = glb.bin_start + offset + row * stride
            value = struct.unpack_from("<f", raw, byte_offset)[0]
            struct.pack_into("<f", raw, byte_offset, value + shift_s)

        shifted_glb = ContainerGlb.from_bytes(bytes(raw))
        frames, extraction = _source_frames(
            shifted_glb,
            SOURCE,
            animation_name=animation_name,
        )
        expected_end = 4.069565296173096 + shift_s
        self.assertAlmostEqual(frames[0]["time_s"], shift_s, places=6)
        self.assertAlmostEqual(frames[-1]["time_s"], expected_end, places=6)
        self.assertAlmostEqual(extraction["timeline_start_s"], shift_s, places=6)
        self.assertAlmostEqual(extraction["timeline_end_s"], expected_end, places=6)
        self.assertAlmostEqual(extraction["duration_s"], 4.069565296173096, places=6)

    def test_combined_skin_weights_are_validated_and_normalized(self):
        normalized = _normalize_skin_weights(
            [[[0, 1]]],
            [[[1.0, 3.0]]],
            vertex_count=1,
            joint_count=2,
        )
        self.assertAlmostEqual(normalized[0][0][1], 0.25, places=12)
        self.assertAlmostEqual(normalized[0][1][1], 0.75, places=12)
        with self.assertRaisesRegex(ContractError, "must be >= 0"):
            _normalize_skin_weights([[[0, 1]]], [[[1.0, -1.0]]], vertex_count=1, joint_count=2)
        with self.assertRaisesRegex(ContractError, "must be a finite number"):
            _normalize_skin_weights([[[0, 1]]], [[[1.0, math.inf]]], vertex_count=1, joint_count=2)
        with self.assertRaisesRegex(ContractError, "positive combined skin weight"):
            _normalize_skin_weights([[[0, 1]]], [[[0.0, 0.0]]], vertex_count=1, joint_count=2)

    def test_zero_travel_fails_closed(self):
        frames = _synthetic_frames()
        for frame in frames:
            frame["root_m"] = [0.0, 0.0, 0.0]
        with self.assertRaisesRegex(ContractError, "measured travel is zero"):
            analyze_frame_sequence(
                frames,
                policy=POLICY,
                thresholds=SOURCE["thresholds"],
                source_id="zero-travel",
            )

    def test_immutable_source_root_motion_is_measured(self):
        result = analyze_glb(
            SOURCE_PATH,
            SOURCE_PROFILE_PATH,
            POLICY_PATH,
            repository=ROOT,
        )
        self.assertEqual(result.report["sampling"]["count"], 120)
        self.assertEqual(result.report["sampling"]["source_timeline_count"], 245)
        self.assertEqual(result.report["sampling"]["mask_counts"]["left"]["toe"], 1395)
        self.assertEqual(result.report["sampling"]["mask_counts"]["right"]["toe"], 1386)
        self.assertEqual(
            result.report["sampling"]["skin_weight_validation"],
            "finite_nonnegative_positive_sum_normalized",
        )
        self.assertGreater(result.report["measured"]["travel_speed_mps"], 1.0)
        self.assertFalse(result.report["measured"]["crossover"]["observed"])
        self.assertGreater(
            result.report["measured"]["feet"]["right"]["floor"]["toe_penetration_m"]["max"],
            0.005,
        )

    def test_immutable_in_place_clip_rejects_zero_travel(self):
        with self.assertRaisesRegex(ContractError, "measured travel is zero"):
            analyze_glb(
                SOURCE_PATH,
                SOURCE_PROFILE_PATH,
                POLICY_PATH,
                repository=ROOT,
                clip_name=SOURCE["source"]["clips"]["in_place"],
            )

    def test_v8_release_witness_hashes_remain_unchanged(self):
        self.assertEqual(
            sha256_file(SOURCE_PATH),
            "a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5",
        )
        candidate = ROOT / "assets/sha256/b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03.glb"
        self.assertEqual(
            sha256_file(candidate),
            "b5fc582e3bae3b2708735e7ae68cc31da65599f6d155d3b6d089a44ed5517d03",
        )


if __name__ == "__main__":
    unittest.main()
