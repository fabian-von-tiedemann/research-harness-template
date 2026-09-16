# Method

The engine of this repo. An investigation answers one question through studies whose analysis plan was frozen and committed before data, and feeds what it learns into a register where every claim points at the excerpt it rests on. The method is field-neutral: it says nothing about your subject and everything about how a claim earns its place.

It leans on practice you can cite. Rule 3 is pre-registration as run by OSF Registries and AsPredicted, and the Registered Reports format where a journal reviews the plan before data. Rule 5 is provenance in the sense of the FAIR principles. Rule 8 uses CRediT roles and the conflict-of-interest declaration every journal asks for. The rules were taken from `framtidens-arbetssatt`, where they were extracted from seven research runs and sharpened by what each run found missing.

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
