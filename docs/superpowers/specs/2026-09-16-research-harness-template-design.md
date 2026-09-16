# research-harness-template: a research harness for agent-assisted, pre-registered work

Date: 2026-09-16. Owner: Fabian von Tiedemann. First user: Amanda, doctoral researcher, works with Codex and GitHub. Ambition: a template more researchers adopt and improve, with a feedback loop back into the template. Revised after review by Fable 5.1 the same day.

## Purpose

A public GitHub template repository, `fabian-von-tiedemann/research-harness-template`, that a researcher creates their own repo from and is productive in within an hour, with any of Claude Code, Codex, OpenCode or Pi at their side. The repo carries a working method, not a subject: investigations with a competing hypothesis, studies whose analysis plan is frozen and committed before data, a knowledge register where every claim points at a hashed excerpt, a decision log, and rules the agent reads at start.

It leans on established practice and names it: pre-registration and Registered Reports (OSF Registries, AsPredicted) for the frozen protocol; FAIR for the register's provenance; CRediT and conflict-of-interest declarations in the investigation template; Keep a Changelog and SemVer for the repo itself; CITATION.cff so the template can be cited.

The model is `framtidens-arbetssatt`. Form is taken from it, content is not. English throughout.

## Vocabulary

- **Investigation**: one question, an argument chain, a competing hypothesis, studies, synthesis, declared interests. `investigations/NNN-<slug>/`.
- **Study**: one pre-registered analysis inside an investigation. `study-NN/` with `protocol.json`, `inputs/`, and after freezing `frozen/` with manifest, result, evaluation and report. All committed.
- **Rival**: the competing hypothesis, stated so that data could support it.
- **Knowledge register**: `knowledge/registry.json`. Sources (hashed excerpts), claims (with evidence, status, review status, `reconsider_if`), documents (chapters and reports that depend on claims).
- **Data kind**: `simulated`, `primary`, `secondary`.

## What is taken from the model, and what is left

| Taken | Left |
|---|---|
| `harness/registry.py` and `harness/common.py`, trimmed | `runner`, `evaluator`, `transfer`, `requests`, `comparison`, `worker`, `http_worker`, `workflow`, `adapters`, `reasoning`: a channel simulator for one investigation |
| The form of the decision log, method rules, templates, red-team prompt, close-out check | The six-step domain method, legal checklists, pattern register, human-contribution cost |
| The form of an investigation and its numbered trials | All subject content |
| The working rules as `AGENTS.md` | Rules about Digitalist; replaced by declared interests, CRediT, COI |
| Register sections `sources`, `claims`, `documents` | `uses`, `legal`, `audience`, `assertion_mode`, `dated_legal_analysis`, `requirement_candidate`, `design_hypothesis` |

## Structure

```
AGENTS.md                         rules the agent reads at start; names the skill files by path
CLAUDE.md                         "@AGENTS.md"
README.md                         what, who for, first hour, the loop, established practice, structure, commands, feedback, licence
CHANGELOG.md                      Keep a Changelog
CITATION.cff
DECISIONS.md                      decision log
LICENSE                           MIT for code
LICENSE-CONTENT                   CC BY 4.0 for text
CONTRIBUTING.md                   feedback upstream
.github/ISSUE_TEMPLATE/method-gap.md, template-improvement.md, config.yml
method/README.md                  ten ground rules, close-out check
method/templates.md               investigation README, study README, source, claim
method/red-team.md                five lines of attack
investigations/README.md          index
investigations/001-example/README.md
investigations/001-example/study-01/README.md
investigations/001-example/study-01/protocol.json
investigations/001-example/study-01/inputs/hits.csv
investigations/001-example/study-01/compute.py
investigations/001-example/study-01/frozen/   protocol.json, inputs/hits.csv, manifest.json, result.json, evaluation.json, report.md
knowledge/README.md
knowledge/registry.json
knowledge/snapshots/
knowledge/INDEX.md                generated
harness/__init__.py, __main__.py, common.py, registry.py, study.py
tests/test_common.py, test_registry.py, test_study.py, test_cli.py
.agents/skills/new-investigation/SKILL.md
.agents/skills/close-out/SKILL.md
.gitignore
docs/superpowers/specs/, docs/superpowers/plans/, docs/message-to-amanda.md
```

