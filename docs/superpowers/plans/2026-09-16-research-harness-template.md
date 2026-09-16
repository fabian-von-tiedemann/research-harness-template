# research-harness-template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish `research-harness-template`, a public GitHub template repo giving a researcher a field-neutral harness: pre-registered studies frozen and committed before data, a hashed knowledge register, a decision log, agent rules, and a feedback loop back to the template. Version 0.1.0.

**Architecture:** Two Python modules under `harness/` (a trimmed knowledge-register validator from the model repo, and a new study engine that freezes a protocol and evaluates a result separately) behind one CLI. Everything else is Markdown. Standard library only.

**Tech Stack:** Python 3.10+ standard library, `unittest`, Git, `gh`. Agents read `AGENTS.md`; Claude Code reads `CLAUDE.md` which imports it; skills in `.agents/skills/`.

**Spec:** `docs/superpowers/specs/2026-09-16-research-harness-template-design.md`

**Repo root for all tasks:** `/Users/fabianvontiedemann/Developer/research-harness-template` (git initialised, branch `main`). Run every command from there.

## Global Constraints

- English everywhere except `docs/message-to-amanda.md`.
- Python 3.10 or later, standard library only. No `requirements.txt`, no `pyproject.toml`.
- Exit codes: 0 success, 2 invalid input or contract, 3 interrupted.
- MIT for code, CC BY 4.0 for text.
- No em-dashes in prose.
- No real personal data. Example data is simulated and labelled `data_kind: simulated`.
- Vocabulary: investigation, study, rival (competing hypothesis), knowledge register, `simulated | primary | secondary`.
- `python3 -m unittest discover -s tests -v` passes at the end of every task.
- Every rule or format change lands in `CHANGELOG.md` `[Unreleased]` in the same commit.
- Commit after every task with trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

### Task 1: Scaffold, licences, changelog, citation, common helpers

**Files:**
- Create: `.gitignore`, `LICENSE`, `LICENSE-CONTENT`, `CHANGELOG.md`, `CITATION.cff`, `harness/__init__.py`, `harness/common.py`, `tests/__init__.py`, `tests/test_common.py`

**Interfaces:**
- Produces: `harness.common.ContractError(ValueError)`, `read_json(path)`, `digest(path) -> str`, `atomic_json(path, data)`, `confined(base, relative) -> Path`.

- [ ] **Step 1: `.gitignore`**

```
__pycache__/
*.py[cod]
.context/
runs/local/
```

- [ ] **Step 2: `LICENSE`** (MIT, copyright 2026 Fabian von Tiedemann, standard text).

- [ ] **Step 3: `LICENSE-CONTENT`**

```
Creative Commons Attribution 4.0 International (CC BY 4.0)

The text content of this repository (everything outside harness/, tests/ and
scripts, including method/, investigations/, knowledge/, AGENTS.md and
README.md) is licensed under CC BY 4.0.

You are free to share and adapt the material for any purpose, including
commercially, as long as you give appropriate credit, link to the licence and
indicate if changes were made.

Full licence text: https://creativecommons.org/licenses/by/4.0/legalcode

Attribution: "research-harness-template" by Fabian von Tiedemann,
https://github.com/fabian-von-tiedemann/research-harness-template
```

- [ ] **Step 4: `CHANGELOG.md`**

```markdown
# Changelog

All notable changes to this template are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). A rule, template or protocol-format change is a change to the template and belongs here as well as in `DECISIONS.md`.

## [Unreleased]
```

- [ ] **Step 5: `CITATION.cff`**

```yaml
cff-version: 1.2.0
message: "If you use this template, please cite it."
title: "research-harness-template"
type: software
authors:
  - family-names: "von Tiedemann"
    given-names: "Fabian"
version: 0.1.0
date-released: 2026-09-16
repository-code: "https://github.com/fabian-von-tiedemann/research-harness-template"
license: MIT
abstract: "A field-neutral research harness for agent-assisted, pre-registered work: frozen study protocols, a hashed knowledge register, a decision log and agent rules."
```

- [ ] **Step 6: `harness/__init__.py`**

```python
"""Local research instrument. No external calls on import."""

__version__ = "0.1.0"
```

- [ ] **Step 7: failing tests `tests/__init__.py` (empty) and `tests/test_common.py`**

```python
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
```

- [ ] **Step 8: run, expect `ModuleNotFoundError`**: `python3 -m unittest tests.test_common -v`

- [ ] **Step 9: `harness/common.py`**

```python
"""Shared file contracts. Standard library only."""

import hashlib
import json
import os
import tempfile
from pathlib import Path


class ContractError(ValueError):
    pass


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ContractError(f"Cannot read JSON {path}: {exc}") from exc


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".write-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def confined(base, relative):
    path = (Path(base) / relative).resolve()
    if not path.is_relative_to(Path(base).resolve()) or not path.is_file():
        raise ContractError(f"Disallowed or missing file: {relative}")
    return path
```

- [ ] **Step 10: run, expect 3 OK, commit** `Scaffold: licences, changelog, citation, common helpers`

---

### Task 2: Knowledge register, trimmed

**Files:**
- Create: `harness/registry.py`, `knowledge/registry.json` (empty valid), `tests/test_registry.py`

**Interfaces:**
- Produces: `SECTIONS`, `CLAIM_TYPES`, `STATUSES`, `REVIEW_STATUSES`, `RAW_SOURCE_KINDS`; `validate_registry(root) -> list[dict]`; `build_index(root) -> str`; `context(root, ids) -> dict` with `records`, `selection_log`; `impact(root, changed_ids) -> dict` with `changed`, `affected`, `review_proposals`; `snapshot(root, file) -> dict` with `sha256`, `snapshot`, `anchor`, `source_skeleton`.

- [ ] **Step 1: empty valid `knowledge/registry.json`**

```json
{
  "schema_version": 1,
  "sources": [],
  "claims": [],
  "documents": []
}
```

- [ ] **Step 2: failing tests `tests/test_registry.py`** (fixture built in `setUp`, independent of the shipped register)

```python
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
```

- [ ] **Step 3: run, expect `ModuleNotFoundError`**

- [ ] **Step 4: `harness/registry.py`**

