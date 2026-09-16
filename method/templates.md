# Templates

Copy the headings. Keep the order so investigations can be compared line by line. `investigations/001-example/` is a filled-in copy of the first two.

---

## Investigation README (`investigations/NNN-<slug>/README.md`)

```
# INNN: <question as one sentence>

Status <date>: <planned | studies running | synthesised>.

## The question and why it is chosen
<Two or three sentences. What it would change if answered. Why now.>

## The argument chain being tested
<Numbered links. Each link is a claim that could fail on its own. Mark which study tests which link.>

## What would make us change the conclusion
<Concrete observations, not attitudes. "A difference below 0.15 on primary data", not "if the evidence is weak".>

## Studies
| Study | What it tests | Status | Outcome |
|---|---|---|---|

## Knowledge entries
<IDs in knowledge/registry.json this investigation created or changed, with type, status and review status.>

## Synthesis after N studies, <date>
<What holds, what fell, what is undecided. What the red team found and what changed because of it. Next study, or why none.>

## Declared interests
Funding: <funder and grant, or none>. Roles (CRediT): <who did what>. Conflicts of interest: <any, or none>. Prior position: <your own earlier published view on the question, or none>.
```

---

## Study README (`investigations/NNN-<slug>/study-NN/README.md`)

```
# INNN-NN: <what is tested, one line>

Status <date>: <protocol written | frozen | evaluated>. Outcome: <supports_hypothesis | supports_rival | undecided | descriptive | not yet>. Data kind: <simulated | primary | secondary>.

## What is tested
<Hypothesis and competing hypothesis in one paragraph. The thresholds and why those numbers. Or: exploratory, and why no confirmatory rule.>

## Protocol
<`protocol.json`. Inputs, measures, the interpretation rule.>

## How it was run
python3 -m harness create investigations/NNN-<slug>/study-NN/protocol.json --out investigations/NNN-<slug>/study-NN/frozen
<the script or manual step that wrote frozen/result.json>
python3 -m harness evaluate investigations/NNN-<slug>/study-NN/frozen --write
python3 -m harness report investigations/NNN-<slug>/study-NN/frozen --write

## Result
<The measures and the outcome.>

## Assessment
<What the outcome means for the argument chain. Which knowledge entry changes.>

## Limitations
<Sample, data kind, what the measure does not capture.>
```

Commit `frozen/` right after `create`, before any analysis. That commit is the pre-registration record.

---

## Source entry (`knowledge/registry.json`, `sources`)

`python3 -m harness snapshot <file>` prints this skeleton with the hash and anchor filled in.

```json
{
  "id": "S<NNN>",
  "family": "S<NNN>",
  "version": "<YYYY-MM-DD>-v1",
  "snapshot": "knowledge/snapshots/<sha256>.txt",
  "sha256": "<sha256 of the snapshot file>",
  "origin": "<path in the repo, DOI or citation>",
  "anchor": "L<start>-L<end>",
  "kind": "<literature | transcript | empirical_report | dataset | model_trial | analysis | note>",
  "access": "<how you obtained it and whether it may be quoted>",
  "depends_on": []
}
```

## Claim entry (`knowledge/registry.json`, `claims`)

```json
{
  "id": "K<NNN>",
  "statement": "<one sentence>",
  "type": "<observation | hypothesis | interpretation | derivation | model_result>",
  "status": "<open | provisional | bounded_support | weakened | refuted | superseded>",
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

## Document entry (`knowledge/registry.json`, `documents`)

```json
{"id": "DOC-<slug>", "path": "<chapter or report path>", "depends_on": ["K<NNN>"]}
```

What the validator enforces: the evidence anchor equals the source's anchor; an `observation` is supported only by a `transcript` or `empirical_report`; a `model_result` only by a `model_trial`; every claim has at least one dependency or piece of evidence; history dates ascend and the last entry matches the current status; snapshots match their hash; no cycles.
