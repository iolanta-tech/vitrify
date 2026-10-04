<h1><img src="docs/images/logo.png" alt="Vitrify" width="360"></h1>

[![Documentation](https://img.shields.io/badge/docs-Vitrify-blue)](https://vitrify.iolanta.tech/)
[![Rust 1.88+](https://img.shields.io/badge/rust-1.88%2B-orange)](https://www.rust-lang.org/)

Vitrify saves a SPARQL retrieval as an ordinary local file with attached RO-Crate evidence.

From the repository root, install Vitrify and retrieve a Wikidata result:

```sh
cargo install vitrify
vitrify sparql \
  --endpoint https://query.wikidata.org/sparql \
  --query docs/examples/female-persons/query.rq \
  --format csv \
  --to female-persons
```

This writes `female-persons/results.csv` with `query.rq` and
`ro-crate-metadata.json`. See the [documentation](https://vitrify.iolanta.tech/)
for the command reference, output details, workflows, and roadmap.
