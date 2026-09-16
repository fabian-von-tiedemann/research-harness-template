import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from harness.__main__ import main

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "investigations/001-example/study-01"


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "frozen"

    def test_shipped_register_validates_and_indexes(self):
        code, out, _ = run(["validate"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["valid"])
        code, out, _ = run(["index"])
        self.assertEqual(code, 0)
        self.assertIn("| K001 |", out)

    def test_context_and_impact(self):
        code, out, _ = run(["context", "K001"])
        self.assertEqual(code, 0)
        self.assertEqual({r["id"] for r in json.loads(out)["records"]}, {"K001", "S001"})
        code, out, _ = run(["impact", "S001"])
        self.assertEqual(code, 0)
        self.assertIn("K001", json.loads(out)["affected"]["claims"])
        code, _, err = run(["impact", "NOPE"])
        self.assertEqual(code, 2)
        self.assertIn("Unknown", err)

    def test_snapshot(self):
        f = Path(self.temp.name) / "x.txt"
        f.write_text("hello\n")
        code, out, _ = run(["snapshot", str(f)])
        self.assertEqual(code, 0)
        info = json.loads(out)
        self.assertEqual(info["anchor"], "L1-L1")
        (ROOT / info["snapshot"]).unlink()

    def test_create_evaluate_report(self):
        code, out, _ = run(["create", str(STUDY / "protocol.json"), "--out", str(self.out)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["status"], "frozen")
        code, _, err = run(["evaluate", str(self.out)])
        self.assertEqual(code, 2)
        self.assertIn("result.json", err)
        shutil.copyfile(STUDY / "frozen/result.json", self.out / "result.json")
        code, out, _ = run(["evaluate", str(self.out), "--write"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["outcome"], "supports_hypothesis")
        self.assertTrue((self.out / "evaluation.json").exists())
        code, out, _ = run(["report", str(self.out), "--write"])
        self.assertEqual(code, 0)
        self.assertIn("# Pre-registered study I001-01", out)
        self.assertTrue((self.out / "report.md").exists())

    def test_shipped_frozen_study_is_intact(self):
        code, out, _ = run(["evaluate", str(STUDY / "frozen")])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["outcome"], "supports_hypothesis")

    def test_demo(self):
        code, out, _ = run(["demo", "--out", str(self.out)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["outcome"], "supports_hypothesis")
        self.assertTrue((self.out / "evaluation.json").exists())
        code, _, _ = run(["demo", "--out", str(self.out)])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
