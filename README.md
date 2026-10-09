<h1><img src="docs/images/logo.png" alt="Vitrify" width="360"></h1>

[![Documentation](https://img.shields.io/badge/docs-Vitrify-blue)](https://vitrify.iolanta.tech/)
[![Rust 1.88+](https://img.shields.io/badge/rust-1.88%2B-orange)](https://www.rust-lang.org/)

Vitrify saves a SPARQL response as an ordinary local file, alongside the exact
query and RO-Crate retrieval evidence.

With Rust and Cargo installed, install Vitrify from crates.io:

```sh
cargo install vitrify
```

Retrieve five EU-capital labels from Wikidata:

```sh
echo 'SELECT ?label WHERE { ?country wdt:P463 wd:Q458; wdt:P36 ?capital . ?capital rdfs:label ?label . FILTER(LANG(?label) = "en") } ORDER BY ?label LIMIT 5' |
  vitrify sparql \
  --endpoint https://query.wikidata.org/sparql \
  --query - \
  --format csv \
  --to eu-capitals
```

The output directory contains:

```text
eu-capitals/
  results.csv
  query.rq
  ro-crate-metadata.json
```

`results.csv` is the endpoint response body, stored unchanged. The metadata
records retrieval details, including the endpoint, response media type, and
checksums for the query and result. A captured response looks like this:

```csv
label
Amsterdam
Athens
Berlin
Bratislava
Brussels
```

See the [CLI reference](https://vitrify.iolanta.tech/cli/) for options and the
[roadmap](https://vitrify.iolanta.tech/roadmap/) for planned work.
