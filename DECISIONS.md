# Decision log

The repo's decisions in date order: what was decided, why, and what in the documentation changed as a result. The log exists because decisions otherwise live only in the file they happened to change, and then nobody can see whether the documentation reflects them.

A decision belongs here when it changes the repo's direction, method, scope, or what leaves the repo. The content of a single investigation does not; that stays in the investigation's own files. A decision that changes a rule, a template or a format also gets a line in `CHANGELOG.md`.

The log is filled in at every close-out, see `method/README.md`.

## 2026-09-16

**1. The template is created from `framtidens-arbetssatt`, form only.** The model repo's register validator, decision log, investigation form and close-out check are general; its domain method, channel simulator and subject content are not.
Landed in: `harness/registry.py`, `method/`, `DECISIONS.md`, `investigations/001-example/`.

**2. A study is a frozen protocol plus a separately evaluated result, and the harness never calls a model.** A researcher who wants a model inside a study writes a script that puts `result.json` into `frozen/`. Keeps the harness small and the evidence chain inspectable.
Landed in: `harness/study.py`, `method/README.md` rule 3.

**3. `frozen/` is committed, and the git commit that adds it is the pre-registration record.** After review: a frozen directory that lives in a gitignored path proves nothing. Committing it makes the timestamp and the hashes public, and `python3 -m harness report` prints them for a reviewer.
Landed in: `harness/study.py` (`report`), `method/README.md` rule 3, `method/templates.md`, `investigations/001-example/study-01/frozen/`.

**4. Code is MIT, text is CC BY 4.0.** So the harness can be reused in any project and the method can be adapted with attribution.
Landed in: `LICENSE`, `LICENSE-CONTENT`, `README.md`.

**5. Feedback goes upstream through issues, and the close-out check asks for it.** The template improves from use only if the loop runs without anyone remembering it.
Landed in: `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/`, `method/README.md` close-out step 5, `.agents/skills/close-out/`.
