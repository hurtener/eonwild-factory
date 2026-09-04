"""Eonwild procedural animation toolkit v4."""
from .profile import BipedV4Profile
from .terrain import TerrainSurface, FlatTerrain, PlaneTerrain, ProceduralTerrain
from .path import MotionPath, StraightPath, ArcPath
from .clip import AnimationClip
from .generator import TarbosaurusV4Generator

__all__ = [
    "BipedV4Profile", "TerrainSurface", "FlatTerrain", "PlaneTerrain",
    "ProceduralTerrain", "MotionPath", "StraightPath", "ArcPath",
    "AnimationClip", "TarbosaurusV4Generator",
]
