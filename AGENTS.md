# Vitrify agent guidance

## Project tasks

This project is managed with [Jeeves](https://jeeves.sh). Run `j <task>` and
consult `jeeves.py` before adding, changing, or invoking project tasks.

For CLI commands, arguments, and output behavior, start with
`docs/cli.md` and `docs/outputs/ro-crate/index.md`.

## Setup and verification

- `.envrc` activates the project-local `.venv`; run `direnv allow .` after
  setting up the checkout or changing that file.
- `j serve` starts the documentation site at `http://localhost:6453`.
- `j examples` reruns every displayed retrieval script and validates the
  resulting crates against the RO-Crate 1.2 profile. It contacts the example
  endpoints and rewrites their captured artifacts, so run it only when a
  deliberate refresh is in scope.

## Reviews

- Before reporting a behavioral mismatch between the documentation and
  implementation, trace the public command path through the relevant internal
  operations. Do not infer command behavior from an internal helper alone.
