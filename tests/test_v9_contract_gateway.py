from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from eonwild_motion.contracts.v9_loader import load_v9_document, validate_v9_document
from eonwild_motion.contracts.v9_migration import (
    ExplicitMigration,
    migrate_document,
    require_explicit_source_schema,
)
from eonwild_motion.contracts.v9_models import (
    BodyInstanceProfile,
    V9_SCHEMA_IDS,
    canonical_hash,
)
from eonwild_motion.errors import ContractError
from eonwild_motion.hashing import sha256_file
from eonwild_motion.planning.stationary_support import build_stationary_support_plan


ROOT = Path(__file__).resolve().parents[1]
V9_ROOT = ROOT / "profiles/v9"
INTENT = V9_ROOT / "intent.stationary-support.json"
PROGRAM = V9_ROOT / "program.stationary-support.json"
TARBO = V9_ROOT / "tarbosaurus-provisional.json"
SYNTHETIC = V9_ROOT / "synthetic-heavy-biped.json"
CONTACTS = (
    V9_ROOT / "contact.left-foot.loaded.json",
    V9_ROOT / "contact.right-foot.loaded.json",
)


class V9ContractGatewayTests(unittest.TestCase):
    def _plan(self, body: Path):
        return build_stationary_support_plan(
            INTENT,
            PROGRAM,
            body,
            CONTACTS,
            repository=ROOT,
        )

    def _mutated_document(self, source: Path, mutate):
        temporary = tempfile.TemporaryDirectory()
        destination = Path(temporary.name) / source.name
        document = json.loads(source.read_text(encoding="utf-8"))
        mutate(document)
        destination.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return temporary, destination

    def test_tarbosaurus_fixture_produces_grounded_normalized_plan(self):
        result = self._plan(TARBO)

        self.assertEqual(result.plan["schema"], V9_SCHEMA_IDS["plan"])
        self.assertTrue(result.plan["grounded"])
        self.assertEqual(result.plan["centroidal_state"]["mass_mode"], "normalized")
        self.assertIsNone(result.plan["centroidal_state"]["mass_kg"])
        self.assertFalse(result.plan["feasibility"]["absolute_dynamics_enabled"])
        self.assertEqual(result.evidence["status"], "PASS")
        self.assertEqual(result.evidence["plan_sha256"], result.plan_sha256)
        self.assertEqual(result.evidence["evidence_sha256"], result.evidence_sha256)

    def test_synthetic_fixture_uses_same_generic_path(self):
        normalized = self._plan(TARBO)
        absolute = self._plan(SYNTHETIC)

        self.assertNotEqual(
            normalized.plan["centroidal_state"]["com_m"],
            absolute.plan["centroidal_state"]["com_m"],
        )
        self.assertEqual(absolute.plan["centroidal_state"]["mass_mode"], "absolute")
        self.assertEqual(absolute.plan["centroidal_state"]["mass_kg"], 1500.0)
        self.assertTrue(absolute.plan["feasibility"]["absolute_dynamics_enabled"])
        tarbo_document = load_v9_document(
            TARBO, repository=ROOT, expected_schema=V9_SCHEMA_IDS["body"]
        )
        synthetic_document = load_v9_document(
            SYNTHETIC, repository=ROOT, expected_schema=V9_SCHEMA_IDS["body"]
        )
        self.assertNotEqual(tarbo_document["segments"], synthetic_document["segments"])
        self.assertNotEqual(
            canonical_hash(tarbo_document["segments"]),
            canonical_hash(synthetic_document["segments"]),
        )
        planner_source = (
            ROOT / "src/eonwild_motion/planning/stationary_support.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("Tarbosaurus", planner_source)
        self.assertNotIn("tarbosaurus", planner_source)

    def test_body_model_preserves_body_frame_and_inertia(self):
        document = load_v9_document(
            TARBO, repository=ROOT, expected_schema=V9_SCHEMA_IDS["body"]
        )
        model = BodyInstanceProfile.from_document(document)

        self.assertEqual(model.segment_com_frame, "body")
        self.assertEqual(len(model.segments), 17)
        self.assertTrue(
            all(all(value > 0 for value in segment.inertia_diagonal_normalized) for segment in model.segments)
        )

    def test_plan_marks_support_as_bookkeeping_only(self):
        result = self._plan(TARBO)

        self.assertEqual(result.plan["centroidal_state"]["com_frame"], "body")
        self.assertEqual(result.plan["support"]["evaluation"], "bookkeeping_only")
        self.assertFalse(result.plan["feasibility"]["physics_evaluated"])
        self.assertEqual(result.plan["gravity_mps2"], [0.0, -9.81, 0.0])
        self.assertTrue(result.evidence["checks"]["support_physics_unevaluated"])

    def test_double_run_is_byte_and_hash_deterministic(self):
        first = self._plan(TARBO)
        second = self._plan(TARBO)

        self.assertEqual(first.plan, second.plan)
        self.assertEqual(first.evidence, second.evidence)
        self.assertEqual(first.plan_sha256, second.plan_sha256)
        self.assertEqual(first.evidence_sha256, second.evidence_sha256)
        self.assertEqual(canonical_hash(first.report), canonical_hash(second.report))

    def test_report_can_be_emitted_and_reloaded(self):
        with tempfile.TemporaryDirectory() as temporary:
            report_path = Path(temporary) / "stationary-support.json"
            result = build_stationary_support_plan(
                INTENT,
                PROGRAM,
                TARBO,
                CONTACTS,
                repository=ROOT,
                report_path=report_path,
            )
            self.assertTrue(report_path.is_file())
            report = load_v9_document(
                report_path,
                repository=ROOT,
                expected_schema=V9_SCHEMA_IDS["evidence"],
            )
            self.assertEqual(report["plan"]["plan_id"], result.plan["plan_id"])
            self.assertEqual(report["evidence"]["evidence_sha256"], result.evidence_sha256)

    def test_nested_plan_unknown_property_and_hash_tamper_fail_closed(self):
        result = self._plan(TARBO)
        report = copy.deepcopy(result.report)
        report["plan"]["unexpected"] = True
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tampered-plan.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "schema validation failed"):
                load_v9_document(
                    path,
                    repository=ROOT,
                    expected_schema=V9_SCHEMA_IDS["evidence"],
                )

    def test_input_manifest_requires_named_inputs_and_source_hashes(self):
        result = self._plan(TARBO)
        self.assertEqual(
            set(result.evidence["input_manifest"]),
            {"intent", "program", "body", "contact_left_foot", "contact_right_foot"},
        )

        report = copy.deepcopy(result.report)
        report["evidence"]["input_manifest"] = {}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "empty-manifest.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "schema validation failed"):
                load_v9_document(
                    path,
                    repository=ROOT,
                    expected_schema=V9_SCHEMA_IDS["evidence"],
                )

        report = copy.deepcopy(result.report)
        report["evidence"]["input_manifest"]["body"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "stale-manifest.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "input manifest hash mismatch"):
                load_v9_document(
                    path,
                    repository=ROOT,
                    expected_schema=V9_SCHEMA_IDS["evidence"],
                )

        report = copy.deepcopy(result.report)
        report["evidence"]["plan_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "tampered-hash.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "plan hash"):
                load_v9_document(
                    path,
                    repository=ROOT,
                    expected_schema=V9_SCHEMA_IDS["evidence"],
                )

    def test_input_manifest_body_substitution_is_bound_to_plan(self):
        result = self._plan(TARBO)
        report = copy.deepcopy(result.report)
        body_path = ROOT / "profiles/v9/synthetic-heavy-biped.json"
        report["evidence"]["input_manifest"]["body"] = {
            "path": "profiles/v9/synthetic-heavy-biped.json",
            "sha256": sha256_file(body_path),
        }
        evidence_without_hash = report["evidence"]
        evidence_without_hash.pop("evidence_sha256")
        evidence_without_hash["evidence_sha256"] = canonical_hash(evidence_without_hash)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "body-substitution.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "body manifest identity"):
                load_v9_document(
                    path,
                    repository=ROOT,
                    expected_schema=V9_SCHEMA_IDS["evidence"],
                )

    def test_input_manifest_contact_substitution_is_bound_to_plan(self):
        result = self._plan(TARBO)
        report = copy.deepcopy(result.report)
        right_path = ROOT / "profiles/v9/contact.right-foot.loaded.json"
        report["evidence"]["input_manifest"]["contact_left_foot"] = {
            "path": "profiles/v9/contact.right-foot.loaded.json",
            "sha256": sha256_file(right_path),
        }
        evidence_without_hash = report["evidence"]
        evidence_without_hash.pop("evidence_sha256")
        evidence_without_hash["evidence_sha256"] = canonical_hash(evidence_without_hash)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "contact-substitution.json"
            path.write_text(json.dumps(report), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "contact manifest identity"):
                load_v9_document(
                    path,
                    repository=ROOT,
                    expected_schema=V9_SCHEMA_IDS["evidence"],
                )

    def test_missing_schema_fails_closed(self):
        temporary, path = self._mutated_document(INTENT, lambda document: document.pop("schema"))
        with temporary:
            with self.assertRaisesRegex(ContractError, "missing schema"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["intent"])

    def test_unknown_property_fails_closed(self):
        temporary, path = self._mutated_document(
            INTENT, lambda document: document.update({"unexpected": True})
        )
        with temporary:
            with self.assertRaisesRegex(ContractError, "schema validation failed"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["intent"])

    def test_stale_family_alias_fails_closed(self):
        temporary, path = self._mutated_document(
            TARBO, lambda document: document.update({"family": "heavy-predatory-biped"})
        )
        with temporary:
            with self.assertRaisesRegex(ContractError, "schema validation failed"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["body"])

    def test_body_topology_requires_one_acyclic_root_with_existing_parents(self):
        def missing_parent(document):
            document["segments"][1]["parent_id"] = "missing"

        temporary, path = self._mutated_document(TARBO, missing_parent)
        with temporary:
            with self.assertRaisesRegex(ContractError, "missing parent"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["body"])

        def cycle(document):
            document["segments"][1]["parent_id"] = "chest"
            document["segments"][2]["parent_id"] = "trunk"

        temporary, path = self._mutated_document(TARBO, cycle)
        with temporary:
            with self.assertRaisesRegex(ContractError, "cycle"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["body"])

        def two_roots(document):
            document["segments"][1]["parent_id"] = None

        temporary, path = self._mutated_document(TARBO, two_roots)
        with temporary:
            with self.assertRaisesRegex(ContractError, "exactly one root"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["body"])

    def test_body_frame_com_field_is_required(self):
        def legacy_field(document):
            document["segments"][0]["com_local_m"] = document["segments"][0].pop("com_body_m")

        temporary, path = self._mutated_document(TARBO, legacy_field)
        with temporary:
            with self.assertRaisesRegex(ContractError, "schema validation failed"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["body"])

    def test_stale_axis_alias_fails_closed(self):
        def mutate(document):
            document["coordinate_system"]["forward_axis"] = "X"

        temporary, path = self._mutated_document(INTENT, mutate)
        with temporary:
            with self.assertRaisesRegex(ContractError, "schema validation failed"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["intent"])

    def test_ambiguous_units_fail_closed(self):
        def mutate(document):
            document["coordinate_system"]["units"] = "meters"

        temporary, path = self._mutated_document(INTENT, mutate)
        with temporary:
            with self.assertRaisesRegex(ContractError, "schema validation failed"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["intent"])

    def test_provisional_profile_cannot_enable_absolute_dynamics(self):
        def mutate(document):
            document["mass"].update(
                {
                    "mode": "absolute",
                    "total_mass_kg": 500.0,
                    "absolute_dynamics_enabled": True,
                    "absolute_policy": "fixture_absolute_allowed",
                }
            )

        temporary, path = self._mutated_document(TARBO, mutate)
        with temporary:
            with self.assertRaisesRegex(ContractError, "schema validation failed"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["body"])

    def test_nonfinite_exponent_is_rejected_in_contact_body_and_evidence(self):
        contact_text = CONTACTS[0].read_text(encoding="utf-8").replace(
            '"time_s": 0.0', '"time_s": 1e999', 1
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / CONTACTS[0].name
            path.write_text(contact_text, encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "not finite"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["contact"])

        body_text = TARBO.read_text(encoding="utf-8").replace(
            '"mass_fraction": 0.16', '"mass_fraction": 1e999', 1
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / TARBO.name
            path.write_text(body_text, encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "not finite"):
                load_v9_document(path, repository=ROOT, expected_schema=V9_SCHEMA_IDS["body"])

        result = self._plan(TARBO)
        report_text = json.dumps(result.report, sort_keys=True, separators=(",", ":"))
        report_text = report_text.replace(
            '"com_m":[0.0,1.2919,0.0771]',
            '"com_m":[1e999,1.2919,0.0771]',
            1,
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "nonfinite-evidence.json"
            path.write_text(report_text, encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "not finite"):
                load_v9_document(
                    path,
                    repository=ROOT,
                    expected_schema=V9_SCHEMA_IDS["evidence"],
                )

    def test_canonical_hash_rejects_nonfinite_values(self):
        with self.assertRaisesRegex(ContractError, "not finite"):
            canonical_hash({"nested": [float("nan")]})

    def test_cross_document_effector_mismatch_fails_closed(self):
        def mutate(document):
            document["phase_template"][0]["contact_effectors"] = [
                "left_foot",
                "right_foot",
                "tail_tip",
            ]

        temporary, path = self._mutated_document(PROGRAM, mutate)
        with temporary:
            with self.assertRaises(ContractError):
                build_stationary_support_plan(
                    INTENT,
                    path,
                    TARBO,
                    CONTACTS,
                    repository=ROOT,
                )

    def test_migration_requires_declared_schema_and_complete_map(self):
        with self.assertRaisesRegex(ContractError, "missing schema"):
            require_explicit_source_schema({})

        migration = ExplicitMigration(
            source_schema="eonwild.motion.v9.intent-draft.v1",
            target_schema=V9_SCHEMA_IDS["intent"],
            field_map={"id": "id"},
        )
        with self.assertRaisesRegex(ContractError, "unmapped source fields"):
            migrate_document(
                {"schema": migration.source_schema, "id": "intent", "units": "meters"},
                migration,
            )

    def test_migration_rejects_stale_aliases_instead_of_coercing(self):
        migration = ExplicitMigration(
            source_schema="eonwild.motion.v9.body-draft.v1",
            target_schema=V9_SCHEMA_IDS["body"],
            field_map={"family": "family"},
        )
        with self.assertRaisesRegex(ContractError, "family alias"):
            migrate_document(
                {"schema": migration.source_schema, "family": "heavy-predatory-biped"},
                migration,
            )


if __name__ == "__main__":
    unittest.main()
