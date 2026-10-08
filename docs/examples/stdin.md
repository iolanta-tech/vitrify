# :material-import: Query from stdin

A one-line Wikidata query piped to Vitrify through standard input.

{{ directory_preview('basic-example') }}

## :material-code-braces: SPARQL source

{{ source('docs/examples/basic-example/eu-capitals/query.rq') }}

## :material-table: Tabular response

{{ read_csv('docs/examples/basic-example/eu-capitals/results.csv') }}

{{ source('docs/examples/basic-example/eu-capitals/ro-crate-metadata.json', title='RO-Crate metadata', collapsed=True) }}

## :material-play: Run it

From `basic-example/`, run `sh input/retrieve.sh`.

{{ source('docs/examples/basic-example/input/retrieve.sh', title='Retrieval script', collapsed=True) }}