```python
"""Versioned knowledge register. Validates declarations, never their truth."""
from __future__ import annotations
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path

SECTIONS = ('sources', 'claims', 'documents')
CLAIM_TYPES = {'observation', 'hypothesis', 'interpretation', 'derivation', 'model_result'}
STATUSES = {'open', 'provisional', 'bounded_support', 'weakened', 'refuted', 'superseded'}
REVIEW_STATUSES = {'unreviewed', 'reviewed', 'needs_review'}
SOURCE_KINDS = ('literature', 'transcript', 'empirical_report', 'dataset', 'model_trial', 'analysis', 'note')
RAW_SOURCE_KINDS = ('transcript', 'empirical_report', 'dataset')

def _load(root):
    return json.loads((Path(root) / 'knowledge/registry.json').read_text(encoding='utf-8'))

def _nodes(data):
    return {n['id']: n for section in SECTIONS for n in data.get(section, [])}

def _dependencies(node):
    return list(dict.fromkeys(node.get('depends_on', []) + [e['source'] for e in node.get('evidence', [])]))

def _safe_path(root, path):
    if not isinstance(path, str) or Path(path).is_absolute():
        raise ValueError('Expected relative path')
    result = (Path(root) / path).resolve()
    if not result.is_relative_to(Path(root).resolve()):
        raise ValueError('Path escapes repository')
    return result

def _dated_history(entries, allowed, current):
    if not isinstance(entries, list) or not entries or any(not isinstance(h, dict) or h.get('status') not in allowed or not h.get('reason') for h in entries):
        return False
    try:
        dates = [date.fromisoformat(h['date']) for h in entries]
    except (KeyError, TypeError, ValueError):
        return False
    return dates == sorted(dates) and entries[-1]['status'] == current

def validate_registry(root):
    errors = []
    def fail(code, message):
        errors.append({'code': code, 'message': message})
    try:
        data = _load(root)
    except (OSError, ValueError) as exc:
        return [{'code': 'registry_read', 'message': str(exc)}]
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        return [{'code': 'schema_version', 'message': 'Expected registry schema_version 1'}]
    nodes, sections = {}, {}
    for section in SECTIONS:
        if not isinstance(data.get(section), list):
            fail('shape', f'{section}: expected list')
            continue
        for n in data[section]:
            if not isinstance(n, dict) or not isinstance(n.get('id'), str) or not n['id']:
                fail('shape', f'{section}: missing string id')
                continue
            ident = n['id']
            if ident in nodes:
                fail('duplicate_id', ident)
            nodes[ident], sections[ident] = n, section
            if not isinstance(n.get('depends_on', []), list) or any(not isinstance(x, str) for x in n.get('depends_on', [])):
                fail('shape', f'{ident}: depends_on must be strings')
            if not isinstance(n.get('evidence', []), list) or any(not isinstance(e, dict) or not isinstance(e.get('source'), str) for e in n.get('evidence', [])):
                fail('shape', f'{ident}: evidence must contain source IDs')
    if any(e['code'] == 'shape' for e in errors):
        return errors
    for ident, n in nodes.items():
        for dep in _dependencies(n):
            if dep not in nodes:
                fail('missing_reference', f'{ident} -> {dep}')
        if sections[ident] == 'sources':
            if any(sections.get(d) != 'sources' for d in _dependencies(n)):
                fail('source_dependency', ident)
            for key in ('family', 'version', 'snapshot', 'sha256', 'origin', 'anchor', 'access', 'kind'):
                if not isinstance(n.get(key), str) or not n[key]:
                    fail('source_metadata', f'{ident}: {key}')
            if n.get('kind') not in SOURCE_KINDS:
                fail('source_kind', ident)
            try:
                content = _safe_path(root, n.get('snapshot')).read_bytes()
                if hashlib.sha256(content).hexdigest() != n.get('sha256'):
                    fail('snapshot_hash', ident)
                anchor = n.get('anchor')
                if not isinstance(anchor, str) or not anchor.startswith('L'):
                    fail('source_anchor', ident)
                else:
                    parts = anchor[1:].split('-L')
                    start, end = int(parts[0]), int(parts[-1])
                    if not 1 <= start <= end <= len(content.decode('utf-8').splitlines()):
                        fail('source_anchor', ident)
            except (OSError, ValueError, TypeError, UnicodeError):
                fail('snapshot_read', ident)
        if sections[ident] == 'claims':
            if n.get('type') not in CLAIM_TYPES:
                fail('claim_type', ident)
            if n.get('status') not in STATUSES:
                fail('claim_status', ident)
            if not isinstance(n.get('version'), int) or isinstance(n.get('version'), bool) or n['version'] < 1:
                fail('claim_version', ident)
            if n.get('review_status') not in REVIEW_STATUSES:
                fail('review_status', ident)
            if not _dated_history(n.get('review_history'), REVIEW_STATUSES, n.get('review_status')):
                fail('review_history', ident)
            if not _dated_history(n.get('history'), STATUSES, n.get('status')):
                fail('status_history', ident)
            if any(not isinstance(n.get(k), str) or not n[k] for k in ('statement', 'scope', 'reconsider_if')):
                fail('claim_metadata', ident)
            if not _dependencies(n):
                fail('missing_premise', ident)
            for e in n.get('evidence', []):
                source = nodes.get(e['source'], {})
                if sections.get(e['source']) != 'sources':
                    fail('evidence_source', f'{ident}: {e["source"]}')
                if e.get('relation') not in ('supports', 'opposes', 'limits', 'origin'):
                    fail('evidence_relation', ident)
                if not e.get('anchor') or not e.get('reading'):
                    fail('evidence_anchor', ident)
                if e.get('anchor') != source.get('anchor'):
                    fail('evidence_anchor', f'{ident}: evidence must select the preserved source excerpt')
                if n.get('type') == 'observation' and e.get('relation') == 'supports' and source.get('kind') not in ('transcript', 'empirical_report'):
                    fail('observation_from_nonobservation', ident)
                if n.get('type') == 'model_result' and e.get('relation') == 'supports' and source.get('kind') != 'model_trial':
                    fail('model_result_from_nontrial', ident)
        if sections[ident] == 'documents':
            if not isinstance(n.get('path'), str) or not n['path']:
                fail('document_path', ident)
    colors = {}
    def visit(ident):
        if colors.get(ident) == 1:
            fail('dependency_cycle', ident)
            return
        if colors.get(ident) == 2:
            return
        colors[ident] = 1
        for dep in _dependencies(nodes[ident]):
            if dep in nodes:
                visit(dep)
        colors[ident] = 2
    for ident in nodes:
        visit(ident)
    versions, paths = set(), {}
    for n in data.get('sources', []):
        pair = (n.get('origin'), n.get('version'))
        if pair in versions:
            fail('duplicate_source_version', n['id'])
        versions.add(pair)
        path = n.get('snapshot')
        if path in paths and paths[path] != n.get('sha256'):
            fail('snapshot_reused', n['id'])
        paths[path] = n.get('sha256')
    return errors

def _valid(root):
    errors = validate_registry(root)
    if errors:
        raise ValueError(json.dumps(errors, ensure_ascii=False))
    return _load(root)

def context(root, ids):
    """Records for the given IDs and everything they rest on, with source excerpts inlined."""
    data = _valid(root)
    nodes = _nodes(data)
    selected = set()
    def select(ident):
        if ident not in nodes:
            raise ValueError(f'Unknown ID: {ident}')
        if ident in selected:
            return
        selected.add(ident)
        for dep in _dependencies(nodes[ident]):
            select(dep)
    for ident in ids:
        select(ident)
    source_ids = {n['id'] for n in data['sources']}
    records, log = [], []
    for ident in sorted(selected):
        n = dict(nodes[ident])
        if ident in source_ids:
            n['excerpt'] = _safe_path(root, n['snapshot']).read_text(encoding='utf-8')
        records.append(n)
        log.append({'id': ident, 'action': 'included', 'reason': 'requested' if ident in ids else 'dependency'})
    return {'schema_version': 1, 'records': records, 'selection_log': log}

def impact(root, changed_ids):
    """Everything that rests on the changed IDs, at any depth, as review proposals."""
    data = _valid(root)
    nodes = _nodes(data)
    unknown = set(changed_ids) - nodes.keys()
    if unknown:
        raise ValueError(f'Unknown IDs: {sorted(unknown)}')
    affected = set(changed_ids)
    reasons = {ident: 'changed' for ident in affected}
    while True:
        added = {ident for ident, n in nodes.items() if ident not in affected and set(_dependencies(n)) & affected}
        if not added:
            break
        for ident in added:
            reasons[ident] = 'depends_on:' + ','.join(sorted(set(_dependencies(nodes[ident])) & affected))
        affected |= added
    return {'schema_version': 1, 'changed': sorted(changed_ids), 'affected': {section: [n['id'] for n in data[section] if n['id'] in affected] for section in SECTIONS}, 'review_proposals': [{'id': i, 'reason': reasons[i], 'action': 'review_no_automatic_status_change'} for i in sorted(affected)]}

def snapshot(root, file):
    """Copy a file into knowledge/snapshots/<sha256>.txt and return what a source entry needs."""
    file = Path(file)
    content = file.read_bytes()
    sha = hashlib.sha256(content).hexdigest()
    rel = f'knowledge/snapshots/{sha}.txt'
    target = Path(root) / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copyfile(file, target)
    lines = len(content.decode('utf-8').splitlines())
    anchor = f'L1-L{max(lines, 1)}'
    skeleton = {'id': 'S<NNN>', 'family': 'S<NNN>', 'version': f'{date.today().isoformat()}-v1', 'snapshot': rel, 'sha256': sha, 'origin': str(file), 'anchor': anchor, 'kind': '<one of ' + ' | '.join(SOURCE_KINDS) + '>', 'access': '<how you obtained it and whether it may be quoted>', 'depends_on': []}
    return {'sha256': sha, 'snapshot': rel, 'anchor': anchor, 'lines': lines, 'source_skeleton': skeleton}

def build_index(root):
    data = _valid(root)
    rows = ['# Knowledge index', '', 'Generated from `registry.json` by `python3 -m harness index`. Status is a declaration of how much the evidence carries; review status says whether anyone other than the author has checked. Neither is set automatically.', '', '| ID | Version | Type | Status | Review | Statement |', '|---|---|---|---|---|---|']
    for n in data['claims']:
        rows.append(f'| {n["id"]} | {n["version"]} | {n["type"]} | {n["status"]} | {n["review_status"]} | {n["statement"].replace("|", " / ")} |')
    rows.extend(['', '## Sources', ''])
    for family in sorted({n['family'] for n in data['sources']}):
        rows.append(f'- {family}: ' + ', '.join(f'{n["id"]} ({n["kind"]}, {n["version"]})' for n in data['sources'] if n['family'] == family))
    rows.extend(['', '## Documents', ''])
    for n in data['documents']:
        rows.append(f'- {n["id"]}: `{n["path"]}` depends on ' + ', '.join(n.get('depends_on', [])))
    return '\n'.join(rows) + '\n'
```

