---
name: close-out
description: Run the close-out check when an investigation or a working session ends, and before anything is shared outside the repo. Ends with the feedback question about the template.
---

# Close-out

You run the five checks in `method/README.md`, section "Close-out check", in order, and report deviations together with what you corrected.

## Steps

1. **Decisions.** Read the investigation README and the git log since the investigation started. List every decision that changed the repo's direction, method, scope or what leaves the repo. For each, add an entry to `DECISIONS.md` under today's date: what, why, which files it landed in. If there are none, say so.
2. **Carrier documents.** For each decision, open the file that carries the rule (`method/README.md`, `method/templates.md`, `knowledge/README.md`, a skill) and confirm the change is there. If a rule, template or format changed, confirm there is a line under `[Unreleased]` in `CHANGELOG.md`. Fix what is missing.
3. **Harness.** Run, in order:
   ```sh
   python3 -m harness check
   python3 -m harness validate
   python3 -m harness index > knowledge/INDEX.md
   python3 -m unittest discover -s tests
   ```
   Stop and report if any fails. Do not mark the investigation closed with a failing validate.
4. **Investigation index.** Compare the row in `investigations/README.md` with the investigation README: status, outcome. Fix the row.
5. **Feedback.** Ask the researcher: "Did the method, a template or the harness get in the way anywhere in this investigation? A rule that did not fit, a template heading you skipped, a command that did the wrong thing?" If yes, draft an issue using `.github/ISSUE_TEMPLATE/method-gap.md`, show it, and if the researcher agrees offer:
   ```sh
   gh issue create -R fabian-von-tiedemann/research-harness-template --title "<title>" --body-file <draft>
   ```
   Never file without the researcher seeing the text. Never include subject content or personal data in the issue.

Report: decisions written, corrections made, test results, and whether feedback was sent.
