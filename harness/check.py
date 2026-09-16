"""Checks on the repo itself: versions, changelog, rules, links, frozen directories."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

RULE_CARRIERS = ("method/", ".agents/", "harness/study.py", "harness/registry.py", "AGENTS.md")
TEXT_SUFFIXES = {".md", ".py", ".json", ".cff", ".yml", ".yaml"}
SKIP_DIRS = {".git", "docs", "runs", "__pycache__"}
EM_DASH = "\u2014"


def _fail(errors, code, message):
    errors.append({"code": code, "message": message})


def _read(root, rel):
    path = Path(root) / rel
    return path.read_text(encoding="utf-8") if path.exists() else ""


def check(root):
    """Static checks that hold at every commit. Returns a list of {code, message}."""
    root = Path(root)
    errors = []
    version = re.search(r'__version__\s*=\s*"([^"]+)"', _read(root, "harness/__init__.py"))
    changelog = _read(root, "CHANGELOG.md")
    released = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)
    cff = re.search(r"^version:\s*(\S+)", _read(root, "CITATION.cff"), re.M)
    versions = {"harness/__init__.py": version.group(1) if version else None, "CHANGELOG.md": released[0] if released else None, "CITATION.cff": cff.group(1) if cff else None}
    if len(set(versions.values())) != 1:
        _fail(errors, "version_mismatch", f"versions differ: {versions}")
    if "## [Unreleased]" not in changelog:
        _fail(errors, "changelog_unreleased", "CHANGELOG.md has no [Unreleased] section")
    method = _read(root, "method/README.md")
    rules_section = method.split("## Ground rules", 1)[-1].split("## Close-out check", 1)[0]
    rules = re.findall(r"^\d+\. \*\*", rules_section, re.M)
    if len(rules) != 10:
        _fail(errors, "ground_rules", f"method/README.md has {len(rules)} ground rules, expected 10")
    for path in sorted(root.rglob("*")):
        if path.suffix not in TEXT_SUFFIXES or not path.is_file() or SKIP_DIRS & set(path.relative_to(root).parts):
            continue
        if EM_DASH in path.read_text(encoding="utf-8", errors="ignore"):
            _fail(errors, "em_dash", str(path.relative_to(root)))
    readme = _read(root, "README.md")
    for link in re.findall(r"\]\(([^)#][^)]*)\)", readme):
        if link.startswith(("http://", "https://")):
            continue
        if not (root / link.split("#", 1)[0]).exists():
            _fail(errors, "broken_link", f"README.md -> {link}")
    index = _read(root, "investigations/README.md")
    inv = root / "investigations"
    if inv.exists():
        for d in sorted(p for p in inv.iterdir() if p.is_dir()):
            if f"{d.name}/README.md" not in index:
                _fail(errors, "investigation_index", f"{d.name} is not listed in investigations/README.md")
    for skill in sorted(root.glob(".agents/skills/*/SKILL.md")):
        head = skill.read_text(encoding="utf-8").split("---")
        front = head[1] if len(head) > 2 and head[0].strip() == "" else ""
        if not re.search(r"^name:\s*\S", front, re.M) or not re.search(r"^description:\s*\S", front, re.M):
            _fail(errors, "skill_frontmatter", str(skill.relative_to(root)))
    return errors


def _staged(root, diff_filter=None):
    args = ["git", "diff", "--cached", "--name-only"] + ([f"--diff-filter={diff_filter}"] if diff_filter else [])
    out = subprocess.run(args, cwd=root, capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def check_staged(root):
    """Checks on what is about to be committed. Returns a list of {code, message}."""
    errors = []
    staged = _staged(root)
    if staged is None:
        return [{"code": "git", "message": "not a git repository or git not available"}]
    changed = _staged(root, "MD") or []
    frozen = [f for f in changed if "/frozen/" in f or f.startswith("frozen/")]
    if frozen:
        _fail(errors, "frozen_modified", "frozen files changed or deleted: " + ", ".join(frozen))
    carriers = [f for f in staged if f.startswith(RULE_CARRIERS) or f in RULE_CARRIERS]
    if carriers and "CHANGELOG.md" not in staged:
        _fail(errors, "changelog_not_staged", "rule, template or harness change without a CHANGELOG.md line: " + ", ".join(carriers))
    return errors
