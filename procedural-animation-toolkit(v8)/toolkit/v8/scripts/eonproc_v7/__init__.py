"""Eonwild procedural animation V7: contact-locked locomotion and mass-led turns."""
from .profile import BipedV7Profile
from .locomotion import TarbosaurusV7LocomotionGenerator
from .actions import TarbosaurusV7ActionGenerator
from .generator import TarbosaurusV7Generator

__all__ = [
    "BipedV7Profile",
    "TarbosaurusV7LocomotionGenerator",
    "TarbosaurusV7ActionGenerator",
    "TarbosaurusV7Generator",
]