- [ ] **Step 5: run, expect 13 OK. Commit** `Knowledge register: validator, context, impact, snapshot, index`

---

### Task 3: Study engine

**Files:**
- Create: `harness/study.py`, `tests/test_study.py`

**Interfaces:**
- Produces: `OPS`, `DATA_KINDS = ('simulated', 'primary', 'secondary')`, `RESERVED = ('protocol.json', 'manifest.json', 'result.json', 'evaluation.json', 'report.md')`, `validate_protocol(p)`, `apply_rule(rule, value) -> str`, `create(protocol_path, out_dir, root=None) -> dict`, `evaluate(run_dir) -> dict`, `report(run_dir) -> str`.

- [ ] **Step 1: failing tests `tests/test_study.py`**

```python
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
```

- [ ] **Step 2: run, expect `ModuleNotFoundError`**

- [ ] **Step 3: `harness/study.py`**

```python
"""Pre-registered studies: a frozen protocol, a result, a separate evaluation. No model calls."""

from __future__ import annotations

import math
import operator
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .common import ContractError, atomic_json, confined, digest, read_json

OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt, "==": operator.eq}
DATA_KINDS = ("simulated", "primary", "secondary")
RESERVED = ("protocol.json", "manifest.json", "result.json", "evaluation.json", "report.md")
REQUIRED = ("schema_version", "id", "investigation", "question", "hypothesis", "rival", "measures", "interpretation_rule", "affects", "inputs", "data_kind", "limitations")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _condition(cond, name):
    if not isinstance(cond, dict) or cond.get("op") not in OPS:
        raise ContractError(f"{name}: op must be one of {sorted(OPS)}")
    value = cond.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ContractError(f"{name}: value must be a finite number")


def _bounds(cond):
    op, v = cond["op"], cond["value"]
    if op == ">=":
        return (v, True, math.inf, False)
    if op == ">":
        return (v, False, math.inf, False)
    if op == "<=":
        return (-math.inf, False, v, True)
    if op == "<":
        return (-math.inf, False, v, False)
    return (v, True, v, True)


def _overlap(a, b):
    """True if some value satisfies both conditions."""
    if a[0] > b[0]:
        lo, lo_in = a[0], a[1]
    elif b[0] > a[0]:
        lo, lo_in = b[0], b[1]
    else:
        lo, lo_in = a[0], a[1] and b[1]
    if a[2] < b[2]:
        hi, hi_in = a[2], a[3]
    elif b[2] < a[2]:
        hi, hi_in = b[2], b[3]
    else:
        hi, hi_in = a[2], a[3] and b[3]
    if lo < hi:
        return True
    return lo == hi and lo_in and hi_in


def _validate_rule(rule, measure_ids):
    if not isinstance(rule, dict) or rule.get("measure") not in measure_ids:
        raise ContractError("interpretation_rule.measure must name a declared measure")
    _condition(rule.get("supports_hypothesis_if"), "supports_hypothesis_if")
    _condition(rule.get("supports_rival_if"), "supports_rival_if")
    if _overlap(_bounds(rule["supports_hypothesis_if"]), _bounds(rule["supports_rival_if"])):
        raise ContractError("supports_hypothesis_if and supports_rival_if overlap; a value could satisfy both")


def validate_protocol(p):
    if not isinstance(p, dict):
        raise ContractError("Protocol must be an object")
    missing = [k for k in REQUIRED if k not in p]
    if missing:
        raise ContractError(f"Protocol missing fields: {missing}")
    if p["schema_version"] != 1:
        raise ContractError("Protocol schema_version must be 1")
    for key in ("id", "investigation", "question", "hypothesis", "rival", "limitations"):
        if not isinstance(p[key], str) or not p[key].strip():
            raise ContractError(f"Protocol field {key} must be a non-empty string")
    if p["data_kind"] not in DATA_KINDS:
        raise ContractError(f"data_kind must be one of {DATA_KINDS}")
    measures = p["measures"]
    if not isinstance(measures, list) or not measures:
        raise ContractError("measures must be a non-empty list")
    ids = []
    for m in measures:
        if not isinstance(m, dict) or not isinstance(m.get("id"), str) or not m["id"] or not isinstance(m.get("description"), str) or not m["description"]:
            raise ContractError("Each measure needs string id and description")
        ids.append(m["id"])
    if len(set(ids)) != len(ids):
        raise ContractError("Measure ids must be unique")
    exploratory = p.get("exploratory", False)
    if not isinstance(exploratory, bool):
        raise ContractError("exploratory must be true or false")
    if exploratory:
        if p["interpretation_rule"] is not None:
            raise ContractError("An exploratory study has no interpretation_rule; set it to null")
    else:
        if p["interpretation_rule"] is None:
            raise ContractError("A confirmatory study needs an interpretation_rule; set exploratory to true if there is none")
        _validate_rule(p["interpretation_rule"], ids)
    for key in ("affects", "inputs"):
        if not isinstance(p[key], list) or any(not isinstance(x, str) or not x for x in p[key]):
            raise ContractError(f"{key} must be a list of strings")
    for rel in p["inputs"]:
        if Path(rel).name in RESERVED or rel in RESERVED:
            raise ContractError(f"Input may not be named {Path(rel).name}; reserved for the frozen directory")


def apply_rule(rule, value):
    _condition(rule.get("supports_hypothesis_if"), "supports_hypothesis_if")
    _condition(rule.get("supports_rival_if"), "supports_rival_if")
    h, r = rule["supports_hypothesis_if"], rule["supports_rival_if"]
    if OPS[h["op"]](value, h["value"]):
        return "supports_hypothesis"
    if OPS[r["op"]](value, r["value"]):
        return "supports_rival"
    return "undecided"


def _register_ids(root):
    """IDs in the register, or None when the repo has no register."""
    path = Path(root) / "knowledge/registry.json"
    if not path.exists():
        return None
    data = read_json(path)
    return {n["id"] for section in ("sources", "claims", "documents") for n in data.get(section, []) if isinstance(n, dict) and "id" in n}


def create(protocol_path, out_dir, root=None):
    protocol_path, out_dir = Path(protocol_path), Path(out_dir)
    p = read_json(protocol_path)
    validate_protocol(p)
    known = _register_ids(root) if root is not None else None
    if known is not None:
        unknown = [x for x in p["affects"] if x not in known]
        if unknown:
            raise ContractError(f"affects names unknown register IDs: {unknown}")
    if out_dir.exists():
        raise ContractError(f"Frozen directory already exists: {out_dir}")
    base = protocol_path.parent
    inputs = [confined(base, rel) for rel in p["inputs"]]
    out_dir.mkdir(parents=True)
    shutil.copyfile(protocol_path, out_dir / "protocol.json")
    for rel, src in zip(p["inputs"], inputs):
        target = out_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, target)
    hashes = {"protocol.json": digest(out_dir / "protocol.json")}
    for rel in p["inputs"]:
        hashes[rel] = digest(out_dir / rel)
    manifest = {"schema_version": 1, "id": p["id"], "created_at": _now(), "status": "frozen", "hashes": hashes}
    atomic_json(out_dir / "manifest.json", manifest)
    return manifest


def _frozen(run_dir):
    manifest = read_json(run_dir / "manifest.json")
    if manifest.get("schema_version") != 1 or manifest.get("status") != "frozen" or not isinstance(manifest.get("hashes"), dict):
        raise ContractError("manifest.json is not a frozen study manifest")
    for rel, expected in manifest["hashes"].items():
        if digest(confined(run_dir, rel)) != expected:
            raise ContractError(f"Frozen file changed after freezing: {rel}")
    p = read_json(run_dir / "protocol.json")
    validate_protocol(p)
    return manifest, p


def evaluate(run_dir):
    run_dir = Path(run_dir)
    manifest, p = _frozen(run_dir)
    result = read_json(run_dir / "result.json")
    measures = result.get("measures") if isinstance(result, dict) else None
    if not isinstance(measures, dict):
        raise ContractError("result.json must contain an object 'measures'")
    for m in p["measures"]:
        value = measures.get(m["id"])
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ContractError(f"result.json missing numeric measure {m['id']}")
    rule = p["interpretation_rule"]
    outcome = "descriptive" if p.get("exploratory") else apply_rule(rule, measures[rule["measure"]])
    return {
        "schema_version": 1,
        "id": p["id"],
        "evaluated_at": _now(),
        "measures": {m["id"]: measures[m["id"]] for m in p["measures"]},
        "outcome": outcome,
        "rule": rule,
        "data_kind": p["data_kind"],
        "limitations": p["limitations"],
        "note": result.get("note", ""),
        "manifest_sha256": digest(run_dir / "manifest.json"),
        "result_sha256": digest(run_dir / "result.json"),
    }


def _first_commit(run_dir, name):
    try:
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H %cI", "--", name], cwd=run_dir, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    lines = [line for line in out.stdout.splitlines() if line.strip()]
    return lines[-1] if out.returncode == 0 and lines else None


def report(run_dir):
    """One page of Markdown a reviewer can read: the frozen plan, its hashes, and when it entered git."""
    run_dir = Path(run_dir)
    manifest, p = _frozen(run_dir)
    commit = _first_commit(run_dir, "manifest.json")
    rows = [f"# Pre-registered study {p['id']}", "", f"Investigation {p['investigation']}. Data kind: {p['data_kind']}. Frozen {manifest['created_at']}.", ""]
    rows += [f"**Committed:** {commit}" if commit else "**Committed:** not committed yet. The pre-registration record is the git commit that adds manifest.json; commit this directory.", ""]
    rows += ["## Question", "", p["question"], "", "## Hypothesis", "", p["hypothesis"], "", "## Competing hypothesis", "", p["rival"], "", "## Measures", ""]
    rows += [f"- `{m['id']}`: {m['description']}" + (f" ({m['unit']})" if m.get("unit") else "") for m in p["measures"]]
    rows += ["", "## Interpretation rule", ""]
    if p.get("exploratory"):
        rows += ["Exploratory study. No confirmatory rule was pre-registered; the outcome is descriptive."]
    else:
        r = p["interpretation_rule"]
        rows += [f"On `{r['measure']}`: supports the hypothesis if {r['supports_hypothesis_if']['op']} {r['supports_hypothesis_if']['value']}; supports the competing hypothesis if {r['supports_rival_if']['op']} {r['supports_rival_if']['value']}; otherwise undecided."]
    rows += ["", "## Limitations declared before data", "", p["limitations"], "", "## Frozen files (SHA-256)", ""]
    rows += [f"- `{rel}`: `{sha}`" for rel, sha in manifest["hashes"].items()]
    evaluation = run_dir / "evaluation.json"
    if evaluation.exists():
        e = read_json(evaluation)
        rows += ["", "## Evaluation", "", f"Outcome: **{e.get('outcome')}**. Evaluated {e.get('evaluated_at')}.", ""]
        rows += [f"- `{k}`: {v}" for k, v in e.get("measures", {}).items()]
        rows += ["", f"result.json SHA-256 `{e.get('result_sha256')}`."]
    return "\n".join(rows) + "\n"
```

