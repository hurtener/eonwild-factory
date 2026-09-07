"""Evidence-bound animal instances and deliberately limited motion proxies."""
from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Mapping

import numpy as np

from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _world_matrices, _world_position

SCHEMA = "eonwild.motion.animal-instance.v1"
G_M_S2 = 9.80665


def _quantity(value: Any, *, unit: str, name: str) -> float:
    if not isinstance(value, Mapping) or set(value) != {
        "value", "unit", "evidence_kind", "confidence", "source"
    }:
        raise ContractError(f"animal {name} needs value, units and provenance")
    number = value["value"]
    source = value["source"]
    if (isinstance(number, bool) or not isinstance(number, (int, float))
        or not math.isfinite(number) or number <= 0 or value["unit"] != unit
        or not isinstance(value["evidence_kind"], str) or not value["evidence_kind"]
        or value["confidence"] not in ("published_estimate", "derived_proxy", "measured_source_geometry")
        or not isinstance(source, Mapping) or not all(isinstance(source.get(k), str) and source[k]
                                                     for k in ("citation", "locator"))):
        raise ContractError(f"invalid animal {name}")
    return float(number)


def _vector_quantity(value: Any, *, name: str) -> list[float]:
    if not isinstance(value,Mapping) or set(value)!={"value","unit","evidence_kind","confidence","source"}:
        raise ContractError(f"animal {name} needs values, units and provenance")
    values=value["value"]
    if (value["unit"]!="m" or not isinstance(values,list) or len(values)!=3
        or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in values)
        or value["confidence"]!="measured_source_geometry" or not isinstance(value["evidence_kind"],str)
        or not isinstance(value["source"],Mapping) or not all(isinstance(value["source"].get(k),str) and value["source"][k] for k in ("citation","locator"))):
        raise ContractError(f"invalid animal {name}")
    return [float(v) for v in values]


def load_animal_instance(document: Mapping[str, Any], *, source_sha256: str) -> dict:
    required = {"schema", "id", "version", "taxon", "specimen", "life_stage", "morphology_comparison",
                "measurements", "geometry_calibration", "limitations"}
    if not isinstance(document, Mapping) or set(document) != required or document.get("schema") != SCHEMA:
        raise ContractError("unsupported animal instance schema")
    for key in ("id", "taxon", "specimen", "life_stage"):
        if not isinstance(document[key], str) or not document[key]:
            raise ContractError(f"animal {key} is required")
    if type(document["version"]) is not int or document["version"] < 1:
        raise ContractError("animal version must be positive")
    measurements = document["measurements"]
    if not isinstance(measurements, Mapping) or set(measurements) != {
        "body_mass", "hindlimb_length", "hip_height_proxy"
    }:
        raise ContractError("animal measurements are incomplete")
    mass = _quantity(measurements["body_mass"], unit="kg", name="body mass")
    hindlimb = _quantity(measurements["hindlimb_length"], unit="m", name="hindlimb length")
    hip_proxy = _quantity(measurements["hip_height_proxy"], unit="m", name="hip-height proxy")
    if not math.isclose(hip_proxy,.8*hindlimb,rel_tol=0,abs_tol=1e-12):
        raise ContractError("animal hip-height proxy differs from its declared 0.8 hindlimb basis")
    morphology=document["morphology_comparison"]
    if (not isinstance(morphology,Mapping) or set(morphology)!={"status","segment_order","taxon_level_lengths_m","source","use_policy"}
        or morphology["status"]!="UNVERIFIED" or morphology["segment_order"]!=["femur","tibia","central_metatarsal"]
        or not isinstance(morphology["taxon_level_lengths_m"],list) or len(morphology["taxon_level_lengths_m"])!=3
        or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0 for v in morphology["taxon_level_lengths_m"])
        or not isinstance(morphology["source"],Mapping) or not all(isinstance(morphology["source"].get(k),str) and morphology["source"][k] for k in ("citation","locator"))
        or not isinstance(morphology["use_policy"],str) or not morphology["use_policy"]):
        raise ContractError("invalid animal morphology comparison")
    calibration = document["geometry_calibration"]
    if not isinstance(calibration, Mapping) or set(calibration) != {
        "source_geometry_sha256", "scale_policy", "source_measurements"
    } or calibration.get("source_geometry_sha256") != source_sha256:
        raise ContractError("animal calibration is not bound to the admitted geometry")
    if calibration.get("scale_policy") != "uniform_hindlimb_match":
        raise ContractError("unsupported animal geometry scale policy")
    source = calibration["source_measurements"]
    if not isinstance(source, Mapping) or set(source) != {
        "skin_length", "left_semantic_hindlimb", "right_semantic_hindlimb", "left_semantic_segments",
        "right_semantic_segments", "pelvis_to_skin_floor"
    }:
        raise ContractError("animal source measurements are incomplete")
    values = {key:(_vector_quantity(value,name=key.replace("_"," ")) if key.endswith("segments") else
                   _quantity(value,unit="m",name=key.replace("_", " "))) for key,value in source.items()}
    source_hindlimb = .5 * (values["left_semantic_hindlimb"] + values["right_semantic_hindlimb"])
    scale = hindlimb / source_hindlimb
    if not .25 <= scale <= 4:
        raise ContractError("animal uniform geometry scale is outside the supported envelope")
    limitations = document["limitations"]
    if not isinstance(limitations, list) or not limitations or any(not isinstance(v,str) or not v for v in limitations):
        raise ContractError("animal limitations must be explicit")
    return {"document":dict(document), "mass_kg":mass, "hindlimb_length_m":hindlimb,
            "hip_height_proxy_m":hip_proxy, "source_measurements_m":values,
            "taxon_level_segment_lengths_m":[float(v) for v in morphology["taxon_level_lengths_m"]],
            "uniform_scale":scale}


