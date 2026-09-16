---
name: new-investigation
description: Start a new investigation in this research repo: directory, README, first study protocol, register check. Use when the researcher has a question to test. Not for editing an existing investigation.
---

# New investigation

You create the skeleton for one investigation with one study, following `method/templates.md`. You do not gather data or write conclusions.

## Steps

1. Read `method/README.md`, `method/templates.md` and `investigations/README.md`.
2. Find the next number: the highest `NNN` in `investigations/` plus one. Ask for a slug if the question does not give an obvious one.
3. Ask one thing at a time, and write each answer down before the next question:
   - The question, as one sentence.
   - The hypothesis: what would be true if the answer is yes.
   - The competing hypothesis: what would be true if the answer is no, in a form data could support. If the researcher says "the hypothesis is false", push once for something a study could distinguish.
   - The first study: what it measures, in what unit, and the two thresholds. They must not overlap. If the researcher has no thresholds because the study is exploratory, set `exploratory: true` and `interpretation_rule: null`, and say in the study README why.
   - Data kind: `simulated`, `primary` or `secondary`.
   - Declared interests: funding, CRediT roles, conflicts of interest, prior position. "None" only if true.
4. Create `investigations/NNN-<slug>/README.md` from the investigation template with those answers. Status `planned`.
5. Create `investigations/NNN-<slug>/study-01/protocol.json` with `id: INNN-01`, `investigation: INNN`, the measures and the rule. `inputs` lists the files the study will read under `study-01/inputs/`; create the directory with a `.gitkeep` if no inputs exist yet. `affects` is empty until a claim exists.
6. Create `study-01/README.md` from the study template, status `protocol written`.
7. Add a row to `investigations/README.md`.
8. Run `python3 -m harness validate`.
9. Tell the researcher what was created, and that the next steps are: put the input files in `study-01/inputs/`, run `python3 -m harness create investigations/NNN-<slug>/study-01/protocol.json --out investigations/NNN-<slug>/study-01/frozen`, and commit `frozen/` before any analysis. That commit is the pre-registration record.
