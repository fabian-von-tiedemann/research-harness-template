import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from harness.registry import CLAIM_TYPES, SECTIONS, build_index, context, impact, snapshot, validate_registry

EXCERPT = "line one\nline two\nline three\n"


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "knowledge/snapshots").mkdir(parents=True)
        sha = hashlib.sha256(EXCERPT.encode()).hexdigest()
        (self.root / f"knowledge/snapshots/{sha}.txt").write_text(EXCERPT)
        self.data = {
            "schema_version": 1,
            "sources": [{"id": "S001", "family": "S001", "version": "2026-09-16-v1", "snapshot": f"knowledge/snapshots/{sha}.txt", "sha256": sha, "origin": "fixture.txt", "anchor": "L1-L3", "kind": "dataset", "access": "fixture", "depends_on": []}],
            "claims": [{"id": "K001", "statement": "fixture claim", "type": "derivation", "status": "provisional", "scope": "fixture", "reconsider_if": "fixture changes", "depends_on": [], "evidence": [{"source": "S001", "anchor": "L1-L3", "relation": "supports", "reading": "fixture"}], "history": [{"date": "2026-09-16", "status": "provisional", "reason": "fixture"}], "version": 1, "review_status": "unreviewed", "review_history": [{"date": "2026-09-16", "status": "unreviewed", "reason": "fixture"}]}],
            "documents": [{"id": "DOC-1", "path": "chapter.md", "depends_on": ["K001"]}],
        }
        self.path = self.root / "knowledge/registry.json"
        self.save()

    def save(self):
        self.path.write_text(json.dumps(self.data))

    def codes(self):
        self.save()
        return {x["code"] for x in validate_registry(self.root)}

    def claim(self):
        return self.data["claims"][0]

    def source(self):
        return self.data["sources"][0]

    def test_fixture_is_valid_and_indexed(self):
        self.assertEqual(validate_registry(self.root), [])
        self.assertIn("| K001 |", build_index(self.root))

    def test_sections_and_claim_types_are_trimmed(self):
        self.assertEqual(SECTIONS, ("sources", "claims", "documents"))
        self.assertEqual(CLAIM_TYPES, {"observation", "hypothesis", "interpretation", "derivation", "model_result"})
        self.claim()["type"] = "dated_legal_analysis"
        self.assertIn("claim_type", self.codes())

    def test_duplicates_missing_and_cycles(self):
        self.claim()["depends_on"] = ["UNKNOWN", "DOC-1"]
        self.data["claims"].append(copy.deepcopy(self.claim()))
        self.assertTrue({"duplicate_id", "missing_reference", "dependency_cycle"} <= self.codes())

    def test_missing_premise(self):
        self.claim()["evidence"] = []
        self.assertIn("missing_premise", self.codes())

    def test_observation_needs_observational_source(self):
        self.claim()["type"] = "observation"
        self.assertIn("observation_from_nonobservation", self.codes())
        self.source()["kind"] = "transcript"
        self.assertNotIn("observation_from_nonobservation", self.codes())

    def test_model_result_needs_model_trial(self):
        self.claim()["type"] = "model_result"
        self.assertIn("model_result_from_nontrial", self.codes())
        self.source()["kind"] = "model_trial"
        self.assertNotIn("model_result_from_nontrial", self.codes())

    def test_snapshot_mutation_and_escape(self):
        (self.root / self.source()["snapshot"]).write_text("changed")
        self.assertIn("snapshot_hash", self.codes())
        self.source()["snapshot"] = "../outside"
        self.assertIn("snapshot_read", self.codes())

    def test_evidence_must_select_preserved_excerpt(self):
        self.claim()["evidence"][0]["anchor"] = "L1-L2"
        self.assertIn("evidence_anchor", self.codes())

    def test_version_review_and_history(self):
        n = self.claim()
        n["version"] = 0
        n["review_status"] = "reviewed"
        self.assertTrue({"claim_version", "review_history"} <= self.codes())
        n["version"], n["review_status"] = 1, "unreviewed"
        n["status"] = "refuted"
        self.assertIn("status_history", self.codes())

    def test_malformed_shape_is_error_not_crash(self):
        self.claim()["evidence"] = ["invalid"]
        self.assertIn("shape", self.codes())

    def test_versions_coexist_and_context_carries_excerpts(self):
        new = copy.deepcopy(self.source())
        new.update(id="S001-v2", version="2026-09-17-v2", snapshot="knowledge/snapshots/new.txt", sha256=hashlib.sha256(b"new\n").hexdigest(), anchor="L1-L1")
        (self.root / new["snapshot"]).write_text("new\n")
        self.data["sources"].append(new)
        self.assertEqual(self.codes(), set())
        pack = context(self.root, ["K001", "S001-v2"])
        ids = [r["id"] for r in pack["records"]]
        self.assertEqual(ids, ["K001", "S001", "S001-v2"])
        self.assertEqual(pack["records"][1]["excerpt"], EXCERPT)
        self.assertEqual({(x["id"], x["reason"]) for x in pack["selection_log"]}, {("K001", "requested"), ("S001", "dependency"), ("S001-v2", "requested")})
        with self.assertRaises(ValueError):
            context(self.root, ["NOPE"])

    def test_multihop_impact(self):
        result = impact(self.root, ["S001"])
        self.assertEqual(result["affected"]["claims"], ["K001"])
        self.assertEqual(result["affected"]["documents"], ["DOC-1"])
        self.assertEqual(result["review_proposals"][0]["action"], "review_no_automatic_status_change")
        self.assertEqual(json.loads(self.path.read_text()), self.data)

    def test_snapshot_helper(self):
        (self.root / "paper.txt").write_text("a\nb\n")
        info = snapshot(self.root, self.root / "paper.txt")
        expected = hashlib.sha256(b"a\nb\n").hexdigest()
        self.assertEqual(info["sha256"], expected)
        self.assertEqual(info["snapshot"], f"knowledge/snapshots/{expected}.txt")
        self.assertEqual(info["anchor"], "L1-L2")
        self.assertTrue((self.root / info["snapshot"]).exists())
        self.assertEqual(info["source_skeleton"]["sha256"], expected)
        self.assertEqual(snapshot(self.root, self.root / "paper.txt")["sha256"], expected)


if __name__ == "__main__":
    unittest.main()