def apply_uniform_geometry_scale(source: Glb, scale: float) -> None:
    if not math.isfinite(scale) or scale <= 0:
        raise ContractError("uniform geometry scale must be positive and finite")
    scene_index = source.document.get("scene", 0)
    scenes = source.document.get("scenes")
    if (not isinstance(scenes,list) or not 0 <= scene_index < len(scenes)
        or not isinstance(scenes[scene_index].get("nodes"),list) or not scenes[scene_index]["nodes"]):
        raise ContractError("animal scale requires explicit scene roots")
    roots = [int(index) for index in scenes[scene_index]["nodes"]]
    if set(roots) != {i for i,parent in enumerate(source.parents) if parent is None}:
        raise ContractError("animal scale requires every topology root in the active scene")
    for index in roots:
        current = np.asarray(source.rest_scale[index],dtype=float)
        scaled = tuple(float(v*scale) for v in current)
        source.nodes[index]["scale"] = list(scaled)
        source.rest_scale[index] = scaled


def verify_emitted_animal_geometry(animal: dict, emitted: Glb, roles: Mapping[str, Any],
                                   up_axis: Any, *, actual_semantic_height_m: float) -> None:
    """Bind the declared animal scale to each reopened emitted skeleton."""
    try:
        up = np.asarray(up_axis, dtype=float)
        up = up / np.linalg.norm(up)
        worlds = _world_matrices(emitted, emitted.rest_translation, emitted.rest_rotation, emitted.rest_scale)
        for side in ("left", "right"):
            indices = [emitted.name_to_node[name] for name in roles["legs"][side]["contactChain"]]
            points = [np.asarray(_world_position(worlds[index])) for index in indices]
            measured = [float(np.linalg.norm(after - before)) for before, after in zip(points, points[1:])]
            expected = np.asarray(animal["source_measurements_m"][f"{side}_semantic_segments"], dtype=float)
            expected *= float(animal["uniform_scale"])
            if len(measured) != len(expected) or not np.allclose(measured, expected, rtol=0, atol=2e-6):
                raise ContractError(f"emitted animal geometry scale differs for {side} semantic segments")
        pelvis = np.asarray(_world_position(worlds[emitted.name_to_node[roles["pelvis"]]]))
        toes = [emitted.name_to_node[name] for leg in roles["legs"].values()
                for chain in leg["toeChains"] for name in chain]
        if not toes:
            raise ContractError("emitted animal geometry has no bound digits")
        ground = min(float(np.asarray(_world_position(worlds[index])) @ up) for index in toes)
        measured_height = float(pelvis @ up - ground)
        if (isinstance(actual_semantic_height_m, bool)
                or not isinstance(actual_semantic_height_m, (int, float))
                or not math.isfinite(actual_semantic_height_m)
                or not math.isclose(measured_height, actual_semantic_height_m, rel_tol=0, abs_tol=2e-6)):
            raise ContractError("emitted animal semantic height differs from runtime calibration")
        animation = emitted.document.get("animations", [])
        if any(channel.get("target", {}).get("path") == "scale"
               for item in animation for channel in item.get("channels", [])):
            raise ContractError("emitted animal geometry scale must remain constant")
    except ContractError:
        raise
    except (AttributeError, KeyError, TypeError, IndexError, ValueError, ZeroDivisionError) as exc:
        raise ContractError("emitted animal geometry scale cannot be verified") from exc


