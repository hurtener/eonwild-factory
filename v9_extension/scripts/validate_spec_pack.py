#!/usr/bin/env python3
"""Fail-closed structural validator for the Eonwild V9 biomechanics specification pack.

This validates schemas, mass normalization, phase coverage, event vocabulary,
program references, growth regimes, power-attack branches, and pinned inputs.
It deliberately does not claim to validate generated motion, biology, or taste.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(instance: Any, schema: dict[str, Any], label: str, errors: list[str]) -> None:
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.path)):
        location = ".".join(map(str, error.path)) or "<root>"
        errors.append(f"{label}: schema error at {location}: {error.message}")


def close(a: float, b: float, tol: float = 1e-8) -> bool:
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=tol)


def validate_phase_graph(phases: list[dict[str, Any]], label: str, errors: list[str]) -> None:
    if not phases:
        errors.append(f"{label}: no phases")
        return
    if not close(phases[0]["range"][0], 0.0):
        errors.append(f"{label}: first phase does not start at 0")
    if not close(phases[-1]["range"][1], 1.0):
        errors.append(f"{label}: last phase does not end at 1")
    seen: set[str] = set()
    previous_end = 0.0
    for index, phase in enumerate(phases):
        pid = phase["id"]
        if pid in seen:
            errors.append(f"{label}: duplicate phase id {pid}")
        seen.add(pid)
        start, end = map(float, phase["range"])
        if not 0.0 <= start < end <= 1.0:
            errors.append(f"{label}: invalid phase range {pid}={start,end}")
        if index and not close(start, previous_end, 1e-6):
            errors.append(f"{label}: phase gap/overlap before {pid}: {previous_end} -> {start}")
        previous_end = end


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output or root / "validation-report.json"
    errors: list[str] = []
    checks: list[dict[str, Any]] = []

    schemas = {p.stem: load_json(p) for p in (root / "schemas").glob("*.json")}
    required_schema_names = {
        "body-instance-profile.schema", "segment-mass-properties.schema", "growth-profile.schema",
        "motion-regime.schema", "motion-intent.schema", "motion-program.schema", "contact-state.schema",
        "biomechanical-plan.schema", "dynamic-action-plan.schema", "dynamic-action-spec.schema",
        "animation-spec.schema", "animation-catalog.schema", "joint-limit-envelope.schema",
        "joint-limit-catalog.schema", "actuation-capacity-profile.schema",
    }
    missing_schemas = sorted(required_schema_names - set(schemas))
    if missing_schemas:
        errors.append(f"missing required schemas: {missing_schemas}")
    checks.append({"id": "required_schemas", "expected": len(required_schema_names), "found": len(required_schema_names - set(missing_schemas))})

    global_contract = load_yaml(root / "motions/contracts/global-animation-contract.yaml")
    vocabulary = {name: kind for kind, names in global_contract["event_vocabulary"].items() for name in names}

    programs: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "motions/programs").glob("*.yaml")):
        program = load_yaml(path)
        validate_schema(program, schemas["motion-program.schema"], f"program:{path.name}", errors)
        if program["id"] in programs:
            errors.append(f"duplicate program id: {program['id']}")
        programs[program["id"]] = program
        text = path.read_text(encoding="utf-8").lower()
        if "tarbosaurus" in text or "bone_" in text:
            errors.append(f"generic program contains species/literal-bone hardcoding: {path.name}")
    if len(programs) != 12:
        errors.append(f"expected 12 motion programs, found {len(programs)}")
    checks.append({"id": "motion_programs", "expected": 12, "found": len(programs)})

    capacity_path = root / "profiles/families/heavy-predatory-biped-capacity-provisional.yaml"
    capacity = load_yaml(capacity_path)
    validate_schema(capacity, schemas["actuation-capacity-profile.schema"], "actuation_capacity", errors)
    capacity_group_ids = [group["id"] for group in capacity["capacity_groups"]]
    expected_capacity_groups = [
        "hindlimb_hip", "hindlimb_knee", "ankle_metatarsal_toe",
        "pelvis_trunk", "neck_head", "tail", "jaw",
    ]
    if capacity_group_ids != expected_capacity_groups:
        errors.append(
            f"capacity groups expected {expected_capacity_groups}, found {capacity_group_ids}"
        )
    if capacity["mode"] == "normalized" and capacity.get("normalization", {}).get("absolute_export_enabled") is not False:
        errors.append("normalized provisional capacity profile must disable absolute export")
    checks.append({
        "id": "actuation_capacity",
        "mode": capacity["mode"],
        "groups": capacity_group_ids,
        "provenance": capacity["provenance"]["status"],
    })

    joint_catalog_path = root / "profiles/species/tarbosaurus/joint-limits-provisional.yaml"
    joint_catalog = load_yaml(joint_catalog_path)
    joint_catalog_schema = json.loads(json.dumps(schemas["joint-limit-catalog.schema"]))
    joint_catalog_schema["properties"]["envelopes"]["items"] = schemas["joint-limit-envelope.schema"]
    validate_schema(joint_catalog, joint_catalog_schema, "joint_limit_catalog", errors)
    joint_ids: list[str] = []
    for envelope in joint_catalog["envelopes"]:
        validate_schema(
            envelope, schemas["joint-limit-envelope.schema"],
            f"joint_limit:{envelope.get('id', '<missing>')}", errors,
        )
        joint_ids.append(envelope["id"])
        if envelope["hard_envelope"].get("status") != "unresolved":
            errors.append(f"{envelope['id']}: provisional hard envelope should remain unresolved")
        if envelope["preferred_envelope"].get("status") != "unresolved":
            errors.append(f"{envelope['id']}: provisional preferred envelope should remain unresolved")
    if len(joint_ids) != len(set(joint_ids)):
        errors.append("joint-limit catalog ids are not unique")
    checks.append({
        "id": "joint_limit_catalog",
        "envelopes": len(joint_ids),
        "provenance": joint_catalog["provenance"]["status"],
    })

    body_paths = [
        root / "profiles/species/tarbosaurus/body-template-provisional.yaml",
        root / "profiles/fixtures/synthetic-heavy-biped.yaml",
    ]
    mass_summaries = []
    for path in body_paths:
        profile = load_yaml(path)
        validate_schema(profile, schemas["body-instance-profile.schema"], f"body:{path.name}", errors)
        for segment in profile["segments"]:
            validate_schema(segment, schemas["segment-mass-properties.schema"], f"segment:{profile['profile_id']}:{segment['id']}", errors)
        total = sum(float(s["mass_fraction"]) for s in profile["segments"])
        if not close(total, 1.0):
            errors.append(f"{profile['profile_id']}: segment mass fractions sum to {total}, not 1")
        if profile["mass"]["absolute_dynamics_enabled"] and not profile["mass"].get("mass_kg"):
            errors.append(f"{profile['profile_id']}: absolute dynamics enabled without mass_kg")
        if not profile["mass"]["absolute_dynamics_enabled"] and profile["mass"].get("mass_kg") is not None:
            errors.append(f"{profile['profile_id']}: disabled absolute dynamics should not expose a single authoritative mass")

        capacity_ref = root / profile["actuation_capacity_profile"]
        if not capacity_ref.is_file():
            errors.append(f"{profile['profile_id']}: actuation capacity profile does not resolve: {profile['actuation_capacity_profile']}")
        joint_ref = profile.get("joint_limit_catalog")
        referenced_joint_ids = {
            segment.get("joint_limit_profile")
            for segment in profile["segments"]
            if segment.get("joint_limit_profile")
        }
        if joint_ref is None and referenced_joint_ids:
            errors.append(f"{profile['profile_id']}: has joint-limit references but no catalog")
        elif joint_ref is not None:
            if not (root / joint_ref).is_file():
                errors.append(f"{profile['profile_id']}: joint-limit catalog does not resolve: {joint_ref}")
            if missing := sorted(referenced_joint_ids - set(joint_ids)):
                errors.append(f"{profile['profile_id']}: unresolved joint-limit ids: {missing}")

        mass_summaries.append({
            "profile_id": profile["profile_id"],
            "segments": len(profile["segments"]),
            "mass_fraction_sum": total,
            "absolute_dynamics_enabled": profile["mass"]["absolute_dynamics_enabled"],
            "joint_limit_references": len(referenced_joint_ids),
        })
    checks.append({"id": "body_profiles", "profiles": mass_summaries})

    growth = load_yaml(root / "profiles/species/tarbosaurus/growth-profile.yaml")
    growth_schema = json.loads(json.dumps(schemas["growth-profile.schema"]))
    growth_schema["properties"]["regimes"]["items"] = schemas["motion-regime.schema"]
    validate_schema(growth, growth_schema, "growth_profile", errors)
    regime_ids = [r["id"] for r in growth["regimes"]]
    expected_regimes = ["juvenile", "subadult", "adult", "heavy_adult"]
    if regime_ids != expected_regimes:
        errors.append(f"growth regimes expected {expected_regimes}, found {regime_ids}")
    if growth.get("tier_selection", {}).get("primary_trait") != "structural_mass_ratio_to_reference_adult":
        errors.append("growth tier selection is not primarily mass/weight based")
    for regime in growth["regimes"]:
        selector = regime["selector"]
        hysteresis = regime["hysteresis"]
        enter = float(selector["enter_at_or_above"])
        low, high = map(float, selector["nominal_range"])
        leave_below = float(hysteresis["leave_below"])
        leave_above = float(hysteresis["leave_above"])
        if selector["primary_trait"] != "structural_mass_ratio_to_reference_adult":
            errors.append(f"growth regime {regime['id']} is not mass-tier selected")
        if not (low <= enter <= high):
            errors.append(f"growth regime {regime['id']} enter threshold outside nominal range")
        if leave_below > enter:
            errors.append(f"growth regime {regime['id']} leave_below above enter threshold")
        if leave_above < high:
            errors.append(f"growth regime {regime['id']} leave_above below nominal high range")
    preserve = set(growth["switch_contract"]["preserve"])
    required_preserve = {"motion_program","phase","contact_state","COM_velocity","root_velocity","angular_momentum","tail_angle","tail_angular_velocity","target_commitment"}
    if missing := sorted(required_preserve - preserve):
        errors.append(f"growth switch contract missing preserved state: {missing}")
    checks.append({"id": "growth_regimes", "expected": expected_regimes, "found": regime_ids})

    catalog = load_yaml(root / "motions/tarbosaurus/catalog.yaml")
    catalog_schema = json.loads(json.dumps(schemas["animation-catalog.schema"]))
    catalog_schema["properties"]["animations"]["items"] = schemas["animation-spec.schema"]
    validate_schema(catalog, catalog_schema, "animation_catalog", errors)
    animations = catalog["animations"]
    if catalog.get("animation_count") != len(animations):
        errors.append("catalog animation_count does not match array length")
    if len(animations) != 29:
        errors.append(f"expected 29 animation contracts, found {len(animations)}")
    numbers = [a.get("number") for a in animations]
    if numbers != list(range(1, 30)):
        errors.append(f"animation numbers are not exactly 1..29: {numbers}")
    ids = [a["id"] for a in animations]
    if len(ids) != len(set(ids)):
        errors.append("animation ids are not unique")

    loop_ids = []
    for a in animations:
        label = f"animation:{a['number']:02d}:{a['id']}"
        validate_schema(a, schemas["animation-spec.schema"], label, errors)
        validate_phase_graph(a["phases"], label, errors)
        d = a["duration_s"]
        if not (float(d["min"]) <= float(d["target"]) <= float(d["max"])):
            errors.append(f"{label}: target duration outside min/max")
        if a["program"] not in programs:
            errors.append(f"{label}: unknown program {a['program']}")
        for e in a["events"]:
            name, kind = e["name"], e["kind"]
            if name not in vocabulary:
                errors.append(f"{label}: unknown event {name}")
            elif vocabulary[name] != kind:
                errors.append(f"{label}: event {name} kind {kind}, expected {vocabulary[name]}")
            if kind == "point" and "at" not in e and "phase" not in e:
                errors.append(f"{label}: point event {name} lacks at or phase")
            if kind == "window" and "range" not in e:
                errors.append(f"{label}: window event {name} lacks range")
        if a["loop"]:
            loop_ids.append(a["id"])
            if not any(e["name"] == "LOOP_SAFE" for e in a["events"]):
                errors.append(f"{label}: loop lacks LOOP_SAFE")
        if not a["validation"].get("animation_specific"):
            errors.append(f"{label}: no animation-specific validation")
    checks.append({"id": "animation_catalog", "expected": 29, "found": len(animations), "loop_count": len(loop_ids), "loop_ids": loop_ids})

    power = load_yaml(root / "motions/tarbosaurus/power-attack.yaml")
    validate_schema(power, schemas["dynamic-action-spec.schema"], "power_attack", errors)
    validate_phase_graph(power["phase_graph"], "power_attack", errors)
    if power["program"] != "dynamic_launch_attack":
        errors.append("power attack does not reference dynamic_launch_attack")
    variants = set(power["selection"]["variants"])
    if variants != {"power_attack_airborne", "power_attack_grounded"}:
        errors.append(f"power attack variants incomplete: {sorted(variants)}")
    required_branches = {"hit_target_yields", "hit_target_resists", "miss", "landing_failure"}
    if missing := sorted(required_branches - set(power["branches"])):
        errors.append(f"power attack missing branches: {missing}")
    for e in power["events"]:
        if e["name"] not in vocabulary:
            errors.append(f"power_attack: unknown event {e['name']}")
        elif vocabulary[e["name"]] != e["kind"]:
            errors.append(f"power_attack: event {e['name']} kind mismatch")
    critical = power["centroidal_math"]["critical_rule"].lower()
    if "whole-body com" not in critical or "pelvis/root" not in critical:
        errors.append("power attack does not explicitly distinguish whole-body COM from pelvis/root")
    checks.append({"id": "power_attack", "variants": sorted(variants), "phases": len(power["phase_graph"]), "branches": sorted(power["branches"])})

    pinned = load_yaml(root / "validation/pinned-regressions.yaml")
    pinned_by_id = {x["id"]: x for x in pinned["historical_inputs"]}
    expected_hashes = {
        "v8_2_approved_walk": "a2cf73a3c7d14a9c8fb9dffb8d9dc5bbcac330af3eeff772ca78c612801500b5",
        "v8_2_iteration_b_base": "bfe8e833721f1dc0b8b4a1df72a6ea933debb1c6d76ac6d7970ae3ed6c8f4bc2",
        "v8_1_iteration_38_source": "1b9a7d071c1b375e128beeb5bda68298e32b39aac3ea76a90afe7ca3f744b73e",
    }
    for pid, expected in expected_hashes.items():
        actual = pinned_by_id.get(pid, {}).get("sha256")
        if actual != expected:
            errors.append(f"pinned regression {pid} SHA mismatch: {actual}")
    checks.append({"id": "pinned_regressions", "review_repo_commit": pinned["review_repo_commit"], "verified_hash_contracts": len(expected_hashes)})

    example_specs = [
        (root / "examples/motion-intent.power-attack.yaml", schemas["motion-intent.schema"], "example_motion_intent"),
        (root / "examples/contact-state.left-foot-loaded.yaml", schemas["contact-state.schema"], "example_contact_state"),
        (root / "examples/dynamic-action-plan.power-attack-skeleton.yaml", schemas["dynamic-action-plan.schema"], "example_dynamic_action_plan"),
    ]
    example_count = 0
    for path, schema, label in example_specs:
        if not path.is_file():
            errors.append(f"required example missing: {path.relative_to(root)}")
            continue
        validate_schema(load_yaml(path), schema, label, errors)
        example_count += 1
    checks.append({"id": "examples", "expected": len(example_specs), "found": example_count})

    required_files = [
        "README.md", "docs/V9_ARCHITECTURE.md", "docs/V9_ANIMATION_SYSTEM.md", "docs/ANIMATION_CATALOG.md",
        "docs/IMPLEMENTATION_HANDOFF.md", "docs/RESEARCH_NOTES.md", "motions/tarbosaurus/catalog.yaml",
        "motions/tarbosaurus/power-attack.yaml", "validation/acceptance-gates.yaml",
    ]
    for relative in required_files:
        if not (root / relative).is_file():
            errors.append(f"required file missing: {relative}")
    checks.append({"id": "required_files", "expected": len(required_files), "found": sum((root / x).is_file() for x in required_files)})

    report = {
        "schema": "eonwild.spec_pack_validation.v1",
        "status": "PASS" if not errors else "FAIL",
        "scope": "Structural and internal-consistency validation only. No V9 motion GLB, biomechanics truth, or perceptual approval is claimed.",
        "root": str(root),
        "checks": checks,
        "error_count": len(errors),
        "errors": errors,
    }
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
