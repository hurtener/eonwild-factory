"""Typed, source-bound neutral jaw calibration data.

The calibration is authored kinematic behavior.  Its surface witnesses prove a
positive sampled gap; they are not tooth correspondences or biological data.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re
from typing import Any, Mapping

from ..errors import ContractError


@dataclass(frozen=True)
class JawSurfaceBin:
    lower_vertex_indices: tuple[int, ...]
    upper_vertex_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        for values, label in (
            (self.lower_vertex_indices, "lower"),
            (self.upper_vertex_indices, "upper"),
        ):
            if (not isinstance(values, tuple) or len(values) < 3
                    or any(type(value) is not int or value < 0 for value in values)
                    or len(values) != len(set(values))):
                raise ContractError(
                    f"neutral jaw {label} surface indices must be unique nonnegative integers")


@dataclass(frozen=True)
class NeutralJawCalibration:
    source_geometry_sha256: str
    close_degrees: float
    clearance_body_heights: float
    measured_body_height_m: float
    measured_minimum_gap_m: float
    method: str
    axis_frame: str
    skin_index: int
    position_accessor: int
    joint_accessors: tuple[int, ...]
    weight_accessors: tuple[int, ...]
    surface_bins: tuple[JawSurfaceBin, ...]

    def __post_init__(self) -> None:
        if (not isinstance(self.source_geometry_sha256, str)
                or not re.fullmatch(r"[0-9a-f]{64}", self.source_geometry_sha256)):
            raise ContractError("neutral jaw calibration requires a lowercase source SHA256")
        for value, label in (
            (self.close_degrees, "closure"),
            (self.clearance_body_heights, "clearance"),
            (self.measured_body_height_m, "measured body height"),
            (self.measured_minimum_gap_m, "measured minimum gap"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ContractError(f"neutral jaw {label} must be finite numeric")
        if not 0 <= self.close_degrees <= 70:
            raise ContractError("neutral jaw closure exceeds the authored envelope")
        if not 0 < self.clearance_body_heights <= .02:
            raise ContractError("neutral jaw clearance exceeds the authored envelope")
        if self.measured_body_height_m <= 0 or self.measured_minimum_gap_m <= 0:
            raise ContractError("neutral jaw measured gap evidence must be positive")
        expected_gap = self.clearance_body_heights * self.measured_body_height_m
        if abs(self.measured_minimum_gap_m - expected_gap) > 1e-9:
            raise ContractError("neutral jaw measured gap does not match its normalized evidence")
        if self.method != "semantic_weighted_binned_surface_clearance.v1":
            raise ContractError("unsupported neutral jaw calibration method")
        if self.axis_frame != "admitted_jaw_local_from_declared_lateral.v1":
            raise ContractError("unsupported neutral jaw axis frame")
        for value, label in (
            (self.skin_index, "skin"),
            (self.position_accessor, "position accessor"),
        ):
            if type(value) is not int or value < 0:
                raise ContractError(f"neutral jaw {label} index must be a nonnegative integer")
        for values, label in (
            (self.joint_accessors, "joint accessors"),
            (self.weight_accessors, "weight accessors"),
        ):
            if (not isinstance(values, tuple) or not 1 <= len(values) <= 4
                    or any(type(value) is not int or value < 0 for value in values)
                    or len(values) != len(set(values))):
                raise ContractError(
                    f"neutral jaw {label} must be unique nonnegative integer indices")
        if len(self.joint_accessors) != len(self.weight_accessors):
            raise ContractError("neutral jaw joint and weight accessor counts differ")
        if not isinstance(self.surface_bins, tuple) or not 3 <= len(self.surface_bins) <= 12:
            raise ContractError("neutral jaw calibration requires 3..12 surface bins")
        if any(not isinstance(value, JawSurfaceBin) for value in self.surface_bins):
            raise ContractError("neutral jaw surface bins must be typed")
        lower = [index for value in self.surface_bins for index in value.lower_vertex_indices]
        upper = [index for value in self.surface_bins for index in value.upper_vertex_indices]
        if len(lower) != len(set(lower)) or len(upper) != len(set(upper)) or set(lower) & set(upper):
            raise ContractError("neutral jaw surface witness identities must be unique and disjoint")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_neutral_jaw_calibration(value: Any) -> NeutralJawCalibration:
    if not isinstance(value, Mapping):
        raise ContractError("neutral jaw calibration must be a mapping")
    required = set(NeutralJawCalibration.__dataclass_fields__)
    if set(value) != required:
        raise ContractError("neutral jaw calibration fields are incomplete or unknown")
    bins = value["surface_bins"]
    if not isinstance(bins, (list, tuple)):
        raise ContractError("neutral jaw surface bins must be a sequence")
    typed_bins = []
    for item in bins:
        if not isinstance(item, Mapping) or set(item) != set(JawSurfaceBin.__dataclass_fields__):
            raise ContractError("neutral jaw surface bin fields are incomplete or unknown")
        lower = item["lower_vertex_indices"]
        upper = item["upper_vertex_indices"]
        if (not isinstance(lower, (list, tuple))
                or not isinstance(upper, (list, tuple))):
            raise ContractError("neutral jaw surface indices must be sequences")
        typed_bins.append(JawSurfaceBin(tuple(lower), tuple(upper)))
    kwargs = dict(value)
    kwargs["joint_accessors"] = tuple(value["joint_accessors"]) if isinstance(
        value["joint_accessors"], (list, tuple)) else value["joint_accessors"]
    kwargs["weight_accessors"] = tuple(value["weight_accessors"]) if isinstance(
        value["weight_accessors"], (list, tuple)) else value["weight_accessors"]
    kwargs["surface_bins"] = tuple(typed_bins)
    return NeutralJawCalibration(**kwargs)
