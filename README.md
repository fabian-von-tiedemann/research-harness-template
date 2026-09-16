# research-harness-template

A research harness for agent-assisted, pre-registered work. It carries a method, not a subject: investigations with a competing hypothesis, studies whose analysis plan is frozen and committed before data, a knowledge register where every claim points at the hashed excerpt it rests on, a decision log, and rules any coding agent reads before it does anything.

Built for doctoral work first. The ambition is a template more researchers adopt and improve. Everything you find lacking is something to send back; see [Improving the template](#improving-the-template).

## Who it is for

- **Doctoral and master's work.** Literature studies, interview analysis, data studies, with a traceable path from source excerpt to chapter.
- **Research groups** that want several people and agents working in one knowledge state without losing track of what rests on what.
- **Policy analysis and evaluation** where a revised source must trigger re-review of everything built on it. `python3 -m harness impact S001` lists it.
- **Grant applications and registered reports.** A frozen protocol with hashes and a commit date, printed by `python3 -m harness report`, is evidence of rigor a reviewer can check rather than take on trust.
- **Consultancy and product research** where interests must be declared and a convenient conclusion attacked before it is published.
- **Teaching research method.** The repo is a runnable version of "state the competing hypothesis and lock the measure before you look at data".

## First hour

1. Click **Use this template** on GitHub, name your repo, clone it.
2. Check the harness runs:
   ```sh
   python3 -m harness validate
   python3 -m harness demo
   python3 -m unittest discover -s tests
   ```
   Python 3.10 or later, standard library only. `demo` freezes the example study in a scratch directory, evaluates it and prints `supports_hypothesis`.
3. Read `method/README.md`. Ten rules and a close-out check. Fifteen minutes.
4. Start your agent in the repo. It reads `AGENTS.md` first (Claude Code reads `CLAUDE.md`, which imports it). In Codex, type `$new-investigation`. In any other agent, say "follow `.agents/skills/new-investigation/SKILL.md`". Answer its questions: your question, your hypothesis, the competing hypothesis, your first measure, your interests.
5. Once your own first investigation exists, delete `investigations/001-example/`, remove S001, K001 and DOC-example from `knowledge/registry.json`, delete the snapshot they point at, and run `python3 -m harness validate`.

## The loop

```
question ──▶ competing hypothesis ──▶ protocol frozen and committed ──▶ data in ──▶ result.json ──▶ evaluate ──▶ knowledge entry ──▶ decision
   ▲                                  (measures, thresholds, hashes)                                 (hash-checked)                       │
   └─────────────────────────────────────── red team before synthesis ◀──────────────────────────────────────────────────────────────────┘
```

- **Investigation:** one question, an argument chain, what would change the conclusion, studies, synthesis, declared interests. `investigations/NNN-<slug>/README.md`.
- **Study:** `protocol.json` names the measures and an interpretation rule with two thresholds that may not overlap. `python3 -m harness create` copies protocol and inputs into `frozen/` with hashes; you commit `frozen/` before any analysis, and that commit is the pre-registration record. A script, or you, writes `result.json` into `frozen/`. `python3 -m harness evaluate` checks the hashes and applies the rule: `supports_hypothesis`, `supports_rival`, `undecided`, or `descriptive` for exploratory studies. `python3 -m harness report` prints the page a reviewer reads.
- **Knowledge:** `knowledge/registry.json`. Sources are hashed excerpts. Claims point at excerpts, carry a status, a review status and a `reconsider_if`. Documents are the chapters that depend on claims. `validate` enforces the shape; `impact` follows dependencies when a source changes; `context` builds a source-bound pack for an agent.
- **Decisions:** `DECISIONS.md` for what changed and why; `CHANGELOG.md` for what changed in the template itself.

The worked example is [I001](investigations/001-example/README.md): simulated data, one study, one claim, every file the loop produces.

## Established practice it leans on

- **Pre-registration and Registered Reports.** Rule 3 is what OSF Registries and AsPredicted ask for, with the git commit as the timestamp. For a real study, register the same plan there too.
- **FAIR provenance.** Every claim is traceable to a hashed excerpt with a line range.
- **CRediT and conflict-of-interest declarations** in every investigation README.
- **Keep a Changelog and Semantic Versioning** for the template; **CITATION.cff** so it can be cited.

## Works with

Claude Code, Codex, OpenCode and Pi. All read `AGENTS.md` (Claude Code through `CLAUDE.md`). The two skills live in `.agents/skills/`; Codex discovers them, the others follow the path `AGENTS.md` gives. Nothing else is agent-specific.

## Structure

| Path | What |
|---|---|
| `AGENTS.md` | Rules every agent reads at start. `CLAUDE.md` imports it. |
| `method/` | Ground rules, close-out check, templates, red-team prompt. |
| `investigations/` | One directory per question. Studies inside, each with `protocol.json`, `inputs/`, `frozen/`. |
| `knowledge/` | Register, hashed snapshots, generated index, how-to. |
| `harness/` | `registry.py` (validate, index, context, impact, snapshot) and `study.py` (create, evaluate, report). `python3 -m harness --help`. |
| `tests/` | `python3 -m unittest discover -s tests`. |
| `runs/local/` | Scratch output from `demo`. Gitignored. |
| `.agents/skills/` | `new-investigation`, `close-out`. |
| `DECISIONS.md` | Decision log. |
| `CHANGELOG.md` | Template changes by version. |
| `CONTRIBUTING.md` | How to send feedback upstream. |

## Commands

```sh
python3 -m harness validate                      # check the register and snapshots
python3 -m harness index > knowledge/INDEX.md    # regenerate the readable index
python3 -m harness context K001                  # claims, dependencies and excerpts for an agent
python3 -m harness impact S001                   # what needs re-review when a source changes
python3 -m harness snapshot paper-excerpt.txt    # hash an excerpt and print a source entry
python3 -m harness create <study>/protocol.json --out <study>/frozen
python3 -m harness evaluate <study>/frozen --write
python3 -m harness report <study>/frozen --write
python3 -m harness demo
```

Exit codes: 0 done, 2 invalid input or contract, 3 interrupted. A negative or undecided study outcome is exit 0; it is a result, not an error.

## Improving the template

Three ways, all in `CONTRIBUTING.md`:

1. Open a **Method gap** or **Template improvement** issue on `fabian-von-tiedemann/research-harness-template`.
2. Let the `close-out` skill ask you at the end of each investigation; it drafts the issue.
3. Send a pull request.

## Versioning

Semantic Versioning, recorded in `CHANGELOG.md`. Your own repo made from the template keeps its own changelog from the version it started on.

## Licence

Code (`harness/`, `tests/`, scripts): MIT, see `LICENSE`. Text (method, templates, examples, this file): CC BY 4.0, see `LICENSE-CONTENT`.

## Origin

The form comes from [framtidens-arbetssatt](https://github.com/digitalist-se/framtidens-arbetssatt), a research repo on future ways of working, where the register validator, the decision log and the close-out check were extracted from seven domain runs. The subject content stayed there.