- [ ] **Step 4: run, expect 11 OK. Commit** `Study engine: frozen protocol, disjoint thresholds, exploratory studies, report`

---

### Task 4: Example investigation, frozen and evaluated (before any claim exists)

**Files:**
- Create: `investigations/README.md`, `investigations/001-example/README.md`, `investigations/001-example/study-01/README.md`, `investigations/001-example/study-01/protocol.json`, `investigations/001-example/study-01/inputs/hits.csv`, `investigations/001-example/study-01/compute.py`, `investigations/001-example/study-01/frozen/` (generated: `protocol.json`, `inputs/hits.csv`, `manifest.json`, `result.json`, `evaluation.json`)

- [ ] **Step 1: `inputs/hits.csv`**, header plus 40 rows, LF, trailing newline:

```
search_id,hit_id,relevant
single,h01,1
single,h02,0
single,h03,1
single,h04,0
single,h05,0
single,h06,1
single,h07,0
single,h08,1
single,h09,0
single,h10,1
single,h11,0
single,h12,1
single,h13,0
single,h14,0
single,h15,1
single,h16,0
single,h17,1
single,h18,0
single,h19,1
single,h20,0
combined,h21,1
combined,h22,1
combined,h23,0
combined,h24,1
combined,h25,1
combined,h26,1
combined,h27,0
combined,h28,1
combined,h29,1
combined,h30,1
combined,h31,0
combined,h32,1
combined,h33,1
combined,h34,1
combined,h35,0
combined,h36,1
combined,h37,1
combined,h38,1
combined,h39,0
combined,h40,1
```

- [ ] **Step 2: `protocol.json`** (`affects` empty: K001 does not exist yet, honest chronology)

