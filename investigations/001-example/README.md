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
