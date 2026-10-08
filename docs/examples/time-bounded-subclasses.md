# :material-clock-outline: Time-bounded subclasses

This Wikidata query finds subclass statements with start and end qualifiers,
then returns their English labels. The captured JSON response contains 176
bindings.

{{ directory_preview('time-bounded-subclasses') }}

## :material-code-braces: SPARQL source

{{ source('docs/examples/time-bounded-subclasses/query.rq') }}

## :material-table: Tabular response preview

{{ response_table('time-bounded-subclasses') }}

The [RO-Crate](https://www.researchobject.org/ro-crate/) records the response
file's media type and checksum.

{{ source('docs/examples/time-bounded-subclasses/ro-crate-metadata.json', title='RO-Crate metadata', collapsed=True) }}

## :material-play: Run it

From `time-bounded-subclasses/`, run the
[retrieval script](time-bounded-subclasses/retrieve.sh) with `sh`:

```sh
--8<-- "docs/examples/time-bounded-subclasses/retrieve.sh"
```
