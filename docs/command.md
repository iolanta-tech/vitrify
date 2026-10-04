# Command reference

Vitrify currently provides the `sparql` command. It sends one query to a SPARQL
endpoint and saves the response body in an output directory.

```sh
vitrify sparql \
  --endpoint https://query.wikidata.org/sparql \
  --query docs/examples/female-persons/query.rq \
  --format csv \
  --to female-persons
```

## Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `--endpoint IRI` | Yes | SPARQL endpoint URL. |
| `--query PATH` or `--query -` | Yes | Read the query from a UTF-8 file, or read standard input when the value is `-`. |
| `--to DIRECTORY` | Yes | Directory for the result and its RO-Crate files. |
| `--format FORMAT` | No | Request a response format and use its corresponding filename extension. |

The query must not be empty. Standard input is read only when `--query -` is
specified. Vitrify saves the query text it sends as `query.rq` in the output
directory.

## Formats

| `--format` | Requested media type | Result extension |
| --- | --- | --- |
| `json` | `application/sparql-results+json` | `.json` |
| `xml` | `application/sparql-results+xml` | `.xml` |
| `csv` | `text/csv` | `.csv` |
| `tsv` | `text/tab-separated-values` | `.tsv` |
| `turtle` | `text/turtle` | `.ttl` |
| `ntriples` | `application/n-triples` | `.nt` |
| `rdfxml` | `application/rdf+xml` | `.rdf` |
| `jsonld` | `application/ld+json` | `.jsonld` |

When `--format` is omitted, Vitrify does not send an `Accept` header. It uses
the response `Content-Type` to choose a filename extension. If the media type
is missing or unrecognized, it writes `results.dat` and prints a warning.

Vitrify saves successful response bytes unchanged. The requested format does
not guarantee the endpoint returns that media type; use the recorded
`Content-Type` to identify the response.

A non-success HTTP response is an error and does not produce a successful
result crate.

## Requested and returned formats can differ

SPARQL `SELECT` results are tables, while Turtle represents an RDF graph. From
`docs/examples/select-turtle/`, run the retrieval script for an example that
requests Turtle for a `SELECT` query:

```sh
--8<-- "docs/examples/select-turtle/retrieve.sh"
```

QLever returned SPARQL Results JSON with HTTP 200. Vitrify saved the body as
`results.ttl` because Turtle was requested, and recorded the actual media type
as `application/sparql-results+json`. The extension alone does not identify the
body format; see [Output and provenance](output.md).
