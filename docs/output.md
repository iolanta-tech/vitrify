# Output and provenance

`vitrify sparql --to DIRECTORY` writes the result and two evidence files into
the directory:

```text
female-persons/
  query.rq
  results.csv
  ro-crate-metadata.json
```

`results.<extension>` is the ordinary response body, stored unchanged. Its
extension comes from `--format` when supplied, or from a recognized response
`Content-Type` when format selection is left to the endpoint. A missing or
unrecognized response media type produces `results.dat`.

`query.rq` contains the exact query text sent to the endpoint. It is included
even when the query was read from standard input.

`ro-crate-metadata.json` is an RO-Crate 1.2 JSON-LD document describing the
retrieval. It links the result and query files and records their byte sizes and
SHA-256 checksums, the result media type when provided, the endpoint, response
status, final URL, requested `Accept` value when one was sent, and retrieval
times. The result media type describes the received response and can differ
from the requested format.

The root dataset's license text says that Vitrify does not assert a license
for retrieved data. Check the source endpoint's terms before reusing that data.

Open the complete example metadata file:

[RO-Crate metadata for the Wikidata example](examples/female-persons/ro-crate-metadata.json)