def scaled_contact_profile(document: Mapping[str, Any], scale: float) -> dict:
    result=deepcopy(document)
    try: level=result["geometry"]["ground"]["level_m"]
    except (KeyError,TypeError) as exc: raise ContractError("animal scale requires an explicit contact plane") from exc
    if isinstance(level,bool) or not isinstance(level,(int,float)) or not math.isfinite(level):
        raise ContractError("animal contact plane must be finite numeric")
    result["geometry"]["ground"]["level_m"]=float(level*scale)
    return result


def verify_source_calibration(animal: dict, source: Glb, roles: Mapping[str, Any],
                              contact_profile: Mapping[str, Any], forward: Any, up: Any) -> dict:
    """Recompute the committed source measurements from the bound rig and skin."""
    from ..contact_gauge import (_column_major_matrix, _mat_mul, _mat_point,
        _normalize_skin_weights, _read_glb_accessor)
    forward,up=np.asarray(forward,dtype=float),np.asarray(up,dtype=float)
    worlds=_world_matrices(source,source.rest_translation,source.rest_rotation,source.rest_scale)
    measured={}
    for side,key in (("left","left_semantic_hindlimb"),("right","right_semantic_hindlimb")):
        try: indices=[source.name_to_node[name] for name in roles["legs"][side]["contactChain"]]
        except (KeyError,TypeError) as exc: raise ContractError("animal calibration needs semantic biped legs") from exc
        points=[np.asarray(_world_position(worlds[index])) for index in indices]
        segments=[float(np.linalg.norm(b-a)) for a,b in zip(points,points[1:])]
        measured[key]=sum(segments);measured[f"{side}_semantic_segments"]=segments
    try:
        geometry=contact_profile["geometry"];skin=source.document["skins"][int(geometry["skin_index"])]
        positions=_read_glb_accessor(source,geometry["position_accessor"],label="animal source positions")
        joints=[_read_glb_accessor(source,index,label="animal source joints") for index in geometry["joint_accessors"]]
        weights=[_read_glb_accessor(source,index,label="animal source weights") for index in geometry["weight_accessors"]]
        influences=_normalize_skin_weights(joints,weights,vertex_count=len(positions),joint_count=len(skin["joints"]))
        inverse=[_column_major_matrix(row) for row in _read_glb_accessor(source,skin["inverseBindMatrices"],label="animal inverse bind")]
        matrices={node:_mat_mul(worlds[node],inverse[slot]) for slot,node in enumerate(skin["joints"])}
    except (KeyError,TypeError,IndexError) as exc:
        raise ContractError("animal calibration needs bound skinned source geometry") from exc
    skinned=[]
    for vertex,position in enumerate(positions):
        point=np.zeros(3)
        for slot,weight in influences[vertex]:
            point += weight*np.asarray(_mat_point(matrices[skin["joints"][slot]],position))
        skinned.append(point)
    skinned=np.asarray(skinned)
    projected_forward=skinned@forward;projected_up=skinned@up
    measured["skin_length"]=float(np.ptp(projected_forward))
    pelvis=np.asarray(_world_position(worlds[source.name_to_node[roles["pelvis"]]]))
    measured["pelvis_to_skin_floor"]=float(pelvis@up-np.min(projected_up))
    expected=animal["source_measurements_m"]
    for key,value in measured.items():
        if not np.allclose(value,expected[key],rtol=0,atol=2e-6):
            raise ContractError(f"animal source calibration differs for {key}")
    return measured


