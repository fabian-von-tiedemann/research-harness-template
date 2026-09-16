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

`affects` in the protocol is empty because K001 was created after the protocol was frozen, which is the honest order: a study is registered before it knows what it will change. Run `python3 -m harness report investigations/001-example/study-01/frozen` after committing to see the commit that serves as the pre-registration record.

## Limitations

Simulated. Forty hits. Relevance judged by nobody. Not a finding.
