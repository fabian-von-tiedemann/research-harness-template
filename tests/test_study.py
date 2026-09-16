import tempfile
import unittest
from pathlib import Path

from harness.common import ContractError, atomic_json, read_json
from harness.study import apply_rule, create, evaluate, report, validate_protocol


def protocol(**overrides):
    p = {
        "schema_version": 1,
        "id": "T-01",
        "investigation": "T",
        "question": "Does x beat y?",
        "hypothesis": "x beats y by at least 0.15",
        "rival": "x does not beat y",
        "measures": [{"id": "m1", "description": "difference x minus y", "unit": "share"}],
        "interpretation_rule": {
            "measure": "m1",
            "supports_hypothesis_if": {"op": ">=", "value": 0.15},
            "supports_rival_if": {"op": "<=", "value": 0.0},
        },
        "exploratory": False,
        "affects": [],
        "inputs": ["inputs/data.csv"],
        "data_kind": "simulated",
        "limitations": "fixture",
    }
    p.update(overrides)
    return p


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / "study"
        (self.src / "inputs").mkdir(parents=True)
        (self.src / "inputs/data.csv").write_text("a,b\n1,2\n")
        self.protocol_path = self.src / "protocol.json"
        atomic_json(self.protocol_path, protocol())
        self.out = self.src / "frozen"

    def write_result(self, value):
        atomic_json(self.out / "result.json", {"measures": {"m1": value}, "note": "fixture"})

    def test_apply_rule_three_outcomes(self):
        rule = protocol()["interpretation_rule"]
        self.assertEqual(apply_rule(rule, 0.3), "supports_hypothesis")
        self.assertEqual(apply_rule(rule, -0.1), "supports_rival")
        self.assertEqual(apply_rule(rule, 0.05), "undecided")

    def test_validate_rejects_overlapping_thresholds(self):
        rule = {"measure": "m1", "supports_hypothesis_if": {"op": ">=", "value": 0.1}, "supports_rival_if": {"op": "<=", "value": 0.2}}
        with self.assertRaises(ContractError):
            validate_protocol(protocol(interpretation_rule=rule))
        rule["supports_rival_if"] = {"op": "<", "value": 0.1}
        validate_protocol(protocol(interpretation_rule=rule))
        rule["supports_rival_if"] = {"op": "<=", "value": 0.1}
        with self.assertRaises(ContractError):
            validate_protocol(protocol(interpretation_rule=rule))

    def test_validate_requires_fields_and_known_measure(self):
        with self.assertRaises(ContractError):
            validate_protocol(protocol(hypothesis=""))
        with self.assertRaises(ContractError):
            validate_protocol(protocol(interpretation_rule={**protocol()["interpretation_rule"], "measure": "m9"}))
        with self.assertRaises(ContractError):
            validate_protocol(protocol(data_kind="synthetic"))
        with self.assertRaises(ContractError):
            validate_protocol(protocol(inputs=["manifest.json"]))
        validate_protocol(protocol())

    def test_exploratory_requires_null_rule_and_gives_descriptive(self):
        with self.assertRaises(ContractError):
            validate_protocol(protocol(exploratory=True))
        with self.assertRaises(ContractError):
            validate_protocol(protocol(interpretation_rule=None))
        atomic_json(self.protocol_path, protocol(exploratory=True, interpretation_rule=None))
        create(self.protocol_path, self.out)
        self.write_result(0.3)
        self.assertEqual(evaluate(self.out)["outcome"], "descriptive")

    def test_create_freezes_and_hashes(self):
        manifest = create(self.protocol_path, self.out)
        self.assertEqual(manifest["status"], "frozen")
        self.assertEqual(set(manifest["hashes"]), {"protocol.json", "inputs/data.csv"})
        self.assertEqual(read_json(self.out / "manifest.json"), manifest)

    def test_create_refuses_existing_dir_and_escaping_inputs(self):
        create(self.protocol_path, self.out)
        with self.assertRaises(ContractError):
            create(self.protocol_path, self.out)
        atomic_json(self.protocol_path, protocol(inputs=["../outside.csv"]))
        (self.root / "outside.csv").write_text("x")
        with self.assertRaises(ContractError):
            create(self.protocol_path, self.src / "frozen2")

    def test_create_checks_affects_against_register(self):
        (self.root / "knowledge").mkdir()
        atomic_json(self.root / "knowledge/registry.json", {"schema_version": 1, "sources": [], "claims": [], "documents": []})
        atomic_json(self.protocol_path, protocol(affects=["K999"]))
        with self.assertRaises(ContractError):
            create(self.protocol_path, self.out, root=self.root)
        create(self.protocol_path, self.out)

    def test_evaluate_outcomes_and_hashes(self):
        create(self.protocol_path, self.out)
        self.write_result(0.3)
        result = evaluate(self.out)
        self.assertEqual(result["outcome"], "supports_hypothesis")
        self.assertEqual(result["measures"], {"m1": 0.3})
        self.assertEqual(result["data_kind"], "simulated")
        self.assertEqual(len(result["manifest_sha256"]), 64)
        self.assertEqual(len(result["result_sha256"]), 64)
        self.write_result(-0.2)
        self.assertEqual(evaluate(self.out)["outcome"], "supports_rival")
        self.write_result(0.1)
        self.assertEqual(evaluate(self.out)["outcome"], "undecided")

    def test_evaluate_rejects_tampered_input(self):
        create(self.protocol_path, self.out)
        self.write_result(0.3)
        (self.out / "inputs/data.csv").write_text("a,b\n9,9\n")
        with self.assertRaises(ContractError):
            evaluate(self.out)

    def test_evaluate_rejects_missing_measure_or_result(self):
        create(self.protocol_path, self.out)
        with self.assertRaises(ContractError):
            evaluate(self.out)
        atomic_json(self.out / "result.json", {"measures": {"m2": 1}})
        with self.assertRaises(ContractError):
            evaluate(self.out)
        atomic_json(self.out / "result.json", {"measures": {"m1": "high"}})
        with self.assertRaises(ContractError):
            evaluate(self.out)

    def test_report_lists_protocol_hashes_and_commit_state(self):
        create(self.protocol_path, self.out)
        text = report(self.out)
        self.assertIn("# Pre-registered study T-01", text)
        self.assertIn("inputs/data.csv", text)
        self.assertIn("not committed yet", text)
        self.write_result(0.3)
        atomic_json(self.out / "evaluation.json", evaluate(self.out))
        self.assertIn("supports_hypothesis", report(self.out))


if __name__ == "__main__":
    unittest.main()
