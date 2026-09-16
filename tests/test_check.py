import subprocess
import tempfile
import unittest
from pathlib import Path

from harness.check import check, check_staged

ROOT = Path(__file__).resolve().parents[1]


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)


class CheckTests(unittest.TestCase):
    def test_shipped_repo_passes(self):
        self.assertEqual(check(ROOT), [])

    def test_static_checks_catch_drift(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        for rel in ("harness/__init__.py", "CHANGELOG.md", "CITATION.cff", "method/README.md", "README.md", "investigations/README.md", ".agents/skills/x/SKILL.md"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / "harness/__init__.py").write_text('__version__ = "0.2.0"\n')
        (root / "CHANGELOG.md").write_text("# Changelog\n\n## [0.1.0] - 2026-09-16\n")
        (root / "CITATION.cff").write_text("version: 0.1.0\n")
        (root / "method/README.md").write_text("## Ground rules\n\n1. **One.** A rule with an em-dash \u2014 here.\n\n## Close-out check\n")
        (root / "README.md").write_text("[missing](nowhere.md)\n")
        (root / "investigations/README.md").write_text("| ID |\n")
        (root / "investigations/002-orphan").mkdir()
        (root / ".agents/skills/x/SKILL.md").write_text("no frontmatter\n")
        codes = {e["code"] for e in check(root)}
        self.assertEqual(codes, {"version_mismatch", "changelog_unreleased", "ground_rules", "em_dash", "broken_link", "investigation_index", "skill_frontmatter"})

    def test_staged_checks(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "t@example.com")
        git(root, "config", "user.name", "t")
        (root / "method").mkdir()
        (root / "method/README.md").write_text("rules\n")
        (root / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n")
        (root / "s/frozen").mkdir(parents=True)
        (root / "s/frozen/manifest.json").write_text("{}\n")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "base")
        (root / "method/README.md").write_text("rules changed\n")
        git(root, "add", "method/README.md")
        self.assertEqual({e["code"] for e in check_staged(root)}, {"changelog_not_staged"})
        (root / "CHANGELOG.md").write_text("# Changelog\n\n## [Unreleased]\n\n- rule changed\n")
        git(root, "add", "CHANGELOG.md")
        self.assertEqual(check_staged(root), [])
        (root / "s/frozen/manifest.json").write_text("{\"x\": 1}\n")
        git(root, "add", "s/frozen/manifest.json")
        self.assertEqual({e["code"] for e in check_staged(root)}, {"frozen_modified"})
        (root / "t/frozen").mkdir(parents=True)
        (root / "t/frozen/manifest.json").write_text("{}\n")
        git(root, "add", "t/frozen/manifest.json")
        self.assertNotIn("t/frozen", " ".join(e["message"] for e in check_staged(root)))


if __name__ == "__main__":
    unittest.main()
