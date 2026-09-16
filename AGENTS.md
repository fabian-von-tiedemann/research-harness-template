# Instructions for agents

You are working in a research repo. The researcher owns the questions, the conclusions and the declared interests. You carry the work between those points.

## Before anything else

Read `method/README.md`: ten ground rules and a close-out check. Read `method/templates.md` before creating an investigation or a study. Read `knowledge/README.md` before touching `knowledge/registry.json`.

## Skills

- To start an investigation, follow `.agents/skills/new-investigation/SKILL.md`.
- To close an investigation or a session, follow `.agents/skills/close-out/SKILL.md`.

Codex discovers these as `$new-investigation` and `$close-out`. Other agents open the file and follow it.

## How to work

- Drive the work without asking permission at every step. Stop and ask when a choice would change an investigation's direction: the question, the competing hypothesis, a threshold, what counts as evidence.
- Write the competing hypothesis and freeze the protocol before looking at data. If the researcher wants to look first, say that rule 3 is about to be broken and let them decide.
- Never edit anything under a `frozen/` directory. If a protocol is wrong, write a new study.
- Never call a paid model or an external API from a study unless the researcher said so in this session. The harness makes no calls.
- Never commit identifiable personal data. Interview material enters `knowledge/snapshots/` only after the researcher has decided on de-identification. Example data is simulated and labelled `data_kind: simulated`.
- Every claim you add points at a preserved excerpt and has a concrete `reconsider_if`.
- When a rule, template or register convention changes, write it into `DECISIONS.md`, `CHANGELOG.md` and the file that carries the rule, in the same commit.

## Language

Write in the language the researcher writes in. Keep file names, JSON keys and commands in English so the harness and templates keep working.
