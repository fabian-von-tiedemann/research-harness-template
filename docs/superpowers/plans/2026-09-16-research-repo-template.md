# Research Repo Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `research-repo-template`, a public GitHub template repo that gives a researcher a working method (investigations, frozen trials, a versioned knowledge register, decision log, agent rules) plus a feedback loop back to the template.

**Architecture:** Two small Python modules under `harness/` (a knowledge register validator copied from the model repo, and a new trial engine that freezes a protocol and evaluates a result separately) behind one CLI. Everything else is Markdown: method rules, templates, one worked example investigation, agent instructions and two Codex skills. Standard library only.

**Tech Stack:** Python 3.10+ standard library, `unittest`, Git, `gh` CLI. Codex reads `AGENTS.md` and `.agents/skills/*/SKILL.md`.

**Spec:** `docs/superpowers/specs/2026-09-16-research-repo-template-design.md`

**Repo root for all tasks:** `/Users/fabianvontiedemann/Developer/forskningsrepo` (already `git init`, branch `main`, two commits with the spec). Run every command from there.

## Global Constraints

- Language: English everywhere (file names, commands, rules, JSON keys, commit messages). The only Swedish file is `docs/message-to-amanda.md`.
- Python 3.10 or later, standard library only. No `requirements.txt`, no `pyproject.toml`.
- Exit codes: 0 success, 2 invalid input or contract, 3 incomplete.
- Licences: MIT for `harness/`, `tests/`, scripts. CC BY 4.0 for text.
- No em-dashes in any prose. Use commas, colons or full stops.
- No real personal data anywhere. Example data is synthetic and labelled so.
- Tests run with `python3 -m unittest discover -s tests -v` and must pass at the end of every task.
- Commit after every task with the trailer `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`.

---

### Task 1: Scaffold, licences, common helpers

**Files:**
- Create: `.gitignore`, `LICENSE`, `LICENSE-CONTENT`, `harness/__init__.py`, `harness/common.py`, `tests/__init__.py`, `tests/test_common.py`

**Interfaces:**
- Produces: `harness.common.ContractError(ValueError)`, `read_json(path) -> Any`, `digest(path) -> str` (sha256 hex), `atomic_json(path, data) -> None`, `confined(base, relative) -> Path` (raises `ContractError` if outside `base` or not a file).

- [ ] **Step 1: Write `.gitignore`**

```
__pycache__/
*.py[cod]
.context/
runs/local/
```

- [ ] **Step 2: Write `LICENSE` (MIT)**

```
MIT License

Copyright (c) 2026 Fabian von Tiedemann

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: Write `LICENSE-CONTENT`**

```
Creative Commons Attribution 4.0 International (CC BY 4.0)

The text content of this repository (everything outside harness/, tests/ and
scripts, including method/, investigations/, knowledge/, AGENTS.md and
README.md) is licensed under CC BY 4.0.

You are free to share and adapt the material for any purpose, including
commercially, as long as you give appropriate credit, link to the licence and
indicate if changes were made.

Full licence text: https://creativecommons.org/licenses/by/4.0/legalcode

Attribution: "Research repo template" by Fabian von Tiedemann,
https://github.com/fabian-von-tiedemann/research-repo-template
```

- [ ] **Step 4: Write `harness/__init__.py`**

```python
"""Local research instrument. No external calls on import."""

__version__ = "0.1.0"
```

- [ ] **Step 5: Write failing tests `tests/__init__.py` (empty) and `tests/test_common.py`**

```python
import json
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
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_common -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.common'`

- [ ] **Step 7: Write `harness/common.py`**

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

- [ ] **Step 8: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_common -v`
Expected: 3 tests, OK

- [ ] **Step 9: Commit**

```bash
git add .gitignore LICENSE LICENSE-CONTENT harness tests
git commit -m "Scaffold: licences, common helpers, first tests

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Example input data and the knowledge register

**Files:**
- Create: `investigations/001-example/trial-01/sources/hits.csv`, `knowledge/snapshots/<sha256>.txt`, `knowledge/registry.json`, `harness/registry.py`, `tests/test_registry.py`

**Interfaces:**
- Consumes: nothing from harness (registry has its own loader).
- Produces: `harness.registry.validate_registry(root) -> list[dict]` (each `{'code', 'message'}`; empty list means valid), `build_index(root) -> str`, `context(root, ids, audience='internal', sources_only=False) -> dict`, `impact(root, changed_ids, as_of=None) -> dict`, constants `SECTIONS`, `CLAIM_TYPES`, `STATUSES`, `REVIEW_STATUSES`. Register lives at `<root>/knowledge/registry.json`.

- [ ] **Step 1: Write the synthetic CSV `investigations/001-example/trial-01/sources/hits.csv`**

Exactly this content (header plus 40 rows, LF line endings, trailing newline):

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

`single` has 9 relevant of 20 (0.45). `combined` has 15 relevant of 20 (0.75). Difference 0.30.

- [ ] **Step 2: Create the snapshot and compute its hash**

```bash
mkdir -p knowledge/snapshots
SHA=$(shasum -a 256 investigations/001-example/trial-01/sources/hits.csv | cut -d' ' -f1)
cp investigations/001-example/trial-01/sources/hits.csv "knowledge/snapshots/$SHA.txt"
echo "$SHA"
```

Keep the printed `$SHA`; it goes into `registry.json` twice below (the `snapshot` path and `sha256`).

- [ ] **Step 3: Write `knowledge/registry.json`** (replace `<SHA>` with the hash from Step 2)

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
      "origin": "investigations/001-example/trial-01/sources/hits.csv",
      "anchor": "L1-L41",
      "kind": "dataset",
      "audience": "public",
      "access": "synthetic example data written for this template; not collected from any real search",
      "depends_on": []
    }
  ],
  "claims": [
    {
      "id": "K001",
      "statement": "In the example dataset, the combined search yields a 0.30 higher share of relevant hits than the single search.",
      "type": "derivation",
      "status": "provisional",
      "assertion_mode": "descriptive",
      "audience": "public",
      "scope": "Synthetic data with 40 hits. Shows the form of a knowledge entry, not a finding about literature search.",
      "reconsider_if": "The dataset is replaced by collected data, or the measure definition in trial I001-01 changes.",
      "depends_on": [],
      "evidence": [
        {
          "source": "S001",
          "anchor": "L1-L41",
          "relation": "supports",
          "reading": "Rows with search_id=combined have 15 of 20 relevant; rows with search_id=single have 9 of 20."
        }
      ],
      "history": [
        {"date": "2026-09-16", "status": "provisional", "reason": "Derived from trial I001-01 on synthetic data."}
      ],
      "version": 1,
      "review_status": "unreviewed",
      "review_history": [
        {"date": "2026-09-16", "status": "unreviewed", "reason": "Example entry; nobody has reviewed it and nobody needs to."}
      ]
    }
  ],
  "documents": [
    {
      "id": "DOC-example",
      "path": "investigations/001-example/README.md",
      "audience": "public",
      "depends_on": ["K001"]
    }
  ],
  "uses": [
    {
      "id": "USE-readme-example",
      "description": "Cited in README.md as the worked example of the loop.",
      "audience": "public",
      "depends_on": ["K001"]
    }
  ]
}
```

- [ ] **Step 4: Write failing tests `tests/test_registry.py`**

```python
import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from harness.registry import CLAIM_TYPES, build_index, context, impact, validate_registry

