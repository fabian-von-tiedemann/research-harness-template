# Pre-registered study I001-01

Investigation I001. Data kind: simulated. Frozen 2026-09-16T10:03:17+00:00.

**Committed:** 4818089428b15a42d6bae5bdcb8bb2d5e8cae74b 2026-09-16T12:03:37+02:00

## Question

Does a literature search with two search strings yield a higher share of relevant hits than a search with one?

## Hypothesis

The combined search has a share of relevant hits at least 0.15 higher than the single search.

## Competing hypothesis

The combined search is no better: its share of relevant hits is equal to or lower than the single search.

## Measures

- `m1`: Share of relevant hits for the combined search minus share for the single search (share)
- `m_single`: Share of relevant hits, single search (share)
- `m_combined`: Share of relevant hits, combined search (share)

## Interpretation rule

On `m1`: supports the hypothesis if >= 0.15; supports the competing hypothesis if <= 0.0; otherwise undecided.

## Limitations declared before data

Simulated data written for this template. Forty hits, two searches, relevance judged by nobody. The study shows the form of a frozen protocol, not a finding about literature search.

## Frozen files (SHA-256)

- `protocol.json`: `f85d71229294f25a4d7ae0f3e51ae699aed9d826614f990ae694854e9ba15523`
- `inputs/hits.csv`: `d8d483f386697878a74d5b122bdebe0a3c61eb105be5b50cfd7e1652414c60f7`

## Evaluation

Outcome: **supports_hypothesis**. Evaluated 2026-09-16T10:03:17+00:00.

- `m1`: 0.3
- `m_single`: 0.45
- `m_combined`: 0.75

result.json SHA-256 `96657683f36fa9c153329a718dd203cb54c526e021b5a8c35584ff738766e8d4`.