def biomechanics_report(animal: dict, plan: Mapping[str, Any], *, actual_semantic_height_m: float) -> dict:
    rows = plan.get("samples")
    if not isinstance(rows,list) or len(rows)<3 or not math.isfinite(actual_semantic_height_m) or actual_semantic_height_m<=0:
        raise ContractError("biomechanics report needs a measured emitted plan")
    times=np.asarray([row["time_s"] for row in rows],dtype=float)
    positions=np.asarray([row["root_forward_m"] for row in rows],dtype=float)
    if not np.isfinite(times).all() or not np.isfinite(positions).all() or np.any(np.diff(times)<=0):
        raise ContractError("biomechanics report received an invalid trajectory")
    speeds=np.gradient(positions,times,edge_order=2)
    accelerations=np.gradient(speeds,times,edge_order=2)
    pelvis=np.asarray([row["pelvis_height_offset_m"] for row in rows],dtype=float)
    if not np.isfinite(pelvis).all():
        raise ContractError("biomechanics report received invalid pelvis motion")
    pelvis_velocity=np.gradient(pelvis,times,edge_order=2)
    pelvis_acceleration=np.gradient(pelvis_velocity,times,edge_order=2)
    peak_speed=float(np.max(np.abs(speeds)))
    peak_acceleration=float(np.max(np.abs(accelerations)))
    mass=animal["mass_kg"]
    proxy=animal["hip_height_proxy_m"]
    absolute_pelvis=actual_semantic_height_m+pelvis
    hindlimb=animal["hindlimb_length_m"]
    return {"schema":"eonwild.motion.biomechanics-report.v1",
        "animal_id":animal["document"]["id"], "specimen":animal["document"]["specimen"],
        "geometry":{"uniform_scale":animal["uniform_scale"],
            "target_hindlimb_length_m":animal["hindlimb_length_m"],
            "actual_semantic_pelvis_to_toe_plane_m":actual_semantic_height_m,
            "study_hip_height_proxy_m":proxy,
            "planned_semantic_pelvis_height_range_m":[float(np.min(absolute_pelvis)),float(np.max(absolute_pelvis))],
            "planned_pelvis_height_to_published_hindlimb_ratio_range":
                [float(np.min(absolute_pelvis)/hindlimb),float(np.max(absolute_pelvis)/hindlimb)],
            "study_hip_height_proxy_basis":"0.8 * published femur+tibia+central-metatarsal hindlimb length; posture estimate"},
        "anatomical_fit":{"status":"UNVERIFIED","policy":"comparison only; uniform scaling does not alter relative bone proportions",
            "source_semantic_segment_fractions":
                (np.mean(np.asarray([animal["source_measurements_m"]["left_semantic_segments"],animal["source_measurements_m"]["right_semantic_segments"]]),axis=0)/
                 np.sum(np.mean(np.asarray([animal["source_measurements_m"]["left_semantic_segments"],animal["source_measurements_m"]["right_semantic_segments"]]),axis=0))).tolist(),
            "published_taxon_level_segment_fractions":
                (np.asarray(animal["taxon_level_segment_lengths_m"])/sum(animal["taxon_level_segment_lengths_m"])).tolist(),
            "published_comparison_specimen":"UNSPECIFIED"},
        "kinematics":{"peak_root_speed_mps":peak_speed,"peak_root_acceleration_mps2":peak_acceleration,
            "pelvis_height_offset_range_m":[float(np.min(pelvis)),float(np.max(pelvis))],
            "pelvis_vertical_velocity_range_mps":[float(np.min(pelvis_velocity)),float(np.max(pelvis_velocity))],
            "pelvis_vertical_acceleration_range_mps2":[float(np.min(pelvis_acceleration)),float(np.max(pelvis_acceleration))],
            "peak_pelvis_vertical_acceleration_in_g":float(np.max(np.abs(pelvis_acceleration)))/G_M_S2,
            "froude_using_study_hip_proxy":peak_speed**2/(G_M_S2*proxy),
            "froude_using_actual_semantic_height":peak_speed**2/(G_M_S2*actual_semantic_height_m)},
        "mass_proxies":{"body_mass_kg":mass,"weight_newtons":mass*G_M_S2,
            "peak_root_translational_inertial_load_proxy_newtons":mass*peak_acceleration,
            "peak_pelvis_mass_times_acceleration_proxy_newtons":mass*float(np.max(np.abs(pelvis_acceleration))),
            "peak_pelvis_mass_times_acceleration_over_body_weight":float(np.max(np.abs(pelvis_acceleration)))/G_M_S2},
        "pelvis_acceleration_force_interpretation":"NOT_EVALUATED; pelvis is not whole-body center of mass",
        "force_aware_solver":"NOT_IMPLEMENTED", "contact_force_distribution":"NOT_EVALUATED",
        "segment_inertia":"NOT_EVALUATED", "stress_and_tissue_limits":"NOT_EVALUATED",
        "biological_validation":"NOT_VALIDATED"}