```json
{
  "schema_version": 1,
  "id": "I001-01",
  "investigation": "I001",
  "question": "Does a literature search with two search strings yield a higher share of relevant hits than a search with one?",
  "hypothesis": "The combined search has a share of relevant hits at least 0.15 higher than the single search.",
  "rival": "The combined search is no better: its share of relevant hits is equal to or lower than the single search.",
  "measures": [
    {"id": "m1", "description": "Share of relevant hits for the combined search minus share for the single search", "unit": "share"},
    {"id": "m_single", "description": "Share of relevant hits, single search", "unit": "share"},
    {"id": "m_combined", "description": "Share of relevant hits, combined search", "unit": "share"}
  ],
  "interpretation_rule": {
    "measure": "m1",
    "supports_hypothesis_if": {"op": ">=", "value": 0.15},
    "supports_rival_if": {"op": "<=", "value": 0.0}
  },
  "exploratory": false,
  "affects": [],
  "inputs": ["inputs/hits.csv"],
  "data_kind": "simulated",
  "limitations": "Simulated data written for this template. Forty hits, two searches, relevance judged by nobody. The study shows the form of a frozen protocol, not a finding about literature search."
}
```

- [ ] **Step 3: `compute.py`**

```python
"""Computes the measures for study I001-01 from a frozen directory and writes result.json there.

Usage: python3 investigations/001-example/study-01/compute.py <frozen-dir>
"""

import csv
import json
import sys
from pathlib import Path


def share(rows, search_id):
    hits = [r for r in rows if r["search_id"] == search_id]
    return sum(int(r["relevant"]) for r in hits) / len(hits)


def main(frozen):
    frozen = Path(frozen)
    with (frozen / "inputs/hits.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    single, combined = share(rows, "single"), share(rows, "combined")
    result = {
        "measures": {"m1": round(combined - single, 4), "m_single": round(single, 4), "m_combined": round(combined, 4)},
        "note": "Computed by compute.py from the frozen copy of inputs/hits.csv.",
    }
    (frozen / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
```

- [ ] **Step 4: freeze, compute, evaluate, into the committed `frozen/`**

```bash
S=investigations/001-example/study-01
python3 -c "from harness.study import create; create('$S/protocol.json', '$S/frozen', root='.')"
python3 $S/compute.py $S/frozen
python3 -c "from harness.study import evaluate; from harness.common import atomic_json; e=evaluate('$S/frozen'); atomic_json('$S/frozen/evaluation.json', e); print(e['outcome'])"
```

Expected: `result.json` has `m1: 0.3`, `m_single: 0.45`, `m_combined: 0.75`; prints `supports_hypothesis`.

- [ ] **Step 5: `study-01/README.md`**

```markdown
# I001-01: two search strings against one, on simulated data

Status 2026-09-16: evaluated. Outcome: supports_hypothesis. Data kind: simulated.

## What is tested

Whether the combined search has a share of relevant hits at least 0.15 higher than the single search. The competing hypothesis is that it is equal or lower. Anything between 0.0 and 0.15 is undecided. The thresholds were written into `protocol.json` and frozen before `result.json` existed. The git history of `frozen/` is the record.

## Protocol

`protocol.json`. One input, `inputs/hits.csv`, forty rows, two searches. Measure `m1` is the difference in share of relevant hits, combined minus single. `m_single` and `m_combined` are reported alongside so a reader can check the arithmetic.

## How it was run

```sh
python3 -m harness create investigations/001-example/study-01/protocol.json --out investigations/001-example/study-01/frozen
python3 investigations/001-example/study-01/compute.py investigations/001-example/study-01/frozen
python3 -m harness evaluate investigations/001-example/study-01/frozen --write
python3 -m harness report investigations/001-example/study-01/frozen --write
```

`create` copies the protocol and the input into `frozen/` with hashes. `compute.py` reads the frozen copy and writes `result.json` next to it. `evaluate` checks the hashes, applies the rule and writes `evaluation.json`. `report` writes the one-page summary a reviewer reads. All of `frozen/` is committed.

## Result

m_single 0.45, m_combined 0.75, m1 0.30. Outcome supports_hypothesis.

## Assessment

The outcome is exactly what the data was written to produce, so it says nothing about literature search. What it shows is the chain: a question, a competing hypothesis, a rule locked before data, a frozen input, a computed result, and an evaluation nobody can change without breaking a hash. Knowledge entry K001 records the derivation with `reconsider_if` pointing at the simulated data.

## Limitations

Simulated. Forty hits. Relevance judged by nobody. Not a finding.
```

- [ ] **Step 6: `001-example/README.md`**

```markdown
# I001: Does a second search string raise the share of relevant hits?

Status 2026-09-16: one study run on simulated data. This investigation exists to show the form. Replace it with your own.

## The question and why it is chosen

Every researcher searches literature, so the example needs no field knowledge. The question is small enough that one study answers it and large enough to need a competing hypothesis, a measure and a rule.

## The argument chain being tested

1. A second search string widens recall (assumed, not tested here).
2. Wider recall does not have to lower precision (the thing tested).
3. If the share of relevant hits rises by at least 0.15, the second string pays for the extra screening (a threshold chosen before data; the number is a convention for the example).

## What would make us change the conclusion

- Primary data replacing the simulated set, with relevance judged by two people.
- A difference below 0.15 on primary data: the chain breaks at link 3.
- A difference at or below 0.0: the competing hypothesis holds.

## Studies

| Study | What it tests | Status | Outcome |
|---|---|---|---|
| [I001-01](study-01/README.md) | Difference in share of relevant hits on simulated data | Evaluated 2026-09-16 | supports_hypothesis, m1 = 0.30 |

## Knowledge entries

- K001, `derivation`, `provisional`, `unreviewed`. Source S001 is the frozen input. See `knowledge/registry.json`.

## Synthesis after one study, 2026-09-16

The form holds end to end. The content is empty by design. A real investigation would now write a second study with primary data, register it as a new source version, and let `python3 -m harness impact S001` list what needs re-review.

## Declared interests

Funding: none. Roles (CRediT): conceptualisation, software, writing by the template author. Conflicts of interest: none. Simulated example.
```

- [ ] **Step 7: `investigations/README.md`**

```markdown
# Investigations

One directory per question, numbered, with a README following `method/templates.md`. Studies live in `study-NN/` inside the investigation: `protocol.json`, `inputs/`, and after freezing `frozen/`, which is committed and never edited.

| ID | Question | Status |
|---|---|---|
| [I001](001-example/README.md) | Does a second search string raise the share of relevant hits? | Example on simulated data. Replace it. |

Start a new one by following `.agents/skills/new-investigation/SKILL.md`.
```

- [ ] **Step 8: run tests (OK), commit** `Example investigation I001: protocol frozen, computed and evaluated on simulated data`

---

### Task 5: CLI, register entries for the example, index

