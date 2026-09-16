import tempfile
import unittest
from pathlib import Path

from harness.common import ContractError, atomic_json, confined, digest, read_json


class CommonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_atomic_json_roundtrip_and_digest(self):
        path = self.root / "a" / "b.json"
        atomic_json(path, {"x": 1, "text": "åäö"})
        self.assertEqual(read_json(path), {"x": 1, "text": "åäö"})
        self.assertEqual(len(digest(path)), 64)

    def test_read_json_missing_is_contract_error(self):
        with self.assertRaises(ContractError):
            read_json(self.root / "missing.json")

    def test_confined_rejects_escape_and_missing(self):
        (self.root / "inside.txt").write_text("ok")
        self.assertEqual(confined(self.root, "inside.txt"), (self.root / "inside.txt").resolve())
        with self.assertRaises(ContractError):
            confined(self.root, "../outside.txt")
        with self.assertRaises(ContractError):
            confined(self.root, "missing.txt")


if __name__ == "__main__":
    unittest.main()
