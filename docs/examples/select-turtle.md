# :material-code-json: SELECT response returned as JSON

This example asks QLever for Turtle while running a `SELECT` query. The
endpoint returns SPARQL Results JSON, and Vitrify records that actual response
type even though the requested format determines the `results.ttl` filename.

{{ directory_preview('select-turtle') }}

## :material-code-braces: SPARQL source

{{ source('docs/examples/select-turtle/query.rq') }}

## :material-table: Tabular response preview

{{ response_table('select-turtle') }}

{{ source('docs/examples/select-turtle/ro-crate-metadata.json', title='RO-Crate metadata', collapsed=True) }}

## :material-play: Run it

From `select-turtle/`, run the [retrieval script](select-turtle/retrieve.sh)
with `sh`:

```sh
--8<-- "docs/examples/select-turtle/retrieve.sh"
```
