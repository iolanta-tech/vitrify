<h1><img src="docs/images/logo.png" alt="Vitrify" width="360"></h1>

[![Documentation](https://img.shields.io/badge/docs-Vitrify-blue)](https://vitrify.iolanta.tech/)
[![Rust 1.88+](https://img.shields.io/badge/rust-1.88%2B-orange)](https://www.rust-lang.org/)

Vitrify saves a SPARQL retrieval as an ordinary local file with attached RO-Crate evidence.

Install Vitrify and retrieve a Wikidata result:

```sh
cargo install vitrify
echo 'SELECT ?label WHERE { ?country wdt:P463 wd:Q458; wdt:P36 ?capital . ?capital rdfs:label ?label . FILTER(LANG(?label) = "en") } ORDER BY ?label LIMIT 5' |
  vitrify sparql \
  --endpoint https://query.wikidata.org/sparql \
  --query - \
  --format csv \
  --to eu-capitals
```

This writes `eu-capitals/results.csv` with `query.rq` and
`ro-crate-metadata.json`. See the [documentation](https://vitrify.iolanta.tech/)
for the command reference, output details, workflows, and roadmap.
