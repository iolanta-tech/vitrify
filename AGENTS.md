# Vitrify agent guidance

## Project tasks

This project is managed with [Jeeves](https://jeeves.sh). Run `j <task>` and
consult the `jeeves` package before adding, changing, or invoking project tasks.
Expose project commands through Jeeves rather than standalone scripts.
Prefer deterministic checks enforced by `j lint` and CI over prompting agents
with rules that can be checked automatically.

For CLI commands, arguments, and output behavior, start with
`docs/sparql.md`, `docs/context/index.md`, and `docs/outputs/ro-crate/index.md`.

A documented Vitrify retrieval is an example under `docs/examples`. Let `j examples`
save and refresh its captures. Do not add a one-off output file for the documentation.

## RDF vocabulary

Before minting RDF terms, use `find-url-for` to find and verify existing candidates.
Check their meaning, domain, range, and value type. Mint terms only for remaining
gaps. Choose their URI scheme from the intended publication and resolution
requirements.

## Setup and verification

- `.envrc` activates the project-local `.venv`; run `direnv allow .` after
  setting up the checkout or changing that file.
- `j lint` checks Python task entry points, runs Python tests, and protects existing
  snapshots against local changes. Use `--base REVISION --head REVISION` to
  compare committed revisions, as CI does.
- Run `j lint`, and only `j lint`, before reporting a Python or Rust change
  complete. Do not resort to a one-file run.
- `j serve` starts the documentation site at `http://localhost:6453`.
- `j examples` runs each Markdown-LD example on its configured endpoints and validates the
  resulting crates against the RO-Crate 1.3 profile. It contacts the example
  endpoints and appends timestamped captures, so run it only when a
  deliberate refresh is in scope.

## Reviews

- After every change to the documentation, run an `/mkdocs` review before
  reporting that change complete.
- Before reporting a behavioral mismatch between the documentation and
  implementation, trace the public command path through the relevant internal
  operations. Do not infer command behavior from an internal helper alone.
