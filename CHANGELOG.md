# Changelog

All notable changes to this template are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). A rule, template or protocol-format change is a change to the template and belongs here as well as in `DECISIONS.md`.

## [Unreleased]

### Added

- `python3 -m harness check [--staged]`: the repo's own rules. Versions in `harness/__init__.py`, `CHANGELOG.md` and `CITATION.cff` agree; `[Unreleased]` exists; ten ground rules; no em-dashes; README links resolve; every investigation is indexed; skills have frontmatter. With `--staged`: no change or deletion under `frozen/`, and no rule, template or harness change without a `CHANGELOG.md` line.
- `.githooks/pre-commit` running `check --staged`; enable with `git config core.hooksPath .githooks`.
- GitHub Actions workflow running `check`, `validate`, `demo` and the tests on Python 3.10 and 3.13.
- README badges for CI, release, licence and "Use this template". Repository topics and Discussions on GitHub.

## [0.1.0] - 2026-09-16

### Added

- Knowledge register: `validate`, `index`, `context`, `impact`, `snapshot`. Sources are hashed excerpts; claims carry status, review status and `reconsider_if`; documents depend on claims.
- Pre-registered studies: `create` freezes protocol and inputs with hashes, `evaluate` applies the interpretation rule to `result.json`, `report` prints a one-page pre-registration summary with the git commit. Thresholds must be disjoint; exploratory studies get a descriptive outcome.
- `demo` runs the example study end to end.
- Method: ten ground rules and a five-step close-out check. Templates for investigation, study, source, claim and document. Red-team prompt with five lines of attack.
- Example investigation I001 on simulated data, frozen and evaluated, with claim K001 in the register.

[Unreleased]: https://github.com/fabian-von-tiedemann/research-harness-template/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fabian-von-tiedemann/research-harness-template/releases/tag/v0.1.0
