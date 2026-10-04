# SELECT response returned as JSON

This example asks QLever for Turtle while running a `SELECT` query. The
endpoint returns SPARQL Results JSON, and Vitrify records that actual response
type even though the requested format determines the `results.ttl` filename.

{{ directory_preview('select-turtle') }}

## SPARQL source

{{ source('docs/examples/select-turtle/query.rq') }}

## Tabular response preview

{{ response_table('select-turtle') }}

The saved file has a `.ttl` extension because Turtle was requested, while its
actual media type is `application/sparql-results+json`, recorded in the
RO-Crate.

{{ source('docs/examples/select-turtle/ro-crate-metadata.json', title='RO-Crate metadata', collapsed=True) }}

## Run it

From `select-turtle/`, run the [retrieval script](select-turtle/retrieve.sh)
with `sh`:

```sh
--8<-- "docs/examples/select-turtle/retrieve.sh"
```