**Files:**
- Create: `harness/__main__.py`, `tests/test_cli.py`
- Modify: `knowledge/registry.json`, `investigations/001-example/study-01/protocol.json` (`affects: ["K001"]` is NOT added; the frozen protocol must stay identical to what was committed. Leave `affects` empty and say so in the study README's Assessment: "affects is empty because K001 was created after freezing, which is the honest order").
- Create: `knowledge/snapshots/<sha>.txt` (via `snapshot`), `knowledge/INDEX.md`, `investigations/001-example/study-01/frozen/report.md`

**Interfaces:**
- Produces: `python3 -m harness {validate,index,context,impact,snapshot,create,evaluate,report,demo}`; `main(argv) -> int`; `ROOT`.

- [ ] **Step 1: failing tests `tests/test_cli.py`**

```python
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
```

- [ ] **Step 2: `harness/__main__.py`**

```python
"""CLI for the knowledge register and pre-registered studies."""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from .common import ContractError, atomic_json
from .registry import build_index, context, impact, snapshot, validate_registry
from .study import create, evaluate, report

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_STUDY = ROOT / "investigations/001-example/study-01"


def emit(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m harness", description="Research harness: knowledge register and pre-registered studies with separate evaluation.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Check knowledge chains and preserved source excerpts")
    sub.add_parser("index", help="Print a readable index of the register")
    p = sub.add_parser("context", help="Records for the given IDs and everything they rest on, excerpts inlined")
    p.add_argument("ids", nargs="+")
    p = sub.add_parser("impact", help="List everything that rests on the given IDs, as review proposals")
    p.add_argument("ids", nargs="+")
    p = sub.add_parser("snapshot", help="Copy a file into knowledge/snapshots/ and print a source entry skeleton")
    p.add_argument("file", type=Path)
    p = sub.add_parser("create", help="Freeze a study protocol and its inputs into a directory")
    p.add_argument("protocol", type=Path)
    p.add_argument("--out", required=True, type=Path)
    p = sub.add_parser("evaluate", help="Apply the frozen interpretation rule to result.json; no model calls")
    p.add_argument("folder", type=Path)
    p.add_argument("--write", action="store_true", help="Save evaluation.json in the frozen directory")
    p = sub.add_parser("report", help="Print a one-page pre-registration report for a frozen directory")
    p.add_argument("folder", type=Path)
    p.add_argument("--write", action="store_true", help="Save report.md in the frozen directory")
    p = sub.add_parser("demo", help="Run the example study end to end in a scratch directory")
    p.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            errors = validate_registry(ROOT)
            emit({"valid": not errors, "errors": errors})
            return 2 if errors else 0
        if args.command == "index":
            print(build_index(ROOT), end="")
        elif args.command == "context":
            emit(context(ROOT, args.ids))
        elif args.command == "impact":
            emit(impact(ROOT, args.ids))
        elif args.command == "snapshot":
            emit(snapshot(ROOT, args.file))
        elif args.command == "create":
            emit(create(args.protocol, args.out, root=ROOT))
        elif args.command == "evaluate":
            result = evaluate(args.folder)
            if args.write:
                atomic_json(args.folder / "evaluation.json", result)
            emit(result)
        elif args.command == "report":
            text = report(args.folder)
            if args.write:
                (args.folder / "report.md").write_text(text, encoding="utf-8")
            print(text, end="")
        elif args.command == "demo":
            folder = args.out or ROOT / "runs/local" / datetime.now().strftime("demo-%Y%m%d-%H%M%S-%f")
            create(EXAMPLE_STUDY / "protocol.json", folder, root=ROOT)
            shutil.copyfile(EXAMPLE_STUDY / "frozen/result.json", folder / "result.json")
            result = evaluate(folder)
            atomic_json(folder / "evaluation.json", result)
            emit({"folder": str(folder), **result})
        return 0
    except (ContractError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: register S001, K001, DOC-example**

```bash
python3 -m harness snapshot investigations/001-example/study-01/frozen/inputs/hits.csv
```

Take `sha256`, `snapshot`, `anchor` (expect `L1-L41`) from the output and write `knowledge/registry.json`:

```json
{
  "schema_version": 1,
  "sources": [
    {
      "id": "S001",
      "family": "S001",
      "version": "2026-09-16-v1",
      "snapshot": "knowledge/snapshots/<SHA>.txt",
      "sha256": "<SHA>",
      "origin": "investigations/001-example/study-01/frozen/inputs/hits.csv",
      "anchor": "L1-L41",
      "kind": "dataset",
      "access": "Simulated example data written for this template; not collected from any real search. May be quoted freely.",
      "depends_on": []
    }
  ],
  "claims": [
    {
      "id": "K001",
      "statement": "In the example dataset, the combined search yields a 0.30 higher share of relevant hits than the single search.",
      "type": "derivation",
      "status": "provisional",
      "scope": "Simulated data with 40 hits. Shows the form of a knowledge entry, not a finding about literature search.",
      "reconsider_if": "The dataset is replaced by primary data, or the measure definition in study I001-01 changes.",
      "depends_on": [],
      "evidence": [
        {"source": "S001", "anchor": "L1-L41", "relation": "supports", "reading": "Rows with search_id=combined have 15 of 20 relevant; rows with search_id=single have 9 of 20. Evaluated in study-01/frozen/evaluation.json."}
      ],
      "history": [{"date": "2026-09-16", "status": "provisional", "reason": "Derived from study I001-01 on simulated data."}],
      "version": 1,
      "review_status": "unreviewed",
      "review_history": [{"date": "2026-09-16", "status": "unreviewed", "reason": "Example entry; nobody has reviewed it and nobody needs to."}]
    }
  ],
  "documents": [
    {"id": "DOC-example", "path": "investigations/001-example/README.md", "depends_on": ["K001"]}
  ]
}
```

- [ ] **Step 4: index and report**

```bash
python3 -m harness validate
python3 -m harness index > knowledge/INDEX.md
python3 -m harness report investigations/001-example/study-01/frozen --write
```

Expected: valid; `report.md` says "not committed yet" (the commit that adds it comes now; that is fine and honest; the README explains that `report` is re-run after the commit if a reviewer wants the hash. Add a line to the study README Assessment: "Run `python3 -m harness report … ` again after committing to see the commit hash.").

- [ ] **Step 5: add to study README Assessment** the two sentences about `affects` being empty and re-running `report`.

- [ ] **Step 6: run all tests (expect 3 + 13 + 11 + 6 = 33 OK), commit** `CLI and register: example claim K001 from the frozen input, index, report`

---

### Task 6: Method, templates, red team, knowledge README, decision log

**Files:** `method/README.md`, `method/templates.md`, `method/red-team.md`, `knowledge/README.md`, `DECISIONS.md`; append to `CHANGELOG.md`.

- [ ] **Step 1: `method/README.md`**

```markdown
# Method

The engine of this repo. An investigation answers one question through studies whose analysis plan was frozen and committed before data, and feeds what it learns into a register where every claim points at the excerpt it rests on. The method is field-neutral: it says nothing about your subject and everything about how a claim earns its place.

It leans on practice you can cite. Rule 3 is pre-registration as run by OSF Registries and AsPredicted, and the Registered Reports format where a journal reviews the plan before data. Rule 5 is provenance in the sense of the FAIR principles. Rule 8 uses CRediT roles and the conflict-of-interest declaration every journal asks for. Taken from `framtidens-arbetssatt`, where the rules were extracted from seven runs and sharpened by what each run found missing.

## Ground rules

1. **Blank sheet.** Start from the question, not from the literature you already like, the method you already know or the result you already expect.
2. **The competing hypothesis is written before evidence is gathered.** Every investigation states what would be true if the hypothesis is wrong, in a form that data could support. A rival that no data could support is a straw man.
3. **The analysis plan is frozen and committed before data.** The protocol names the measures, the threshold that supports the hypothesis and the threshold that supports the rival; the two may not overlap. `python3 -m harness create` freezes protocol and inputs with hashes into `frozen/`, and the git commit that adds it is the pre-registration record. Exploratory studies say so (`exploratory: true`) and get a descriptive outcome, not a verdict. For a real study, register the same plan with OSF Registries or as a Registered Report; `python3 -m harness report` prints the page to submit.
4. **Evidence grade is declared.** Published and peer-reviewed material first, then reports and grey literature, then your own transcripts and notes, then your own experience. Own experience of the thing under study is the weakest grade, and weakest of all when the conclusion would benefit you.
5. **Every claim rests on a preserved excerpt.** The register stores a hashed snapshot of the source and the line range the claim reads. A claim without an excerpt is not a claim, it is a note.
6. **Knowledge status and review status are separate.** `provisional` says how much the evidence carries; `reviewed` says someone other than the author checked. Neither is set automatically.
7. **Red team before synthesis.** Before an investigation writes its synthesis, a reader who did not write it attacks it along `method/red-team.md`. The synthesis records what the attack found and what changed.
8. **Interests are declared in the investigation README.** Funder, CRediT roles, conflicts of interest, your own prior position on the question. Declaring is not distancing: a conflicted source may be used, labelled, and not as the only leg a claim stands on.
9. **No rule changes without an entry in `DECISIONS.md` and a line in `CHANGELOG.md`.** A rule, a template or a register convention that changed during an investigation is written into both, and into the file that carries the rule, in one commit. A change nobody wrote down is invisible until the next investigation reads the wrong rule.
10. **Honest limits in every synthesis.** What is derived, what is observed, what is measured, and the data kind: simulated, primary or secondary.

## Close-out check

An investigation is finished when the documentation reflects the decisions it took, not when the synthesis is written. Five checks, in order.

1. **Decisions.** Every decision that changed the repo's direction, method, scope or what leaves the repo goes into `DECISIONS.md`: date, what, why, which files. The content of the investigation stays in its own files.
2. **Carrier documents.** Each decision stands in the file that carries the rule, not only in the log. Rule changes also get a `CHANGELOG.md` line.
3. **Harness.** `python3 -m harness validate`, then `python3 -m harness index > knowledge/INDEX.md`, then `python3 -m unittest discover -s tests`. All must pass.
4. **Investigation index.** The row in `investigations/README.md` matches the investigation README: status, outcome.
5. **Feedback.** Did the method, a template or the harness get in the way? If so, file it upstream: `CONTRIBUTING.md`.

Report deviations together with what was corrected.

## Files

- `README.md`: this file.
- `templates.md`: investigation README, study README, source entry, claim entry.
- `red-team.md`: five lines of attack.
```

- [ ] **Step 2: `method/templates.md`** (investigation README with Studies table and Declared interests incl. "Funding / Roles (CRediT) / Conflicts of interest / Prior position"; study README with the four commands; source and claim JSON skeletons without `audience` or `assertion_mode`; the validator rules paragraph). Use the Task 4 READMEs as filled examples; the template is the same headings with placeholders in angle brackets.

- [ ] **Step 3: `method/red-team.md`**

````markdown
# Red team

Run before the synthesis of every investigation, by a reader who did not write it. With an agent: a fresh session or a subagent with read access only. Replace `<investigation>`.

```
Working directory: this repo. Change no files.

Role: red team. Your job is to break the investigation, not to confirm it.

Read investigations/<investigation>/README.md, every study-NN/README.md and study-NN/frozen/protocol.json under it, method/README.md, and the register entries the investigation cites in knowledge/registry.json, including the snapshot each points at.

Attack along five lines:

1. Convenient conclusion. Would this conclusion be comfortable for the author, the funder or the supervisor? Look in both directions: a conclusion that flatters the hypothesis, and one that looks self-critical, since that is the cheapest way to appear objective.

2. Selection of evidence. Which sources would a hostile reviewer cite that the investigation does not? Which cited excerpt, read in full, says less than the reading claims? Check the anchor against the snapshot.

3. The measure. Does the measure in the protocol measure what the argument chain claims? Could it move for a reason unrelated to the hypothesis? Were the thresholds justified or picked to be passable?

4. The competing hypothesis. Is it a straw man? Write the strongest rival a competent opponent would put forward, and check whether the study could distinguish it from the hypothesis.

5. Generalisation. Where does the synthesis reach beyond the sample, the data kind, the setting or the period? Which limitation in a study README is missing from the synthesis?

Deliver a Markdown report of at most 800 words. Objections ordered by severity. For each: what it hits (file and section), why, and what resolves it: change the claim, add a study, add a limitation, or mark as undecided. No politeness.
```

Write what the red team found and what changed into the synthesis, dated and marked "after red team".
````

- [ ] **Step 4: `knowledge/README.md`** covering: the three lists; add a source with `python3 -m harness snapshot <file>` and paste the skeleton; source kinds; add a claim; when a source changes (new version, same family, `impact`); personal data and de-identification, with a pointer to the researcher's data management plan; git remembers.

- [ ] **Step 5: `DECISIONS.md`** with the four 2026-09-16 decisions: template from the model repo, form only; studies frozen and committed with no model adapter; MIT and CC BY 4.0; feedback upstream via issues and the close-out question. Plus a fifth: `frozen/` is committed and the git commit is the pre-registration record, after review.

- [ ] **Step 6: `CHANGELOG.md` `[Unreleased]` → `### Added`** list: knowledge register (validate, index, context, impact, snapshot); pre-registered studies (create, evaluate, report, demo) with disjoint thresholds and exploratory mode; ten ground rules and close-out check; templates; red-team prompt; example investigation I001 on simulated data.

- [ ] **Step 7: verify** `grep -c '^[0-9]*\. \*\*' method/README.md` prints 10; tests OK; **commit** `Method: ten ground rules, close-out check, templates, red team, register guide, decision log`

---

### Task 7: AGENTS.md, CLAUDE.md, skills

**Files:** `AGENTS.md`, `CLAUDE.md`, `.agents/skills/new-investigation/SKILL.md`, `.agents/skills/close-out/SKILL.md`

- [ ] **Step 1: `AGENTS.md`**

```markdown
# Instructions for agents

You are working in a research repo. The researcher owns the questions, the conclusions and the declared interests. You carry the work between those points.

## Before anything else

Read `method/README.md`: ten ground rules and a close-out check. Read `method/templates.md` before creating an investigation or a study. Read `knowledge/README.md` before touching `knowledge/registry.json`.

## Skills

- To start an investigation, follow `.agents/skills/new-investigation/SKILL.md`.
- To close an investigation or a session, follow `.agents/skills/close-out/SKILL.md`.

Codex discovers these as `$new-investigation` and `$close-out`. Other agents open the file and follow it.

## How to work

- Drive the work without asking permission at every step. Stop and ask when a choice would change an investigation's direction: the question, the competing hypothesis, a threshold, what counts as evidence.
- Write the competing hypothesis and freeze the protocol before looking at data. If the researcher wants to look first, say that rule 3 is about to be broken and let them decide.
- Never edit anything under a `frozen/` directory. If a protocol is wrong, write a new study.
- Never call a paid model or an external API from a study unless the researcher said so in this session. The harness makes no calls.
- Never commit identifiable personal data. Interview material enters `knowledge/snapshots/` only after the researcher has decided on de-identification. Example data is simulated and labelled `data_kind: simulated`.
- Every claim you add points at a preserved excerpt and has a concrete `reconsider_if`.
- When a rule, template or register convention changes, write it into `DECISIONS.md`, `CHANGELOG.md` and the file that carries the rule, in the same commit.

## Language

Write in the language the researcher writes in. Keep file names, JSON keys and commands in English so the harness and templates keep working.
```

- [ ] **Step 2: `CLAUDE.md`**: exactly `@AGENTS.md` and a newline.

- [ ] **Step 3: `new-investigation/SKILL.md`** (frontmatter `name: new-investigation`, description "Start a new investigation: directory, README, first study protocol, register check. Use when the researcher has a question to test. Not for editing an existing investigation."). Steps: read method files; next number; ask one at a time: question, hypothesis, competing hypothesis (push once if it is just "the hypothesis is false"), first study's measure, unit and two disjoint thresholds or `exploratory: true`, data kind, declared interests (funding, CRediT, COI, prior position); create `investigations/NNN-<slug>/README.md` (status planned), `study-01/protocol.json`, `study-01/inputs/.gitkeep`, `study-01/README.md` (status protocol written); add row to `investigations/README.md`; run `python3 -m harness validate`; tell the researcher the next step is to place inputs and run `python3 -m harness create investigations/NNN-<slug>/study-01/protocol.json --out investigations/NNN-<slug>/study-01/frozen`, then commit `frozen/` before any analysis.

- [ ] **Step 4: `close-out/SKILL.md`** (frontmatter `name: close-out`, description "Run the close-out check when an investigation or session ends, before anything is shared. Ends with the feedback question about the template."). Steps 1 to 5 mirroring `method/README.md`, with the three commands, the CHANGELOG line check, and the feedback step drafting an issue from `.github/ISSUE_TEMPLATE/method-gap.md` and offering `gh issue create -R fabian-von-tiedemann/research-harness-template --title "<title>" --body-file <draft>`, never filing without the researcher seeing the text, never including subject content or personal data.

- [ ] **Step 5: verify `head -4 .agents/skills/*/SKILL.md` shows frontmatter; commit** `Agent instructions and skills: new-investigation, close-out`

---

### Task 8: Feedback loop

**Files:** `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/method-gap.md`, `.github/ISSUE_TEMPLATE/template-improvement.md`, `.github/ISSUE_TEMPLATE/config.yml`

- [ ] **Step 1: `CONTRIBUTING.md`**: what to send (method gaps, harness friction, new study patterns, fixes), what not to send (subject content, personal data, model adapters inside the harness with pointer to DECISIONS.md), how (issue templates; the close-out skill drafts it; PR with tests passing and a CHANGELOG line), licence of contributions.
- [ ] **Step 2: `method-gap.md`**: frontmatter name/about/title/labels; sections Which rule, template or command; What you were doing; What went wrong; What you did instead.
- [ ] **Step 3: `template-improvement.md`**: What to change; Why; Sketch.
- [ ] **Step 4: `config.yml`**: `blank_issues_enabled: true`.
- [ ] **Step 5: commit** `Feedback loop: contributing guide and issue templates`

---

### Task 9: README

**Files:** `README.md`

- [ ] **Step 1: write README** with sections: title and one-paragraph what; Who it is for (doctoral and master's work; research groups; policy analysis and evaluation; consultancy and product research with declared interests; grant applications: the frozen protocol, its report and the decision log are evidence of rigor a reviewer can check; teaching research method); First hour (Use this template, clone, three commands, read method, start your agent: Codex `$new-investigation`, others "follow `.agents/skills/new-investigation/SKILL.md`", delete the example); The loop (ASCII diagram, four bullets: investigation, study, knowledge, decisions); Established practice it leans on (pre-registration and Registered Reports, FAIR, CRediT and COI, Keep a Changelog and SemVer, CITATION.cff); Works with (Claude Code via `CLAUDE.md` import, Codex, OpenCode and Pi via `AGENTS.md`; skills by path); Structure table; Commands block with all nine; exit codes; Improving the template; Versioning; Licence; Origin.
- [ ] **Step 2: link check** as before; **commit** `README`

---

### Task 10: Message, release, publish

**Files:** `docs/message-to-amanda.md`; modify `CHANGELOG.md`

- [ ] **Step 1: `docs/message-to-amanda.md`** in Swedish: what it is; the five first-hour steps with the new repo URL and Codex `$new-investigation`; two requests (write in any language; send friction back as issues, the close-out skill asks); sign-off.
- [ ] **Step 2: release the changelog**: rename `## [Unreleased]` section to `## [0.1.0] - 2026-09-16`, add a fresh empty `## [Unreleased]` above it, and link references at the bottom:

```
[Unreleased]: https://github.com/fabian-von-tiedemann/research-harness-template/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fabian-von-tiedemann/research-harness-template/releases/tag/v0.1.0
```

- [ ] **Step 3: commit** `Release 0.1.0`
- [ ] **Step 4: clean-clone verification**

```bash
rm -rf /tmp/rht-check && git clone -q /Users/fabianvontiedemann/Developer/research-harness-template /tmp/rht-check && (cd /tmp/rht-check && python3 -m harness validate && python3 -m harness demo && python3 -m unittest discover -s tests && git status --porcelain) && rm -rf /tmp/rht-check
grep -rn '—' --include='*.md' --include='*.py' --include='*.json' --include='*.cff' . | grep -v '^./.git/' | grep -v 'docs/superpowers'
```

Expected: valid, `supports_hypothesis`, tests OK, porcelain empty, no em-dashes outside `docs/superpowers`.

- [ ] **Step 5: publish, template flag, tag, release**

```bash
gh repo create fabian-von-tiedemann/research-harness-template --public --source . --push --description "A research harness for agent-assisted, pre-registered work: frozen study protocols, hashed knowledge register, decision log, agent rules. Field-neutral."
gh api -X PATCH repos/fabian-von-tiedemann/research-harness-template -f is_template=true
git tag -a v0.1.0 -m "0.1.0"
git push origin v0.1.0
gh release create v0.1.0 --title "0.1.0" --notes "$(awk '/^## \[0.1.0\]/{f=1;next}/^## \[/{f=0}f' CHANGELOG.md)"
gh repo view fabian-von-tiedemann/research-harness-template --json isTemplate,url
```

- [ ] **Step 6: re-run `report --write` in the example study now that `frozen/` is committed**, commit `Example report with commit hash`, push. The report then shows the pre-registration commit.

- [ ] **Step 7: report to the user**: URL, release, three commands, message path, test count.

---

## Self-review

**Spec coverage.** Vocabulary (study, rival, simulated/primary/secondary): Tasks 3, 4, 6. Trimmed register: Task 2. Study engine with disjointness, exploratory, reserved names, result hash, report with git commit: Task 3. Committed `frozen/` and honest chronology (protocol before K001): Tasks 4 and 5. Snapshot command: Task 2 and 5. Established practice named: Task 6 rules 3, 5, 8 and README Task 9. Multi-agent: Task 7 (`@AGENTS.md`, skill paths). Feedback loop: Tasks 6, 7, 8. Versioning: Tasks 1 and 10. CITATION.cff: Task 1. Grant use: report command and README.

**Placeholders.** `<SHA>` in Task 5 is substituted from the `snapshot` output. Tasks 6 to 9 describe some prose files by section list rather than full text; the executor writes them following the filled examples in Tasks 4 and 6 and the spec. Angle-bracket placeholders inside templates are template content.

**Type consistency.** `create(protocol_path, out_dir, root=None)`, `evaluate(run_dir)`, `report(run_dir)` used identically in Tasks 3, 4, 5. `snapshot(root, file)` returns `sha256`, `snapshot`, `anchor`, `lines`, `source_skeleton` in Tasks 2 and 5. Register sections `sources, claims, documents` everywhere. Test counts: 3 + 13 + 11 + 6 = 33.