ROOT = Path(__file__).resolve().parents[1]


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / "knowledge", self.root / "knowledge")
        self.path = self.root / "knowledge/registry.json"
        self.data = json.loads(self.path.read_text())

    def save(self):
        self.path.write_text(json.dumps(self.data))

    def codes(self):
        self.save()
        return {x["code"] for x in validate_registry(self.root)}

    def claim(self, ident="K001"):
        return next(n for n in self.data["claims"] if n["id"] == ident)

    def source(self, ident="S001"):
        return next(n for n in self.data["sources"] if n["id"] == ident)

    def test_shipped_register_is_valid(self):
        self.assertEqual(validate_registry(self.root), [])
        self.assertIn("K001", build_index(self.root))
        self.assertIn("| ID |", build_index(self.root))

    def test_claim_types_are_field_neutral(self):
        self.assertEqual(CLAIM_TYPES, {"observation", "hypothesis", "interpretation", "derivation", "model_result", "dated_analysis"})
        self.claim()["type"] = "conditional_derivation"
        self.assertIn("claim_type", self.codes())

    def test_duplicates_missing_and_cycles(self):
        self.claim()["depends_on"] = ["UNKNOWN", "DOC-example"]
        self.data["claims"].append(copy.deepcopy(self.claim()))
        self.assertTrue({"duplicate_id", "missing_reference", "dependency_cycle"} <= self.codes())

    def test_missing_premise(self):
        self.claim()["evidence"] = []
        self.claim()["depends_on"] = []
        self.assertIn("missing_premise", self.codes())

    def test_observation_needs_observational_source(self):
        self.claim()["type"] = "observation"
        self.assertIn("observation_from_nonobservation", self.codes())
        self.source()["kind"] = "transcript"
        self.assertNotIn("observation_from_nonobservation", self.codes())

    def test_normative_observation_rejected(self):
        self.source()["kind"] = "transcript"
        self.claim()["type"] = "observation"
        self.claim()["assertion_mode"] = "normative"
        self.assertIn("normative_observation", self.codes())

    def test_model_result_needs_model_trial(self):
        self.claim()["type"] = "model_result"
        self.assertIn("model_result_from_nontrial", self.codes())
        self.source()["kind"] = "model_trial"
        self.assertNotIn("model_result_from_nontrial", self.codes())

    def test_snapshot_mutation_fails(self):
        (self.root / self.source()["snapshot"]).write_text("changed")
        self.assertIn("snapshot_hash", self.codes())

    def test_snapshot_path_escape(self):
        self.source()["snapshot"] = "../outside"
        self.assertIn("snapshot_read", self.codes())

    def test_evidence_must_select_preserved_excerpt(self):
        self.claim()["evidence"][0]["anchor"] = "L1-L2"
        self.assertIn("evidence_anchor", self.codes())

    def test_version_and_review_are_separate(self):
        n = self.claim()
        n["version"] = 0
        n["review_status"] = "reviewed"
        self.assertTrue({"claim_version", "review_history"} <= self.codes())

    def test_history_is_consistent(self):
        self.claim()["status"] = "refuted"
        self.assertIn("status_history", self.codes())

    def test_malformed_shape_is_error_not_crash(self):
        self.claim()["evidence"] = ["invalid"]
        self.assertIn("shape", self.codes())

    def test_versions_coexist(self):
        new = copy.deepcopy(self.source())
        new.update(id="S001-v2", version="2026-09-17-v2", snapshot="knowledge/snapshots/new.txt", sha256=hashlib.sha256(b"new\n").hexdigest(), anchor="L1-L1")
        (self.root / new["snapshot"]).write_text("new\n")
        self.data["sources"].append(new)
        self.assertEqual(self.codes(), set())
        pack = context(self.root, ["S001", "S001-v2"])
        self.assertEqual(pack["source_family_count"], 1)
        self.assertNotEqual(pack["records"][0]["excerpt"], pack["records"][1]["excerpt"])

    def test_public_blocks_transitive_internal(self):
        self.source()["audience"] = "internal"
        self.save()
        pack = context(self.root, ["USE-readme-example"], audience="public")
        self.assertEqual(pack["records"], [])
        self.assertEqual(pack["selection_log"][0]["reason"], "nonpublic_dependency_or_record")

    def test_sources_only_omits_claims(self):
        self.source()["kind"] = "empirical_report"
        self.save()
        pack = context(self.root, ["K001"], sources_only=True)
        ids = {r["id"] for r in pack["records"]}
        self.assertIn("S001", ids)
        self.assertNotIn("K001", ids)

    def test_multihop_impact(self):
        result = impact(self.root, ["S001"], "2026-09-16")
        self.assertIn("K001", result["affected"]["claims"])
        self.assertIn("DOC-example", result["affected"]["documents"])
        self.assertIn("USE-readme-example", result["affected"]["uses"])
        self.assertEqual(json.loads(self.path.read_text()), self.data)

    def test_impact_legal_review_due(self):
        self.source()["legal"] = {"status": "enacted", "review_on": "2026-09-10"}
        self.save()
        due = impact(self.root, [], "2026-09-16")
        self.assertIn("S001", due["legal_review_due"])
        self.assertIn("K001", due["affected"]["claims"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_registry -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.registry'`

- [ ] **Step 6: Write `harness/registry.py`**

This is the model repo's `harness/registry.py` with four changes: the register path is `knowledge/registry.json`; `CLAIM_TYPES` is the new set; the index header is English; `raw_source_ids` in `context` includes `dataset`. Everything else is verbatim.

```python
"""Versioned research register. Validates declarations, never their truth."""
from __future__ import annotations
import hashlib
import json
from datetime import date
from pathlib import Path

SECTIONS = ('sources', 'claims', 'documents', 'uses')
CLAIM_TYPES = {'observation', 'hypothesis', 'interpretation', 'derivation', 'model_result', 'dated_analysis'}
STATUSES = {'open', 'provisional', 'bounded_support', 'weakened', 'refuted', 'superseded'}
REVIEW_STATUSES = {'unreviewed', 'reviewed', 'needs_review'}
RAW_SOURCE_KINDS = ('transcript', 'empirical_report', 'dataset', 'legal_text')

def _load(root):
    root = Path(root)
    return json.loads((root / 'knowledge/registry.json').read_text(encoding='utf-8'))

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
            if n.get('audience') not in ('public', 'internal'):
                fail('audience', ident)
            if not isinstance(n.get('depends_on', []), list) or any(not isinstance(x, str) for x in n.get('depends_on', [])):
                fail('shape', f'{ident}: depends_on must be strings')
            if not isinstance(n.get('evidence', []), list) or any(not isinstance(e, dict) or not isinstance(e.get('source'), str) for e in n.get('evidence', [])):
                fail('shape', f'{ident}: evidence must contain source IDs')
            if 'legal' in n:
                if not isinstance(n['legal'], dict):
                    fail('shape', f'{ident}: legal must be object')
                elif 'actors' in n['legal'] and (not isinstance(n['legal']['actors'], list) or any(not isinstance(a, str) for a in n['legal']['actors'])):
                    fail('shape', f'{ident}: legal actors must be strings')
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
            try:
                content = _safe_path(root, n.get('snapshot')).read_bytes()
                if hashlib.sha256(content).hexdigest() != n.get('sha256'):
                    fail('snapshot_hash', ident)
                anchor = n.get('anchor', {})
                if not isinstance(anchor, str) or not anchor.startswith('L'):
                    fail('source_anchor', ident)
                else:
                    parts = anchor[1:].split('-L')
                    start, end = int(parts[0]), int(parts[-1])
                    if not 1 <= start <= end <= len(content.decode('utf-8').splitlines()):
                        fail('source_anchor', ident)
            except (OSError, ValueError, TypeError, UnicodeError):
                fail('snapshot_read', ident)
            review = n.get('legal', {}).get('review_on')
            if review:
                try:
                    date.fromisoformat(review)
                except (TypeError, ValueError):
                    fail('legal_date', ident)
        if sections[ident] == 'claims':
            if n.get('type') not in CLAIM_TYPES:
                fail('claim_type', ident)
            if n.get('status') not in STATUSES:
                fail('claim_status', ident)
            if not isinstance(n.get('version'), int) or isinstance(n.get('version'), bool) or n['version'] < 1:
                fail('claim_version', ident)
            if n.get('review_status') not in REVIEW_STATUSES:
                fail('review_status', ident)
            reviews = n.get('review_history')
            if not isinstance(reviews, list) or not reviews or any(not isinstance(h, dict) or h.get('status') not in REVIEW_STATUSES or not h.get('reason') for h in reviews):
                fail('review_history', ident)
            else:
                try:
                    review_dates = [date.fromisoformat(h['date']) for h in reviews]
                    if review_dates != sorted(review_dates) or reviews[-1]['status'] != n.get('review_status'):
                        fail('review_history', ident)
                except (KeyError, TypeError, ValueError):
                    fail('review_history', ident)
            history = n.get('history')
            if not isinstance(history, list) or not history or any(not isinstance(h, dict) or h.get('status') not in STATUSES or not h.get('reason') for h in history):
                fail('status_history', ident)
            else:
                try:
                    dates = [date.fromisoformat(h['date']) for h in history]
                    if dates != sorted(dates) or history[-1]['status'] != n.get('status'):
                        fail('status_history', ident)
                except (KeyError, TypeError, ValueError):
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
            if n.get('type') == 'observation' and n.get('assertion_mode') == 'normative':
                fail('normative_observation', ident)
            legal = n.get('legal', {})
            if legal.get('binding') is True:
                refs = [nodes[d] for d in _dependencies(n) if d in nodes and nodes[d].get('legal')]
                if not refs:
                    fail('legal_basis', ident)
                for src in refs:
                    law = src['legal']
                    if law.get('status') in ('proposal', 'previous_analysis'):
                        fail('proposal_as_binding', ident)
                    if legal.get('actor') not in law.get('actors', []):
                        fail('legal_actor', ident)
                if not legal.get('conditions') or not legal.get('as_of'):
                    fail('legal_context', ident)
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

def context(root, ids, audience='internal', sources_only=False):
    if audience not in ('internal', 'public'):
        raise ValueError('audience must be internal or public')
    data = _valid(root)
    nodes = _nodes(data)
    selected, log = set(), []
    memo = {}
    def public(ident):
        if ident not in memo:
            memo[ident] = nodes[ident]['audience'] == 'public' and all(public(dep) for dep in _dependencies(nodes[ident]))
        return memo[ident]
    def select(ident):
        if ident not in nodes:
            raise ValueError(f'Unknown ID: {ident}')
        if ident in selected:
            return
        if audience == 'public' and not public(ident):
            # No statement, source, origin, title or sensitive dependency IDs leak.
            log.append({'id': ident, 'action': 'excluded', 'reason': 'nonpublic_dependency_or_record'})
            return
        selected.add(ident)
        for dep in _dependencies(nodes[ident]):
            select(dep)
    for ident in ids:
        select(ident)
    source_ids = {n['id'] for n in data['sources']}
    raw_source_ids = {n['id'] for n in data['sources'] if n.get('kind') in RAW_SOURCE_KINDS}
    kept = sorted(selected & raw_source_ids if sources_only else selected)
    for ident in sorted(selected):
        log.append({'id': ident, 'action': 'included' if ident in kept else 'excluded', 'reason': 'sources_only' if ident not in kept else 'requested_or_dependency'})
    records = []
    for ident in kept:
        n = dict(nodes[ident])
        if ident in source_ids:
            n['excerpt'] = _safe_path(root, n['snapshot']).read_text(encoding='utf-8')
        records.append(n)
    families = sorted({nodes[i]['family'] for i in kept if i in source_ids})
    return {'schema_version': 1, 'audience': audience, 'sources_only': sources_only, 'records': records, 'source_families': families, 'source_family_count': len(families), 'selection_log': log, 'limitation': 'Family count is provenance grouping, never evidence strength.'}

def impact(root, changed_ids, as_of=None):
    data = _valid(root)
    nodes = _nodes(data)
    unknown = set(changed_ids) - nodes.keys()
    if unknown:
        raise ValueError(f'Unknown IDs: {sorted(unknown)}')
    today = date.fromisoformat(as_of) if isinstance(as_of, str) else (as_of or date.today())
    due = {n['id'] for n in data['sources'] if n.get('legal', {}).get('review_on') and date.fromisoformat(n['legal']['review_on']) <= today}
    affected, reasons = set(changed_ids) | due, {}
    for ident in affected:
        reasons[ident] = 'legal_review_due' if ident in due else 'changed'
    while True:
        added = {ident for ident, n in nodes.items() if ident not in affected and set(_dependencies(n)) & affected}
        if not added:
            break
        for ident in added:
            reasons[ident] = 'depends_on:' + ','.join(sorted(set(_dependencies(nodes[ident])) & affected))
        affected |= added
    return {'schema_version': 1, 'as_of': today.isoformat(), 'changed': sorted(changed_ids), 'legal_review_due': sorted(due), 'affected': {section: [n['id'] for n in data[section] if n['id'] in affected] for section in SECTIONS}, 'review_proposals': [{'id': i, 'reason': reasons[i], 'action': 'review_no_automatic_status_change'} for i in sorted(affected)]}

def build_index(root):
    data = _valid(root)
    rows = ['# Knowledge index', '', 'Generated from registry.json by `python3 -m harness index`. Knowledge status is a declaration; review status is reported separately. Nothing here is an automatic truth classification.', '', '| ID | Version | Type | Status | Review | Statement |', '|---|---|---|---|---|---|']
    for n in data['claims']:
        rows.append(f'| {n["id"]} | {n["version"]} | {n["type"]} | {n["status"]} | {n["review_status"]} | {n["statement"].replace("|", " / ")} |')
    rows.extend(['', '## Source families', ''])
    for family in sorted({n['family'] for n in data['sources']}):
        rows.append(f'- {family}: ' + ', '.join(n['id'] for n in data['sources'] if n['family'] == family))
    return '\n'.join(rows) + '\n'
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_registry -v`
Expected: 18 tests, OK. If `test_shipped_register_is_valid` fails with `snapshot_hash` or `source_anchor`, the `<SHA>` was not substituted or the CSV has a different line count; fix `registry.json`.

- [ ] **Step 8: Commit**

```bash
git add investigations knowledge harness/registry.py tests/test_registry.py
git commit -m "Knowledge register: validator from the model repo, example source and claim

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Trial engine

**Files:**
- Create: `harness/trial.py`, `tests/test_trial.py`

**Interfaces:**
- Consumes: `harness.common.ContractError, read_json, digest, atomic_json, confined`; `harness.registry._nodes, _load` (via a small helper `_register_ids(root)` defined in trial.py that returns `set()` when `knowledge/registry.json` is absent).
- Produces: `harness.trial.OPS: dict[str, Callable]`, `validate_protocol(p: dict) -> None`, `apply_rule(rule: dict, value: float) -> str` returning `'supports_hypothesis' | 'supports_rival' | 'undecided'`, `create(protocol_path: Path, out_dir: Path, root: Path | None = None) -> dict` (the manifest), `evaluate(run_dir: Path) -> dict` (the evaluation; does not write), `DATA_KINDS = ('synthetic', 'collected', 'secondary')`.

- [ ] **Step 1: Write failing tests `tests/test_trial.py`**

```python
import json
import tempfile
import unittest
from pathlib import Path

from harness.common import ContractError, atomic_json, read_json
from harness.trial import apply_rule, create, evaluate, validate_protocol


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
        "affects": [],
        "inputs": ["sources/data.csv"],
        "data_kind": "synthetic",
        "limitations": "fixture",
    }
    p.update(overrides)
    return p


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.src = self.root / "trial"
        (self.src / "sources").mkdir(parents=True)
        (self.src / "sources/data.csv").write_text("a,b\n1,2\n")
        self.protocol_path = self.src / "protocol.json"
        atomic_json(self.protocol_path, protocol())
        self.out = self.root / "runs/t01"

    def write_result(self, value, folder=None):
        atomic_json((folder or self.out) / "result.json", {"measures": {"m1": value}, "note": "fixture"})

    def test_apply_rule_three_outcomes(self):
        rule = protocol()["interpretation_rule"]
        self.assertEqual(apply_rule(rule, 0.3), "supports_hypothesis")
        self.assertEqual(apply_rule(rule, -0.1), "supports_rival")
        self.assertEqual(apply_rule(rule, 0.05), "undecided")

    def test_apply_rule_rejects_unknown_op(self):
        rule = protocol()["interpretation_rule"]
        rule["supports_hypothesis_if"]["op"] = "~"
        with self.assertRaises(ContractError):
            apply_rule(rule, 0.3)

    def test_validate_protocol_requires_fields_and_known_measure(self):
        with self.assertRaises(ContractError):
            validate_protocol(protocol(hypothesis=""))
        with self.assertRaises(ContractError):
            validate_protocol(protocol(interpretation_rule={**protocol()["interpretation_rule"], "measure": "m9"}))
        with self.assertRaises(ContractError):
            validate_protocol(protocol(data_kind="real"))
        validate_protocol(protocol())

    def test_create_freezes_and_hashes(self):
        manifest = create(self.protocol_path, self.out)
        self.assertEqual(manifest["status"], "frozen")
        self.assertEqual(set(manifest["hashes"]), {"protocol.json", "sources/data.csv"})
        self.assertTrue((self.out / "sources/data.csv").exists())
        self.assertEqual(read_json(self.out / "manifest.json"), manifest)

    def test_create_refuses_existing_dir_and_escaping_inputs(self):
        create(self.protocol_path, self.out)
        with self.assertRaises(ContractError):
            create(self.protocol_path, self.out)
        atomic_json(self.protocol_path, protocol(inputs=["../outside.csv"]))
        (self.root / "outside.csv").write_text("x")
        with self.assertRaises(ContractError):
            create(self.protocol_path, self.root / "runs/t02")

    def test_create_checks_affects_against_register(self):
        (self.root / "knowledge").mkdir()
        atomic_json(self.root / "knowledge/registry.json", {"schema_version": 1, "sources": [], "claims": [], "documents": [], "uses": []})
        atomic_json(self.protocol_path, protocol(affects=["K999"]))
        with self.assertRaises(ContractError):
            create(self.protocol_path, self.out, root=self.root)

    def test_evaluate_outcomes(self):
        create(self.protocol_path, self.out)
        self.write_result(0.3)
        result = evaluate(self.out)
        self.assertEqual(result["outcome"], "supports_hypothesis")
        self.assertEqual(result["measures"], {"m1": 0.3})
        self.assertEqual(result["limitations"], "fixture")
        self.assertEqual(len(result["manifest_sha256"]), 64)
        self.write_result(-0.2)
        self.assertEqual(evaluate(self.out)["outcome"], "supports_rival")
        self.write_result(0.1)
        self.assertEqual(evaluate(self.out)["outcome"], "undecided")

    def test_evaluate_rejects_tampered_input(self):
        create(self.protocol_path, self.out)
        self.write_result(0.3)
        (self.out / "sources/data.csv").write_text("a,b\n9,9\n")
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_trial -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.trial'`

- [ ] **Step 3: Write `harness/trial.py`**

```python
"""Frozen trials with separate evaluation. No model calls, no simulator."""

from __future__ import annotations

import math
import operator
import shutil
from datetime import datetime, timezone
from pathlib import Path

from .common import ContractError, atomic_json, confined, digest, read_json

OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt, "==": operator.eq}
DATA_KINDS = ("synthetic", "collected", "secondary")
REQUIRED = ("schema_version", "id", "investigation", "question", "hypothesis", "rival", "measures", "interpretation_rule", "affects", "inputs", "data_kind", "limitations")
OUTCOMES = ("supports_hypothesis", "supports_rival", "undecided")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _condition(cond, name):
    if not isinstance(cond, dict) or cond.get("op") not in OPS:
        raise ContractError(f"{name}: op must be one of {sorted(OPS)}")
    value = cond.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ContractError(f"{name}: value must be a finite number")


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
    rule = p["interpretation_rule"]
    if not isinstance(rule, dict) or rule.get("measure") not in ids:
        raise ContractError("interpretation_rule.measure must name a declared measure")
    _condition(rule.get("supports_hypothesis_if"), "supports_hypothesis_if")
    _condition(rule.get("supports_rival_if"), "supports_rival_if")
    for key in ("affects", "inputs"):
        if not isinstance(p[key], list) or any(not isinstance(x, str) or not x for x in p[key]):
            raise ContractError(f"{key} must be a list of strings")


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
    """IDs in the register, or None when the repo has no register yet."""
    path = Path(root) / "knowledge/registry.json"
    if not path.exists():
        return None
    data = read_json(path)
    return {n["id"] for section in ("sources", "claims", "documents", "uses") for n in data.get(section, []) if isinstance(n, dict) and "id" in n}


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
        raise ContractError(f"Run directory already exists: {out_dir}")
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


def evaluate(run_dir):
    run_dir = Path(run_dir)
    manifest = read_json(run_dir / "manifest.json")
    if manifest.get("schema_version") != 1 or manifest.get("status") != "frozen" or not isinstance(manifest.get("hashes"), dict):
        raise ContractError("manifest.json is not a frozen trial manifest")
    for rel, expected in manifest["hashes"].items():
        path = confined(run_dir, rel)
        if digest(path) != expected:
            raise ContractError(f"Frozen file changed after freezing: {rel}")
    p = read_json(run_dir / "protocol.json")
    validate_protocol(p)
    result = read_json(run_dir / "result.json")
    measures = result.get("measures") if isinstance(result, dict) else None
    if not isinstance(measures, dict):
        raise ContractError("result.json must contain an object 'measures'")
    for m in p["measures"]:
        value = measures.get(m["id"])
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ContractError(f"result.json missing numeric measure {m['id']}")
    rule = p["interpretation_rule"]
    outcome = apply_rule(rule, measures[rule["measure"]])
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
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_trial -v`
Expected: 9 tests, OK

- [ ] **Step 5: Commit**

```bash
git add harness/trial.py tests/test_trial.py
git commit -m "Trial engine: frozen protocol, hashed inputs, separate evaluation

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Example investigation files

**Files:**
- Create: `investigations/README.md`, `investigations/001-example/README.md`, `investigations/001-example/trial-01/README.md`, `investigations/001-example/trial-01/protocol.json`, `investigations/001-example/trial-01/compute.py`, `investigations/001-example/trial-01/result.json`

**Interfaces:**
- Consumes: `harness.trial.create/evaluate` (verified manually here; `demo` in Task 5 automates it).
- Produces: `investigations/001-example/trial-01/protocol.json` with `id: I001-01` and `inputs: ["sources/hits.csv"]`; `result.json` with `measures.m1 == 0.3`. Task 5's `demo` depends on these exact paths.

- [ ] **Step 1: Write `investigations/001-example/trial-01/protocol.json`**

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
  "affects": ["K001"],
  "inputs": ["sources/hits.csv"],
  "data_kind": "synthetic",
  "limitations": "Synthetic data written for this template. Forty hits, two searches, relevance judged by nobody. The trial shows the form of a frozen protocol, not a finding about literature search."
}
```

- [ ] **Step 2: Write `investigations/001-example/trial-01/compute.py`**

```python
"""Computes the measures for trial I001-01 from a frozen run directory and writes result.json there.

Usage: python3 investigations/001-example/trial-01/compute.py runs/local/<run-dir>
"""

import csv
import json
import sys
from pathlib import Path


def share(rows, search_id):
    hits = [r for r in rows if r["search_id"] == search_id]
    return sum(int(r["relevant"]) for r in hits) / len(hits)


def main(run_dir):
    run_dir = Path(run_dir)
    with (run_dir / "sources/hits.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    single, combined = share(rows, "single"), share(rows, "combined")
    result = {
        "measures": {"m1": round(combined - single, 4), "m_single": round(single, 4), "m_combined": round(combined, 4)},
        "note": "Computed by compute.py from the frozen copy of sources/hits.csv.",
    }
    (run_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
```

- [ ] **Step 3: Produce `result.json` by running the engine end to end, then keep a copy**

```bash
rm -rf runs/local/example-check
python3 -c "from harness.trial import create; create('investigations/001-example/trial-01/protocol.json', 'runs/local/example-check', root='.')"
python3 investigations/001-example/trial-01/compute.py runs/local/example-check
cp runs/local/example-check/result.json investigations/001-example/trial-01/result.json
python3 -c "from harness.trial import evaluate; import json; print(json.dumps(evaluate('runs/local/example-check'), indent=2))"
```

Expected: `result.json` contains `"m1": 0.3`, `"m_single": 0.45`, `"m_combined": 0.75`; evaluate prints `"outcome": "supports_hypothesis"`.

- [ ] **Step 4: Write `investigations/001-example/trial-01/README.md`**

```markdown
# I001-01: two search strings against one, on synthetic data

Status 2026-09-16: evaluated. Outcome: supports_hypothesis. Data is synthetic.

## What is tested

Whether the combined search has a share of relevant hits at least 0.15 higher than the single search. The rival is that it is equal or lower. Anything between 0.0 and 0.15 is undecided. The thresholds were written into `protocol.json` before `result.json` existed, which is the point of the exercise.

## Protocol

`protocol.json`. One input, `sources/hits.csv`, forty rows, two searches. Measure `m1` is the difference in share of relevant hits, combined minus single. `m_single` and `m_combined` are reported alongside so a reader can check the arithmetic.

## How it was run

```sh
python3 -m harness create investigations/001-example/trial-01/protocol.json --out runs/local/i001-01
python3 investigations/001-example/trial-01/compute.py runs/local/i001-01
python3 -m harness evaluate runs/local/i001-01 --write
```

`create` freezes the protocol and the input with hashes. `compute.py` reads the frozen copy and writes `result.json` into the run directory. `evaluate` checks the hashes, applies the rule and writes `evaluation.json`. `result.json` here is a copy of what `compute.py` produced, kept so the investigation README can cite it.

## Result

m_single 0.45, m_combined 0.75, m1 0.30. Outcome supports_hypothesis.

## Assessment

The outcome is exactly what the data was written to produce, so it says nothing about literature search. What it shows is the chain: a question, a rival, a rule locked before data, a frozen input, a computed result, and an evaluation nobody can change without breaking a hash. Knowledge entry K001 records the derivation with `reconsider_if` pointing at the synthetic data.

## Limitations

Synthetic. Forty hits. Relevance judged by nobody. Not a finding.
```

- [ ] **Step 5: Write `investigations/001-example/README.md`**

```markdown
# I001: Does a second search string raise the share of relevant hits?

Status 2026-09-16: one trial run on synthetic data. This investigation exists to show the form. Replace it with your own.

## The question and why it is chosen

Every researcher searches literature, so the example needs no field knowledge. The question is small enough that one trial answers it and large enough to need a rival, a measure and a rule.

## The argument chain being tested

1. A second search string widens recall (assumed, not tested here).
2. Wider recall does not have to lower precision (the thing tested).
3. If the share of relevant hits rises by at least 0.15, the second string pays for the extra screening (a threshold chosen before data; the number is a convention for the example).

## What would make us change the conclusion

- Collected data replacing the synthetic set, with relevance judged by two people.
- A difference below 0.15 on collected data: the chain breaks at link 3.
- A difference at or below 0.0: the rival holds.

## Trials

| Trial | What it tests | Status | Outcome |
|---|---|---|---|
| [I001-01](trial-01/README.md) | Difference in share of relevant hits on synthetic data | Evaluated 2026-09-16 | supports_hypothesis, m1 = 0.30 |

## Knowledge entries

- K001, `derivation`, `provisional`, `unreviewed`. Source S001 is the frozen CSV. See `knowledge/registry.json`.

## Synthesis after one trial, 2026-09-16

The form holds end to end. The content is empty by design. A real investigation would now write a second trial with collected data, register it as a new source version, and let `python3 -m harness impact S001` list what needs re-review.

## Declared interests

None. Synthetic example.
```

- [ ] **Step 6: Write `investigations/README.md`**

```markdown
# Investigations

One directory per investigation, numbered, with a README that follows `method/templates.md`. Trials live in `trial-NN/` inside the investigation. Inputs a trial reads live in `trial-NN/sources/`. Run directories are created under `runs/local/` and are not committed.

| ID | Question | Status |
|---|---|---|
| [I001](001-example/README.md) | Does a second search string raise the share of relevant hits? | Example on synthetic data. Replace it. |

Start a new one with the `new-investigation` skill or by copying the template by hand.
```

- [ ] **Step 7: Verify and commit**

Run: `python3 -m unittest discover -s tests -v` (expected OK) and `python3 -c "from harness.registry import validate_registry; print(validate_registry('.'))"` (expected `[]`).

```bash
git add investigations
git commit -m "Example investigation I001 with one frozen trial on synthetic data

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: CLI with demo

**Files:**
- Create: `harness/__main__.py`, `tests/test_cli.py`

**Interfaces:**
- Consumes: `registry.validate_registry, build_index, context, impact`; `trial.create, evaluate`; `common.ContractError, atomic_json`.
- Produces: `python3 -m harness {validate,index,context,impact,create,evaluate,demo}`; `harness.__main__.main(argv) -> int`; `ROOT` = repo root.

- [ ] **Step 1: Write failing tests `tests/test_cli.py`**

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


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "run"

    def test_validate_and_index(self):
        code, out, _ = run(["validate"])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["valid"])
        code, out, _ = run(["index"])
        self.assertEqual(code, 0)
        self.assertIn("K001", out)

    def test_context_and_impact(self):
        code, out, _ = run(["context", "K001", "--audience", "public"])
        self.assertEqual(code, 0)
        self.assertEqual({r["id"] for r in json.loads(out)["records"]}, {"K001", "S001"})
        code, out, _ = run(["impact", "S001", "--as-of", "2026-09-16"])
        self.assertEqual(code, 0)
        self.assertIn("K001", json.loads(out)["affected"]["claims"])
        code, _, err = run(["impact", "NOPE"])
        self.assertEqual(code, 2)
        self.assertIn("Unknown", err)

    def test_create_and_evaluate(self):
        code, out, _ = run(["create", str(ROOT / "investigations/001-example/trial-01/protocol.json"), "--out", str(self.out)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["status"], "frozen")
        code, _, err = run(["evaluate", str(self.out)])
        self.assertEqual(code, 2)
        self.assertIn("result.json", err)
        shutil.copyfile(ROOT / "investigations/001-example/trial-01/result.json", self.out / "result.json")
        code, out, _ = run(["evaluate", str(self.out), "--write"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["outcome"], "supports_hypothesis")
        self.assertTrue((self.out / "evaluation.json").exists())

    def test_demo(self):
        code, out, _ = run(["demo", "--out", str(self.out)])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["outcome"], "supports_hypothesis")
        self.assertTrue((self.out / "evaluation.json").exists())
        code, _, _ = run(["demo", "--out", str(self.out)])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m unittest tests.test_cli -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.__main__'`

- [ ] **Step 3: Write `harness/__main__.py`**

```python
"""CLI for the knowledge register and frozen trials."""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from .common import ContractError, atomic_json
from .registry import build_index, context, impact, validate_registry
from .trial import create, evaluate

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_TRIAL = ROOT / "investigations/001-example/trial-01"


def emit(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m harness", description="Research harness: knowledge register and frozen trials with separate evaluation.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="Check knowledge chains and preserved source excerpts")
    sub.add_parser("index", help="Print a readable index of the register to stdout")
    p = sub.add_parser("context", help="Build a source-bound context pack with a selection log")
    p.add_argument("ids", nargs="+")
    p.add_argument("--audience", choices=("internal", "public"), default="internal")
    p.add_argument("--sources-only", action="store_true")
    p = sub.add_parser("impact", help="Propose re-review when sources change or review dates pass")
    p.add_argument("ids", nargs="*")
    p.add_argument("--as-of", default=None, help="YYYY-MM-DD; today if omitted")
    p = sub.add_parser("create", help="Freeze a trial protocol and its inputs into a run directory")
    p.add_argument("protocol", type=Path)
    p.add_argument("--out", required=True, type=Path)
    p = sub.add_parser("evaluate", help="Apply the frozen interpretation rule to result.json; no model calls")
    p.add_argument("folder", type=Path)
    p.add_argument("--write", action="store_true", help="Save evaluation.json in the run directory")
    p = sub.add_parser("demo", help="Run the example trial end to end")
    p.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            errors = validate_registry(ROOT)
            emit({"valid": not errors, "errors": errors})
            return 2 if errors else 0
        if args.command == "index":
            print(build_index(ROOT))
        elif args.command == "context":
            emit(context(ROOT, args.ids, args.audience, args.sources_only))
        elif args.command == "impact":
            emit(impact(ROOT, args.ids, args.as_of))
        elif args.command == "create":
            emit(create(args.protocol, args.out, root=ROOT))
        elif args.command == "evaluate":
            result = evaluate(args.folder)
            if args.write:
                atomic_json(args.folder / "evaluation.json", result)
            emit(result)
        elif args.command == "demo":
            folder = args.out or ROOT / "runs/local" / datetime.now().strftime("demo-%Y%m%d-%H%M%S-%f")
            create(EXAMPLE_TRIAL / "protocol.json", folder, root=ROOT)
            shutil.copyfile(EXAMPLE_TRIAL / "result.json", folder / "result.json")
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

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -v`
Expected: all tests OK (3 common + 18 registry + 9 trial + 4 cli = 34)

- [ ] **Step 5: Run the three commands a new user runs**

```bash
python3 -m harness validate
python3 -m harness demo
python3 -m unittest discover -s tests
```

Expected: `"valid": true`; demo prints `"outcome": "supports_hypothesis"`; tests OK. Then `rm -rf runs/local` (it is gitignored anyway).

- [ ] **Step 6: Commit**

```bash
git add harness/__main__.py tests/test_cli.py
git commit -m "CLI: validate, index, context, impact, create, evaluate, demo

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Method, templates, red team, knowledge README, decision log

**Files:**
- Create: `method/README.md`, `method/templates.md`, `method/red-team.md`, `knowledge/README.md`, `knowledge/INDEX.md` (generated), `DECISIONS.md`

**Interfaces:**
- Produces: the ten ground rules by number (AGENTS.md and the skills reference them by number), the close-out check (the `close-out` skill executes it step by step).

- [ ] **Step 1: Write `method/README.md`**

```markdown
# Method

The engine of this repo. An investigation answers one question through trials whose measures were locked before data, and feeds what it learns into a register where every claim points at the excerpt it rests on. The method is field-neutral: it says nothing about your subject and everything about how a claim earns its place.

Taken from `framtidens-arbetssatt`, where it was extracted from seven runs and sharpened by what each run found missing. The rules below are the ones that survived being general.

## Ground rules

1. **Blank sheet.** Start from the question, not from the literature you already like, the method you already know or the result you already expect.
2. **The rival is written before evidence is gathered.** Every investigation states what would be true if the hypothesis is wrong, in a form that data could support. A rival that no data could support is a straw man.
3. **Measures and the interpretation rule are locked before data.** The protocol names the measure, the threshold that supports the hypothesis, and the threshold that supports the rival. Values between are undecided. `python3 -m harness create` freezes the protocol with a hash so this cannot be revised afterwards without it showing.
4. **Evidence grade is declared.** Published and peer-reviewed material first, then grey literature and reports, then your own notes and transcripts, then your own experience. Each claim in the register names which it rests on. Own experience of the thing under study is the weakest grade, and weakest of all when the conclusion would benefit you.
5. **Each claim rests on a preserved excerpt.** The register stores a hashed snapshot of the source and the line range the claim reads. A claim without an excerpt is not a claim, it is a note.
6. **Knowledge status and review status are separate.** A claim can be `provisional` and `reviewed`, or `bounded_support` and `unreviewed`. The first says how much the evidence carries; the second says whether anyone other than the author has checked. Neither is set automatically.
7. **Red team before synthesis.** Before an investigation writes its synthesis, a reader who did not write it attacks it along the lines in `method/red-team.md`. The synthesis records what the attack found and what changed.
8. **Interests are declared in the investigation README.** Funder, supervisor's position, your own prior publications on the question, anything a reader would want to know before trusting the conclusion. Declaring is not distancing: a conflicted source may still be used, but it is labelled and it is not the only leg the claim stands on.
9. **No rule changes without an entry in `DECISIONS.md`.** A method rule, a template or a register convention that changed during an investigation is written into the decision log and into the file that carries the rule. A run that changed a rule without writing it down is invisible until the next run reads the wrong rule.
10. **Honest limits in every synthesis.** What is derived, what is observed, what is measured, and what the data kind was: synthetic, collected or secondary.

## Close-out check

An investigation is not finished when the synthesis is written. It is finished when the documentation reflects the decisions the investigation took. Five checks, in this order, before you tell anyone it is done.

1. **Write the decisions into `DECISIONS.md`.** Every decision that changed the repo's direction, method, scope or what leaves the repo. Date, what was decided, why, which files it landed in. The content of the investigation itself does not go there; it stays in the investigation's own files.
2. **Check that each decision stands in the document that carries the rule**, not only in the log. A new ground rule goes into this file and into the skills if it changes how an investigation is driven. A new template goes into `method/templates.md`.
3. **Run the harness.** `python3 -m harness validate` must pass. `python3 -m harness index > knowledge/INDEX.md` regenerates the index. `python3 -m unittest discover -s tests` must pass.
4. **Check the investigation index** in `investigations/README.md`: status and outcome match the investigation README.
5. **Ask the feedback question.** Did the method, a template or the harness get in the way anywhere? If so, file it upstream: see `CONTRIBUTING.md`.

Report deviations together with what was corrected.

## Files in method/

- `README.md`: this file.
- `templates.md`: investigation README, trial README, knowledge entry.
- `red-team.md`: five lines of attack against your own synthesis.
```

- [ ] **Step 2: Write `method/templates.md`**

````markdown
# Templates

Copy the headings. Keep the order so investigations can be compared line by line.

---

## Investigation README (`investigations/NNN-<slug>/README.md`)

```
# INNN: <question as one sentence>

Status <date>: <planned | trials running | synthesised>.

## The question and why it is chosen
<Two or three sentences. What it would change if answered. Why now.>

## The argument chain being tested
<Numbered links. Each link is a claim that could fail on its own. Mark which link each trial tests.>

## What would make us change the conclusion
<Concrete observations, not attitudes. "A difference below 0.15 on collected data", not "if the evidence is weak".>

## Trials
| Trial | What it tests | Status | Outcome |
|---|---|---|---|

## Knowledge entries
<IDs in knowledge/registry.json that this investigation created or changed, with type, status and review status.>

## Synthesis after N trials, <date>
<What holds, what fell, what is undecided. What the red team found and what changed because of it. Next trial or why none.>

## Declared interests
<Funder, supervisor, own prior position. "None" is an answer only if it is true.>
```

---

## Trial README (`investigations/NNN-<slug>/trial-NN/README.md`)

```
# INNN-NN: <what is tested, one line>

Status <date>: <protocol written | frozen | evaluated>. Outcome: <supports_hypothesis | supports_rival | undecided | not yet>. Data kind: <synthetic | collected | secondary>.

## What is tested
<Hypothesis and rival in one paragraph. The thresholds and why those numbers.>

## Protocol
<`protocol.json`. Inputs, measures, the interpretation rule.>

## How it was run
<The three commands, plus whatever script computed result.json.>

## Result
<The measures and the outcome.>

## Assessment
<What the outcome means for the argument chain. Which knowledge entry changes.>

## Limitations
<Sample, data kind, what the measure does not capture.>
```

---

## Knowledge entry (`knowledge/registry.json`)

A source:

```json
{
  "id": "S<NNN>",
  "family": "S<NNN>",
  "version": "<YYYY-MM-DD>-v1",
  "snapshot": "knowledge/snapshots/<sha256>.txt",
  "sha256": "<sha256 of the snapshot file>",
  "origin": "<path in the repo or a citation>",
  "anchor": "L<start>-L<end>",
  "kind": "<literature | transcript | empirical_report | dataset | model_trial | analysis | note>",
  "audience": "<public | internal>",
  "access": "<how you got it and whether it may be quoted>",
  "depends_on": []
}
```

A claim:

```json
{
  "id": "K<NNN>",
  "statement": "<one sentence>",
  "type": "<observation | hypothesis | interpretation | derivation | model_result | dated_analysis>",
  "status": "<open | provisional | bounded_support | weakened | refuted | superseded>",
  "assertion_mode": "<descriptive | conditional | normative>",
  "audience": "<public | internal>",
  "scope": "<where it holds>",
  "reconsider_if": "<what observation would reopen it>",
  "depends_on": ["<other claim IDs>"],
  "evidence": [{"source": "S<NNN>", "anchor": "L<start>-L<end>", "relation": "<supports | opposes | limits | origin>", "reading": "<what the excerpt says, in your words>"}],
  "history": [{"date": "<YYYY-MM-DD>", "status": "<status>", "reason": "<why>"}],
  "version": 1,
  "review_status": "<unreviewed | reviewed | needs_review>",
  "review_history": [{"date": "<YYYY-MM-DD>", "status": "<review status>", "reason": "<who checked, or why nobody has>"}]
}
```

Rules the validator enforces: `anchor` in evidence must equal the source's anchor; an `observation` may only be supported by a `transcript` or `empirical_report`; a `model_result` only by a `model_trial`; an `observation` cannot be `normative`; every claim needs at least one dependency or evidence; history dates ascend and the last entry matches the current status.
````

- [ ] **Step 3: Write `method/red-team.md`**

````markdown
# Red team

Run before the synthesis of every investigation, by a reader who did not write it. With an agent: start a fresh session or a subagent, give it read access only, and paste the prompt below. Replace `<investigation>`.

```
Working directory: this repo. Change no files.

Role: red team. Your job is to break the investigation, not to confirm it.

Read investigations/<investigation>/README.md and every trial-NN/README.md and protocol.json under it. Read method/README.md. Read the knowledge entries the investigation cites in knowledge/registry.json, including the snapshot each one points at.

Attack along five lines:

1. Convenient conclusion. Would this conclusion be comfortable for the author, the funder or the supervisor? Look for bias in both directions: a conclusion that flatters the hypothesis and a conclusion that looks self-critical, since the second is the cheapest way to appear objective.

2. Selection of evidence. Which sources would a hostile reviewer cite that the investigation does not? Which cited excerpt, read in full, says less than the reading claims? Check the anchor against the snapshot.

3. The measure. Does the measure in the protocol measure the thing the argument chain claims? Could the measure move for a reason unrelated to the hypothesis? Were the thresholds justified or picked to be passable?

4. The rival. Is it a straw man? Write the strongest rival a competent opponent would put forward, and check whether the trial could distinguish it from the hypothesis.

5. Generalisation. Where does the synthesis reach beyond the sample, the data kind, the setting or the period? Which limitation in the trial README is missing from the synthesis?

Deliver a report in Markdown of at most 800 words. Objections ordered by severity. For each: what it hits (file and section), why, and what resolves it: change the claim, add a trial, add a limitation, or mark as undecided. No politeness. Return the report as your answer.
```

Write what the red team found and what changed into the investigation's synthesis, dated and marked "after red team".
````

- [ ] **Step 4: Write `knowledge/README.md`**

````markdown
# Knowledge register

`registry.json` holds four lists: `sources`, `claims`, `documents`, `uses`. Every claim points at the excerpt it rests on; every excerpt is a hashed snapshot in `snapshots/`. `INDEX.md` is generated. The validator checks declarations, never truth.

## Add a source

1. Put the excerpt you will cite in a text file. For a paper, the paragraphs you read, with a citation line at the top. For a dataset, the file itself. For an interview, the de-identified transcript passage.
2. Hash it and move it into place:

```sh
SHA=$(shasum -a 256 excerpt.txt | cut -d' ' -f1)
mv excerpt.txt knowledge/snapshots/$SHA.txt
```

3. Add a source entry with `snapshot`, `sha256`, `anchor` (the line range, `L1-L<n>`), `kind`, `audience`, `access`. Template in `method/templates.md`.
4. `python3 -m harness validate`.

Source kinds: `literature` (published work), `transcript` (interview or observation record), `empirical_report` (a study's reported results), `dataset`, `model_trial` (output of a model run you made), `analysis` (your own or someone else's derived analysis), `note` (unverified working note).

## Add a claim

Template in `method/templates.md`. `type` says what kind of thing it is; `status` says how much the evidence carries; `review_status` says whether anyone else checked. `reconsider_if` is mandatory and concrete.

## When a source changes

Add a new source entry with a new `version` and the same `family`; keep the old one. Then:

```sh
python3 -m harness impact S001
```

It lists every claim, document and use that rests on the source, directly or through other claims, as proposals for review. Nothing changes status automatically.

## Audience

`internal` on a source or claim keeps it, and everything that depends on it, out of `python3 -m harness context --audience public`. Use it for anything with a named person, a confidential document, or data you may use but not quote.

## Personal data

Never put a transcript with identifiable people into `snapshots/` until de-identification has been decided and done. The register is committed to git; git remembers.
````

- [ ] **Step 5: Generate `knowledge/INDEX.md` and write `DECISIONS.md`**

```bash
python3 -m harness index > knowledge/INDEX.md
```

`DECISIONS.md`:

```markdown
# Decision log

The repo's decisions in date order: what was decided, why, and what in the documentation changed as a result. The log exists because decisions otherwise live only in the file they happened to change, and then nobody can see whether the documentation reflects them.

A decision belongs here when it changes the repo's direction, method, scope, or what leaves the repo. The content of a single investigation does not; that stays in the investigation's own files.

The log is filled in at every close-out, see `method/README.md`.

## 2026-09-16

**1. The template is created from `framtidens-arbetssatt`, form only.** The model repo's registry validator, decision log, investigation form and close-out check are general; its domain method, channel simulator and subject content are not.
Landed in: `harness/registry.py`, `method/`, `DECISIONS.md`, `investigations/001-example/`.

**2. Trials are a frozen protocol plus a separately evaluated result, with no model adapter.** A researcher who wants a model inside a trial writes a script that puts `result.json` into the frozen directory. The harness never calls a model.
Landed in: `harness/trial.py`, `method/README.md` rule 3.

**3. Code is MIT, text is CC BY 4.0.** So the harness can be reused in any project and the method can be adapted with attribution.
Landed in: `LICENSE`, `LICENSE-CONTENT`, `README.md`.

**4. Feedback goes upstream through issues, and the close-out check asks for it.** The template improves from use only if the loop runs without anyone remembering it.
Landed in: `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/`, `method/README.md` close-out step 5, `.agents/skills/close-out/`.
```

- [ ] **Step 6: Verify and commit**

Run: `python3 -m harness validate` (expected valid) and `grep -c '^[0-9]*\. \*\*' method/README.md` (expected 10).

```bash
git add method knowledge DECISIONS.md
git commit -m "Method: ten ground rules, close-out check, templates, red team, register guide, decision log

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: AGENTS.md, CLAUDE.md and the two Codex skills

**Files:**
- Create: `AGENTS.md`, `CLAUDE.md`, `.agents/skills/new-investigation/SKILL.md`, `.agents/skills/close-out/SKILL.md`

**Interfaces:**
- Consumes: rule numbers from `method/README.md`, close-out steps 1 to 5, CLI commands from Task 5.
- Produces: nothing code-level. Skill names `new-investigation` and `close-out` are referenced by README and CONTRIBUTING.

- [ ] **Step 1: Write `AGENTS.md`**

```markdown
# Instructions for agents

You are working in a research repo. The researcher owns the questions, the conclusions and the interests declared. You carry the work between those points.

## Before anything else

Read `method/README.md`. The ten ground rules and the close-out check are not optional. Read `method/templates.md` before creating an investigation or a trial. Read `knowledge/README.md` before touching `knowledge/registry.json`.

## How to work

- Drive the work without asking permission at every step. Stop and ask when a choice would change the direction of an investigation: the question, the rival, a threshold, what counts as evidence.
- Write the rival and lock the measures before you look at data. If the researcher wants to look first, say that rule 3 is about to be broken and let them decide.
- Never edit a frozen run directory under `runs/`. If a protocol is wrong, create a new run.
- Never call a paid model or an external API from a trial unless the researcher has said so in this session. The harness itself makes no calls.
- Never put identifiable personal data into `knowledge/snapshots/` or anywhere committed. Interview material goes in only after the researcher has decided on de-identification. Example data is always synthetic and labelled `data_kind: synthetic`.
- Every claim you add to the register points at a preserved excerpt and has a concrete `reconsider_if`.
- When you change a rule, a template or a register convention, write it into `DECISIONS.md` and into the file that carries the rule, in the same commit.

## When an investigation closes

Run the close-out check in `method/README.md`, or invoke the `close-out` skill. The last step asks whether the method, the templates or the harness got in the way. If they did, draft an issue for the upstream template; see `CONTRIBUTING.md`.

## Language

Write in the language the researcher writes in. Keep file names, JSON keys and commands in English so the harness and the templates keep working.
```

- [ ] **Step 2: Write `CLAUDE.md`**

```markdown
Read `AGENTS.md`. It is the instruction file for every agent in this repo.
```

- [ ] **Step 3: Write `.agents/skills/new-investigation/SKILL.md`**

```markdown
---
name: new-investigation
description: Start a new investigation in this research repo. Use when the researcher has a question to test and wants the directory, README, first trial protocol and register entries set up according to method/templates.md. Do not use for editing an existing investigation.
---

# New investigation

You create the skeleton for one investigation with one trial, following `method/templates.md`. You do not gather data or write conclusions.

## Steps

1. Read `method/README.md`, `method/templates.md` and `investigations/README.md`.
2. Find the next number: the highest `NNN` in `investigations/` plus one. Ask the researcher for a slug if the question does not give an obvious one.
3. Ask, one at a time, and write the answer before the next question:
   - The question, as one sentence.
   - The hypothesis: what would be true if the question's answer is yes.
   - The rival: what would be true if the answer is no, in a form data could support. If the researcher's rival is "the hypothesis is false", push once for something a trial could distinguish.
   - The first trial: what it measures, in what unit, and the two thresholds. If the researcher does not have thresholds yet, write `undecided` bands wide and note in the trial README that the thresholds were set before data with weak justification.
   - Declared interests: funder, supervisor's position, own prior publications. "None" only if true.
4. Create `investigations/NNN-<slug>/README.md` from the investigation template with those answers. Status `planned`.
5. Create `investigations/NNN-<slug>/trial-01/protocol.json` with `id: INNN-01`, `investigation: INNN`, the measures and the interpretation rule. `inputs` lists the files the trial will read under `trial-01/sources/`; create the directory with a `.gitkeep` if no inputs exist yet. `affects` is empty until a claim exists. `data_kind` is what the researcher says it will be.
6. Create `trial-01/README.md` from the trial template, status `protocol written`.
7. Add a row to `investigations/README.md`.
8. Run `python3 -m harness validate`. Do not run `create` yet; freezing happens when the inputs are in place.
9. Tell the researcher what was created and that the next step is to put the input files in `trial-01/sources/` and run `python3 -m harness create investigations/NNN-<slug>/trial-01/protocol.json --out runs/local/iNNN-01`.
```

- [ ] **Step 4: Write `.agents/skills/close-out/SKILL.md`**

```markdown
---
name: close-out
description: Run the close-out check when an investigation or a working session ends. Use when the researcher says an investigation is done, wants to wrap up, or before anything is shared outside the repo. Ends with the feedback question about the template.
---

# Close-out

You run the five checks in `method/README.md`, section "Close-out check", in order, and report deviations together with what you corrected.

## Steps

1. **Decisions.** Read the investigation README and the git log since the investigation started. List every decision that changed the repo's direction, method, scope or what leaves the repo. For each, add an entry to `DECISIONS.md` under today's date: what, why, which files it landed in. If there are none, say so.
2. **Carrier documents.** For each decision, open the file that carries the rule (`method/README.md`, `method/templates.md`, `knowledge/README.md`, a skill) and confirm the change is there. Fix it if it is not.
3. **Harness.** Run, in order:
   ```sh
   python3 -m harness validate
   python3 -m harness index > knowledge/INDEX.md
   python3 -m unittest discover -s tests
   ```
   Stop and report if any fails. Do not mark the investigation closed with a failing validate.
4. **Investigation index.** Compare the row in `investigations/README.md` with the investigation README: status, outcome. Fix the row.
5. **Feedback.** Ask the researcher: "Did the method, a template or the harness get in the way anywhere in this investigation? A rule that did not fit, a template heading you skipped, a command that did the wrong thing?" If yes, draft an issue using `.github/ISSUE_TEMPLATE/method-gap.md`, show it, and if the researcher agrees offer:
   ```sh
   gh issue create -R fabian-von-tiedemann/research-repo-template --title "<title>" --body-file <draft>
   ```
   Never file without the researcher seeing the text. Never include subject content or personal data in the issue.

Report: decisions written, corrections made, test results, and whether feedback was sent.
```

- [ ] **Step 5: Verify frontmatter and commit**

Run: `head -4 .agents/skills/*/SKILL.md` and confirm each starts with `---`, has `name:` and `description:`.

```bash
git add AGENTS.md CLAUDE.md .agents
git commit -m "Agent instructions and Codex skills: new-investigation, close-out

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Feedback loop files

**Files:**
- Create: `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/method-gap.md`, `.github/ISSUE_TEMPLATE/template-improvement.md`, `.github/ISSUE_TEMPLATE/config.yml`

- [ ] **Step 1: Write `CONTRIBUTING.md`**

```markdown
# Improving the template

This template gets better only through use. If it got in your way, that is the most useful thing you can send back.

## What to send

- **Method gaps.** A ground rule that did not fit your field, a close-out step that made no sense, a template heading you always skip or always add.
- **Harness friction.** A command that did the wrong thing, a validator error you could not understand, a protocol shape the engine could not express.
- **New trial patterns.** A kind of trial you ran that the protocol format handled badly, with a sketch of what would have fit.
- **Fixes.** Pull requests for any of the above are welcome. Keep the standard-library-only rule and keep tests passing.

## What not to send

- Your subject content. The template is field-neutral and stays that way.
- Personal data of any kind, including from example files.
- Requests for a model adapter inside the harness. The design keeps model calls outside: a script writes `result.json` into a frozen run. See `DECISIONS.md` entry 2. If you think that is wrong, open a method-gap issue and argue it.

## How

1. Open an issue on `fabian-von-tiedemann/research-repo-template` using the `Method gap` or `Template improvement` template.
2. The `close-out` skill asks the feedback question at the end of every investigation and drafts the issue for you. You still read it before it is filed.
3. For a fix, fork, branch, run `python3 -m unittest discover -s tests`, open a pull request. Describe which rule or command the change affects.

## Licence of contributions

Code contributions are accepted under MIT. Text contributions under CC BY 4.0. By opening a pull request you agree to that.
```

- [ ] **Step 2: Write `.github/ISSUE_TEMPLATE/method-gap.md`**

```markdown
---
name: Method gap
about: A rule, template or harness behaviour that got in the way of real research work
title: "Method gap: "
labels: method-gap
---

## Which rule, template or command

<!-- e.g. method/README.md rule 3, the trial README template, `python3 -m harness evaluate` -->

## What you were doing

<!-- The kind of investigation and trial, without subject content or personal data. -->

## What went wrong

<!-- What the rule or tool demanded, and why it did not fit. -->

## What you did instead

<!-- The workaround, and whether it should become the rule. -->
```

- [ ] **Step 3: Write `.github/ISSUE_TEMPLATE/template-improvement.md`**

```markdown
---
name: Template improvement
about: A change to the template that would have helped from the start
title: "Improvement: "
labels: improvement
---

## What to change

<!-- File and section, or command. -->

## Why

<!-- What it would have saved you, or what it would have prevented. -->

## Sketch

<!-- If you have one: the new wording, the new field, the new flag. -->
```

- [ ] **Step 4: Write `.github/ISSUE_TEMPLATE/config.yml`**

```yaml
blank_issues_enabled: true
```

- [ ] **Step 5: Commit**

```bash
git add CONTRIBUTING.md .github
git commit -m "Feedback loop: contributing guide and issue templates

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# Research repo template

A repository shape for research done with an agent at your side. It carries a method, not a subject: questions with an argument chain, trials whose measures were locked before data, a knowledge register where every claim points at the excerpt it rests on, a decision log, and rules the agent reads before it does anything.

Built for doctoral work first. The ambition is a template more researchers adopt and improve. Everything you find lacking is something to send back; see [Improving the template](#improving-the-template).

## Who it is for

- **Doctoral and master's work.** Literature trials, interview analysis, data trials, with a traceable path from source excerpt to chapter.
- **Research groups** that want several people and agents working in one knowledge state without losing track of what rests on what.
- **Policy analysis and evaluation** where a revised source must trigger re-review of everything built on it: `python3 -m harness impact S001` lists it.
- **Consultancy and product research** where interests must be declared and a convenient conclusion must be attacked before it is published.
- **Teaching research method.** The repo is a runnable version of "state the rival and lock the measure before you look at data".

## First hour

1. Click **Use this template** on GitHub, name your repo, clone it.
2. Check the harness runs:
   ```sh
   python3 -m harness validate
   python3 -m harness demo
   python3 -m unittest discover -s tests
   ```
   Python 3.10 or later, standard library only. `demo` freezes the example trial, evaluates it and prints `supports_hypothesis`.
3. Read `method/README.md`. Ten rules and a close-out check. Fifteen minutes.
4. Start Codex in the repo. It reads `AGENTS.md` first. Type `$new-investigation` and answer its questions: your question, your hypothesis, your rival, your first measure, your interests.
5. Delete `investigations/001-example/` and its entries in `knowledge/registry.json` once your own first investigation exists. Run `python3 -m harness validate` afterwards.

## The loop

```
question ──▶ rival ──▶ protocol frozen ──▶ data in ──▶ result.json ──▶ evaluate ──▶ knowledge entry ──▶ decision
   ▲                  (measures, thresholds)                            (hash-checked)                      │
   └──────────────────────────── red team before synthesis ◀──────────────────────────────────────────────┘
```

- **Investigation:** one question, an argument chain, what would change the conclusion, trials, synthesis, declared interests. `investigations/NNN-<slug>/README.md`.
- **Trial:** `protocol.json` names the measures and an interpretation rule with two thresholds. `python3 -m harness create` freezes it and the inputs with hashes. A script, or you, writes `result.json` into the run directory. `python3 -m harness evaluate` checks the hashes and applies the rule. Outcome is `supports_hypothesis`, `supports_rival` or `undecided`.
- **Knowledge:** `knowledge/registry.json`. Sources are hashed excerpts. Claims point at excerpts, carry a status, a review status and a `reconsider_if`. `validate` enforces the shape; `impact` follows dependencies when a source changes; `context` builds a source-bound pack for an agent, with an audience filter that keeps internal material out.
- **Decisions:** `DECISIONS.md`. Every rule change, in the log and in the file that carries the rule, same commit.

The worked example is [I001](investigations/001-example/README.md): synthetic data, one trial, one claim, so you can see every file the loop produces.

## Structure

| Path | What |
|---|---|
| `AGENTS.md` | Rules every agent reads at start. `CLAUDE.md` points here. |
| `method/` | Ground rules, close-out check, templates, red team prompt. |
| `investigations/` | One directory per question. Trials inside. |
| `knowledge/` | Register, hashed snapshots, generated index, how-to. |
| `harness/` | `registry.py` (validator, context, impact, index) and `trial.py` (create, evaluate). `python3 -m harness --help`. |
| `tests/` | `python3 -m unittest discover -s tests`. |
| `runs/local/` | Frozen run directories. Gitignored. |
| `.agents/skills/` | Codex skills: `new-investigation`, `close-out`. |
| `DECISIONS.md` | Decision log. |
| `CONTRIBUTING.md` | How to send feedback upstream. |

## Commands

```sh
python3 -m harness validate                      # check the register and snapshots
python3 -m harness index > knowledge/INDEX.md    # regenerate the readable index
python3 -m harness context K001 --audience public
python3 -m harness impact S001 --as-of 2026-09-16
python3 -m harness create <protocol.json> --out runs/local/<name>
python3 -m harness evaluate runs/local/<name> --write
python3 -m harness demo
```

Exit codes: 0 done, 2 invalid input or contract, 3 interrupted. A negative or undecided trial outcome is exit 0; it is a result, not an error.

## Improving the template

Three ways, all in `CONTRIBUTING.md`:

1. Open a **Method gap** or **Template improvement** issue on `fabian-von-tiedemann/research-repo-template`.
2. Let the `close-out` skill ask you at the end of each investigation; it drafts the issue.
3. Send a pull request.

## Licence

Code (`harness/`, `tests/`, scripts): MIT, see `LICENSE`. Text (method, templates, examples, this file): CC BY 4.0, see `LICENSE-CONTENT`.

## Origin

The form comes from [framtidens-arbetssatt](https://github.com/digitalist-se/framtidens-arbetssatt), a research repo on future ways of working, where the register validator, the decision log and the close-out check were extracted from seven domain runs. The subject content stayed there.
```

- [ ] **Step 2: Check every relative link in README resolves**

```bash
grep -o '](\([^)h][^)]*\))' README.md | sed 's/](\(.*\))/\1/' | sed 's/#.*//' | sort -u | while read f; do [ -e "$f" ] || echo "MISSING: $f"; done
```

Expected: no output.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "README: who it is for, first hour, the loop, structure, commands, feedback, licence

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: Message to Amanda, clean-clone verification, publish as template

**Files:**
- Create: `docs/message-to-amanda.md`

- [ ] **Step 1: Write `docs/message-to-amanda.md`** (Swedish, the only Swedish file)

```markdown
# Till Amanda

Hej! Här är repot jag lovade. Det är en mall, inte ett färdigt projekt: en form för hur frågor, prov, källor och beslut hänger ihop, med stöd för att Codex kan bära arbetet mellan punkterna.

**Så här kommer du igång, tar ungefär en timme:**

1. Gå till https://github.com/fabian-von-tiedemann/research-repo-template och klicka **Use this template**. Döp ditt repo och klona det.
2. Kör i repots rot:
   ```sh
   python3 -m harness validate
   python3 -m harness demo
   python3 -m unittest discover -s tests
   ```
   Allt ska gå igenom. `demo` kör ett exempelprov från fryst protokoll till utvärdering.
3. Läs `method/README.md`. Tio regler och en avslutskontroll. Femton minuter.
4. Starta Codex i repot. Det läser `AGENTS.md` först. Skriv `$new-investigation` och svara på frågorna: din fråga, din hypotes, din rival, ditt första mått, dina intressen.
5. När din första undersökning finns: ta bort `investigations/001-example/` och dess poster i `knowledge/registry.json`, kör `validate` igen.

**Två saker jag vill be dig om:**

- Repot är på engelska men du skriver dina egna texter på vilket språk du vill. Codex följer ditt språk.
- När något i metoden, mallarna eller verktyget är i vägen, skicka det tillbaka som ett issue. `close-out`-skillen frågar dig om det varje gång en undersökning avslutas och skriver utkastet. Det är så mallen blir bättre för nästa person.

Fråga när du kör fast. Hälsningar, Fabian
```

- [ ] **Step 2: Commit the message**

```bash
git add docs/message-to-amanda.md
git commit -m "Message to Amanda

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 3: Verify from a clean clone**

```bash
rm -rf /tmp/rrt-check && git clone -q /Users/fabianvontiedemann/Developer/forskningsrepo /tmp/rrt-check && cd /tmp/rrt-check && python3 -m harness validate && python3 -m harness demo && python3 -m unittest discover -s tests && git status --porcelain && cd - && rm -rf /tmp/rrt-check
```

Expected: `"valid": true`, demo outcome `supports_hypothesis`, tests OK, `git status --porcelain` empty (demo output is gitignored). Also check no em-dashes crept in: `grep -rn '—' --include='*.md' --include='*.py' --include='*.json' . | grep -v '^./.git/'` should print nothing.

- [ ] **Step 4: Publish**

```bash
gh repo create fabian-von-tiedemann/research-repo-template --public --source . --push --description "A repo shape for research with an agent at your side: frozen trials, hashed knowledge register, decision log, agent rules. Field-neutral."
gh api -X PATCH repos/fabian-von-tiedemann/research-repo-template -f is_template=true
gh repo view fabian-von-tiedemann/research-repo-template --json isTemplate,url
```

Expected: `"isTemplate": true` and the URL.

- [ ] **Step 5: Report**

Give the user the URL, the three commands, the path to `docs/message-to-amanda.md`, and the test count.

---

## Self-review

**Spec coverage.** Structure table in spec: every file has a task (AGENTS.md, CLAUDE.md, README, DECISIONS.md, LICENSE, LICENSE-CONTENT, CONTRIBUTING.md, two issue templates, method/ three files, investigations/ four files plus protocol/compute/result/csv, knowledge/ four items, harness/ four modules, tests/ four files, two skills, .gitignore, docs). Registry changes (CLAIM_TYPES, path, index text, dataset in raw kinds): Task 2. Trial protocol fields and semantics: Task 3 matches the spec's JSON. Exit codes: Task 5. Feedback loop three mechanisms: Tasks 6 (close-out step 5), 7 (skill), 8 (files). Licensing: Tasks 1 and 9. Delivery steps: Task 10. Out of scope items are absent.

**Placeholders.** `<SHA>` in Task 2 is a deliberate substitution instruction with the command that produces it. `<NNN>`, `<slug>`, `<date>` inside template files are template content, not plan gaps.

**Type consistency.** `create(protocol_path, out_dir, root=None)` used in Tasks 3, 4, 5. `evaluate(run_dir)` returns dict with `outcome`, `measures`, `limitations`, `manifest_sha256`, `data_kind`, `note` in Task 3; Task 5's demo and tests read `outcome`. `validate_registry(root)` returns list; Task 5 uses `not errors`. Protocol `id: I001-01`, `inputs: ["sources/hits.csv"]`, `affects: ["K001"]` consistent between Task 2's register (K001 exists), Task 4 and Task 5's `EXAMPLE_TRIAL`. Skill names `new-investigation` and `close-out` consistent across Tasks 7, 8, 9, 10.
