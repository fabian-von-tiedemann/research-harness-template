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
        if Path(rel).name in RESERVED:
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
