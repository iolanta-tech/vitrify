# Query from stdin

A one-line Wikidata query piped to Vitrify through standard input.

{{ directory_preview('basic-example') }}

## SPARQL source

{{ source('docs/examples/basic-example/output/query.rq') }}

## Tabular response

{{ read_csv('docs/examples/basic-example/output/results.csv') }}

{{ source('docs/examples/basic-example/output/ro-crate-metadata.json', title='RO-Crate metadata', collapsed=True) }}

## Run it

From `basic-example/`, run `sh input/retrieve.sh`.

{{ source('docs/examples/basic-example/input/retrieve.sh', title='Retrieval script', collapsed=True) }}
