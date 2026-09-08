from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path

import pytest

from eonwild_motion.errors import ContractError
from eonwild_motion.factory.animal import apply_uniform_geometry_scale
from eonwild_motion.factory.source_identity import validate_frozen_source_with_uniform_scale
from eonwild_motion.glb.container import Glb


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = "2cdd9017075626e27acdeef09b6787985ca82054cc0f315c09b092920ea7374f"
SOURCE = ROOT / "assets/sha256" / f"{SOURCE_SHA}.glb"


def source() -> Glb:
    value = Glb.from_bytes(SOURCE.read_bytes())
    assert hashlib.sha256(value.raw).hexdigest() == SOURCE_SHA
    return value


def test_frozen_source_accepts_exact_state_and_one_uniform_root_scale():
    exact = source()
    frozen, factor = validate_frozen_source_with_uniform_scale(exact, SOURCE_SHA)
    assert frozen.raw == exact.raw
    assert factor == 1.0

    scaled = source()
    apply_uniform_geometry_scale(scaled, 0.75)
    frozen, factor = validate_frozen_source_with_uniform_scale(scaled, SOURCE_SHA)
    assert frozen.raw == scaled.raw
    assert factor == pytest.approx(0.75, abs=1e-12)


@pytest.mark.parametrize("mutation", [
    lambda value: value.rest_rotation.__setitem__(0, (0.0, 0.0, 1.0, 0.0)),
    lambda value: value.name_to_node.__setitem__("forged", 0),
    lambda value: value.parents.__setitem__(1, None),
    lambda value: value.document["nodes"][0].__setitem__("translation", [1.0, 0.0, 0.0]),
    lambda value: setattr(value, "binary", bytes([value.binary[0] ^ 1]) + value.binary[1:]),
])
def test_frozen_source_rejects_cached_document_topology_or_binary_mutation(mutation):
    changed = source()
    mutation(changed)
    with pytest.raises(ContractError):
        validate_frozen_source_with_uniform_scale(changed, SOURCE_SHA)


@pytest.mark.parametrize("scales", [
    ([0.75, 0.76, 0.75],),
    ([0.10, 0.10, 0.10],),
    ([9.0, 9.0, 9.0],),
    (["bad", 1.0, 1.0],),
])
def test_frozen_source_rejects_nonuniform_out_of_range_or_malformed_scale(scales):
    changed = source()
    roots = changed.document["scenes"][changed.document.get("scene", 0)]["nodes"]
    assert len(roots) == len(scales)
    for root, scale in zip(roots, scales):
        changed.document["nodes"][root]["scale"] = deepcopy(scale)
        changed.rest_scale[root] = tuple(scale)
    with pytest.raises(ContractError):
        validate_frozen_source_with_uniform_scale(changed, SOURCE_SHA)


def test_frozen_source_rejects_wrong_frozen_hash():
    with pytest.raises(ContractError, match="stale"):
        validate_frozen_source_with_uniform_scale(source(), "0" * 64)
