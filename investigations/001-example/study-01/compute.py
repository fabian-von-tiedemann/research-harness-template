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