## Components

### Knowledge register (`harness/registry.py`)

From the model, trimmed:

- `SECTIONS = ('sources', 'claims', 'documents')`.
- `CLAIM_TYPES = {'observation', 'hypothesis', 'interpretation', 'derivation', 'model_result'}`.
- Source kinds documented: `literature`, `transcript`, `empirical_report`, `dataset`, `model_trial`, `analysis`, `note`. An `observation` may only take `supports` from `transcript` or `empirical_report`; a `model_result` only from `model_trial`.
- Removed: `audience` and the public filter, `legal` and `legal_review_due`, `assertion_mode`, `normative_observation`, `source_family_count`. `family` stays so versions of one source can coexist.
- `STATUSES`, `REVIEW_STATUSES`, histories, anchors, hashes, cycles, `duplicate_source_version`, `snapshot_reused` unchanged.
- Register path `knowledge/registry.json`.

Functions: `validate_registry(root) -> list[dict]`, `build_index(root) -> str`, `context(root, ids) -> dict` (records with excerpts, selection log), `impact(root, changed_ids) -> dict` (dependents through any depth, as review proposals, no automatic status change), `snapshot(root, file) -> dict` (copies a file into `knowledge/snapshots/<sha256>.txt`, returns `sha256`, `snapshot`, `anchor` for the full file, and a ready-to-paste source entry skeleton).

### Study engine (`harness/study.py`)

A study is a frozen protocol plus a result plus a separate evaluation, all committed.

**Protocol** (`protocol.json`):

```json
{
  "schema_version": 1,
  "id": "I001-01",
  "investigation": "I001",
  "question": "…",
  "hypothesis": "…",
  "rival": "…",
  "measures": [{"id": "m1", "description": "…", "unit": "…"}],
  "interpretation_rule": {
    "measure": "m1",
    "supports_hypothesis_if": {"op": ">=", "value": 0.15},
    "supports_rival_if": {"op": "<=", "value": 0.0}
  },
  "exploratory": false,
  "affects": ["K001"],
  "inputs": ["inputs/hits.csv"],
  "data_kind": "simulated",
  "limitations": "…"
}
```

Rules: `op` in `>=`, `>`, `<=`, `<`, `==`. The two conditions must be disjoint (no value satisfies both); overlap is a contract error. Values satisfying neither give `undecided`. If `exploratory` is `true`, `interpretation_rule` must be `null` and the outcome is `descriptive`. `affects` are register IDs, checked when a register exists. `inputs` are relative to the protocol's directory, must stay inside it, and may not be named `protocol.json`, `manifest.json`, `result.json`, `evaluation.json` or `report.md`. `data_kind` in `simulated`, `primary`, `secondary`.

**`create <protocol.json> --out <dir>`**: copies protocol and inputs into `<dir>/`, writes `manifest.json` with `schema_version`, `id`, `created_at`, `status: "frozen"`, `hashes`. Convention: `--out <study-dir>/frozen`. Error if the directory exists.

**`evaluate <dir> [--write]`**: checks every hash in the manifest, reads `result.json` (`{"measures": {...}, "note": "…"}`), applies the rule, returns `evaluation.json` with `id`, `evaluated_at`, `measures`, `outcome` (`supports_hypothesis`, `supports_rival`, `undecided`, `descriptive`), `rule`, `data_kind`, `limitations`, `note`, `manifest_sha256`, `result_sha256`. A missing measure is a contract error. A negative or undecided outcome is exit 0.

**`report <dir>`**: prints one page of Markdown: study id, question, hypothesis, rival, measures, rule, data kind, limitations, `created_at`, every hash, and the git commit and date that first added `manifest.json` (from `git log --diff-filter=A --format=%H %cI -- <dir>/manifest.json`; "not committed yet" if none). With `--write`, saves `report.md` in the directory. This is the attachment for a grant application or a registered report.

