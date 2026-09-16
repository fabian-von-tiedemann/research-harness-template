# Changelog

All notable changes to this template are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html). A rule, template or protocol-format change is a change to the template and belongs here as well as in `DECISIONS.md`.

## [Unreleased]

### Added

- Knowledge register: `validate`, `index`, `context`, `impact`, `snapshot`. Sources are hashed excerpts; claims carry status, review status and `reconsider_if`; documents depend on claims.
- Pre-registered studies: `create` freezes protocol and inputs with hashes, `evaluate` applies the interpretation rule to `result.json`, `report` prints a one-page pre-registration summary with the git commit. Thresholds must be disjoint; exploratory studies get a descriptive outcome.
- `demo` runs the example study end to end.
- Method: ten ground rules and a five-step close-out check. Templates for investigation, study, source, claim and document. Red-team prompt with five lines of attack.
- Example investigation I001 on simulated data, frozen and evaluated, with claim K001 in the register.
