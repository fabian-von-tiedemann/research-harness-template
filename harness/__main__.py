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
