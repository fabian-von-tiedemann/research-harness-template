# Improving the template

This template gets better only through use. If it got in your way, that is the most useful thing you can send back.

## What to send

- **Method gaps.** A ground rule that did not fit your field, a close-out step that made no sense, a template heading you always skip or always add.
- **Harness friction.** A command that did the wrong thing, a validator error you could not understand, a protocol shape the study engine could not express.
- **New study patterns.** A kind of study the protocol format handled badly, with a sketch of what would have fit.
- **Fixes.** Pull requests for any of the above are welcome. Keep the standard-library-only rule, keep tests passing, add a line under `[Unreleased]` in `CHANGELOG.md`.

## What not to send

- Your subject content. The template is field-neutral and stays that way.
- Personal data of any kind, including in example files.
- A model adapter inside the harness. The design keeps model calls outside: a script writes `result.json` into `frozen/`. See `DECISIONS.md` entry 2. If you think that is wrong, open a method-gap issue and argue it.

## How

1. Open an issue on `fabian-von-tiedemann/research-harness-template` using the **Method gap** or **Template improvement** template.
2. The `close-out` skill asks the feedback question at the end of every investigation and drafts the issue for you. You read it before it is filed.
3. For a fix: fork, branch, `python3 -m unittest discover -s tests`, pull request. Say which rule or command the change affects.

## Licence of contributions

Code contributions are accepted under MIT, text contributions under CC BY 4.0. Opening a pull request means you agree to that.