**`demo`**: runs `create` on the example protocol into a temporary directory under `runs/local/`, copies the example's committed `frozen/result.json`, evaluates, prints the outcome. Does not touch the committed `frozen/`.

Exit codes: 0 success, 2 invalid input or contract, 3 interrupted.

### Method (`method/`)

`README.md`: ten ground rules, field-neutral, each naming the practice it rests on where one exists. Blank sheet; the rival before evidence; analysis plan frozen and committed before data (pre-registration, Registered Reports); evidence grade declared; every claim rests on a preserved excerpt (FAIR provenance); knowledge status and review status separate; red team before synthesis; interests declared (funder, CRediT roles, COI); no rule changes without a decision-log entry and a changelog line; honest limits with data kind. Close-out check in five steps, the fifth being the feedback question.

`templates.md`: investigation README (question and why, argument chain, what would change the conclusion, studies table, knowledge entries, synthesis, declared interests with CRediT roles and COI), study README (what is tested, protocol, how it was run, result, assessment, limitations), source entry, claim entry.

`red-team.md`: convenient conclusion, selection of evidence, measure that does not measure the claim, straw-man rival, generalisation beyond the material.

### AGENTS.md and skills

`AGENTS.md`: read `method/README.md` first; drive without per-step permission but stop at direction changes; never edit `frozen/`; no paid model or external calls from a study without instruction; no identifiable personal data committed; every claim points at an excerpt with a concrete `reconsider_if`; rule changes go to `DECISIONS.md`, `CHANGELOG.md` and the carrier file in one commit; "to start an investigation follow `.agents/skills/new-investigation/SKILL.md`; to close, follow `.agents/skills/close-out/SKILL.md`"; write in the researcher's language, keep file names and keys in English.

`CLAUDE.md`: the single line `@AGENTS.md`.

Skills in `.agents/skills/` with `name` and `description` frontmatter. Codex discovers them there; Claude Code, OpenCode and Pi reach them through the path in `AGENTS.md`. No symlinks.

### Feedback loop

`CONTRIBUTING.md`, two issue templates, and the close-out skill's final question with a drafted issue and an offered `gh issue create -R fabian-von-tiedemann/research-harness-template`. README section "Improving the template".

### Example investigation (`investigations/001-example/`)

Question: does a literature search with two search strings yield a higher share of relevant hits than with one? Simulated CSV with 40 hits. Measure m1 is the share of relevant hits for the combined search minus the single search; thresholds 0.15 and 0.0. `frozen/` is committed with manifest, result, evaluation and report, in a commit that precedes the commit adding claim K001, so the chronology is honest. K001 is a `derivation`, `provisional`, `unreviewed`, evidence from source S001, which is a snapshot of `frozen/inputs/hits.csv`. `DOC-example` depends on K001.

### Versioning

SemVer. `CHANGELOG.md` per Keep a Changelog, `[Unreleased]` during build, `[0.1.0] - 2026-09-16` at publish. `git tag v0.1.0`, GitHub release with the changelog section as notes. `harness/__init__.py` carries `__version__`.

### Licensing

MIT for `harness/`, `tests/`, scripts. CC BY 4.0 for text. `CITATION.cff` with the repo, version and date.

## Testing

`tests/test_common.py`, `tests/test_registry.py` (against the shipped register plus fixture mutations), `tests/test_study.py` (validate, disjointness, exploratory, create, reserved names, escape, affects, evaluate three outcomes, tamper, missing measure, report), `tests/test_cli.py` (exit codes for every command, demo twice). In a clean clone, `python3 -m unittest discover -s tests`, `python3 -m harness validate` and `python3 -m harness demo` pass. Standard library only, Python 3.10 or later.

## Delivery

1. Built locally in `~/Developer/research-harness-template`, committed per task.
2. `gh repo create fabian-von-tiedemann/research-harness-template --public --source . --push`, `is_template=true`, `git tag v0.1.0`, `gh release create v0.1.0`.
3. `docs/message-to-amanda.md` in Swedish, agent-neutral with a Codex note.

## Out of scope

Model adapters, sandboxes, queues, translation, symlinked skill directories. A researcher who runs a model inside a study writes a script that puts `result.json` into `frozen/`.
