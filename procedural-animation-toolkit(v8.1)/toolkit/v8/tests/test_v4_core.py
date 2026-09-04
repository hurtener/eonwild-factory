from __future__ import annotations
import json
import math
import sys
import unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from eonproc_v3.curves import minimum_jerk
from eonproc_v3.gltf_io import GlbAsset
from eonproc_v3.rig import SemanticMap, AnatomicalBasis
from eonproc_v4.path import StraightPath, ArcPath
from eonproc_v4.profile import BipedV4Profile
from eonproc_v4.sole import SoleContactModel
from eonproc_v4.terrain import FlatTerrain, PlaneTerrain, ProceduralTerrain


class CurvesTest(unittest.TestCase):
    def test_minimum_jerk_endpoints_and_monotonicity(self):
        xs = np.linspace(0, 1, 101)
        ys = np.asarray([minimum_jerk(float(x)) for x in xs])
        self.assertEqual(ys[0], 0.0)
        self.assertEqual(ys[-1], 1.0)
        self.assertTrue(np.all(np.diff(ys) >= -1e-12))
        self.assertLess(abs((ys[1] - ys[0]) / (xs[1] - xs[0])), 0.01)
        self.assertLess(abs((ys[-1] - ys[-2]) / (xs[-1] - xs[-2])), 0.01)


class TerrainAndPathTest(unittest.TestCase):
    def test_terrain_normals_are_unit_and_upward(self):
        surfaces = [
            FlatTerrain(0.0),
            PlaneTerrain.from_slopes(0.08, -0.04),
            ProceduralTerrain(0.08, 1.7, 0.03, 0.8),
        ]
        for surface in surfaces:
            for x in np.linspace(-2, 2, 5):
                for z in np.linspace(-2, 2, 5):
                    _, normal = surface.height_normal(np.array([x, 0.0, z]))
                    self.assertAlmostEqual(float(np.linalg.norm(normal)), 1.0, places=7)
                    self.assertGreater(normal[1], 0.0)

    def test_arc_frame_preserves_orthonormal_basis(self):
        basis = AnatomicalBasis(
            lateral=np.array([1.0, 0.0, 0.0]),
            up=np.array([0.0, 1.0, 0.0]),
            forward=np.array([0.0, 0.0, -1.0]),
        )
        path = ArcPath(np.zeros(3), basis, radius=4.0, sign=1.0)
        frame = path.frame(2.0)
        m = np.column_stack([frame.basis.lateral, frame.basis.up, frame.basis.forward])
        self.assertTrue(np.allclose(m.T @ m, np.eye(3), atol=1e-10))
        self.assertGreater(np.linalg.norm(frame.position), 0.0)


class FixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        candidates = [
            ROOT.parents[2] / "inputs" / "tarbosaurus_source.glb",
            Path("/mnt/data/tarbosaurus(1).glb"),
        ]
        cls.asset_path = next((p for p in candidates if p.exists()), None)
        map_candidates = [
            ROOT.parents[2] / "inputs" / "tarbosaurus_bone_map.edited.yml",
            Path("/mnt/data/bone-map.edited-2.yml"),
        ]
        cls.map_path = next((p for p in map_candidates if p.exists()), None)

    def test_profile_contract(self):
        p = BipedV4Profile()
        self.assertEqual(p.export_sample_hz, 60)
        self.assertGreater(p.stance_fraction, 0.5)
        self.assertGreater(p.cycle_hz, 0.0)
        self.assertLess(p.knee_min_flex_deg, p.knee_max_flex_deg)
        self.assertLess(p.ankle_min_flex_deg, p.ankle_max_flex_deg)

    def test_real_rig_and_sole_patches(self):
        if self.asset_path is None or self.map_path is None:
            self.skipTest("Tarbosaurus fixture not present")
        asset = GlbAsset(self.asset_path)
        semantics = SemanticMap.load(self.map_path)
        mapped, missing = semantics.existing_bones(asset)
        self.assertEqual(missing, [])
        self.assertEqual(len(asset.skin_data()[0]), 75)
        basis = AnatomicalBasis.gltf_y_up(asset, semantics)
        hip = asset.rest_world[asset.name_to_node[semantics.bone("pelvis")]][1, 3] - np.min(asset.primitive().positions[:, 1])
        p = BipedV4Profile()
        sole = SoleContactModel(
            asset, semantics, basis, hip,
            p.sole_weight_threshold,
            hip * p.sole_height_band_hip_fraction,
            p.sole_min_vertices_per_side,
            p.sole_max_vertices_per_side,
            p.sole_contact_quantile,
            p.sole_clearance_m,
            hip * p.sole_max_vertical_correction_hip_fraction,
        )
        for side in ("l", "r"):
            self.assertGreaterEqual(len(sole.selections[side].vertex_indices), p.sole_min_vertices_per_side)
            self.assertLessEqual(len(sole.selections[side].vertex_indices), p.sole_max_vertices_per_side)


if __name__ == "__main__":
    unittest.main(verbosity=2)
