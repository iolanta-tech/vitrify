---
icon: material/console
hide: [navigation, toc]
---

# :material-console: CLI

Vitrify currently provides the `sparql` command only. It sends one query to a SPARQL
endpoint and saves the response body in an output directory.

```sh
vitrify sparql \
  --endpoint https://query.wikidata.org/sparql \
  --query docs/examples/female-persons/query.rq \
  --format csv \
  --to female-persons
```

## :material-format-list-bulleted: Arguments

| Argument | Required | Description |
| --- | --- | --- |
| `--endpoint IRI` | Yes | SPARQL endpoint URL. |
| `--query PATH` or `--query -` | Yes | Read the query from a UTF-8 file, or read standard input when the value is `-`. |
| `--to DIRECTORY` | Yes | Directory for the result and its [RO-Crate](https://www.researchobject.org/ro-crate/) files. |
| `--format FORMAT` | No | Request a response format; also supplies a fallback filename extension. |

The query must not be empty. Standard input is read only when `--query -` is
specified. Vitrify saves the query text it sends as `query.rq` in the output
directory.

## :material-file-document-multiple: Formats

| `--format` | Requested media type | Fallback extension |
| --- | --- | --- |
| `json` | `application/sparql-results+json` | `.json` |
| `xml` | `application/sparql-results+xml` | `.xml` |
| `csv` | `text/csv` | `.csv` |
| `tsv` | `text/tab-separated-values` | `.tsv` |
| `turtle` | `text/turtle` | `.ttl` |
| `ntriples` | `application/n-triples` | `.nt` |
| `rdfxml` | `application/rdf+xml` | `.rdf` |
| `jsonld` | `application/ld+json` | `.jsonld` |

Vitrify chooses the filename extension from the response `Content-Type`, even
when it differs from `--format`. If that media type is missing or unrecognized,
it uses the extension for `--format`. With neither available, it writes
`results.dat` and prints a warning.

When `--format` is omitted, Vitrify does not send an `Accept` header.

Vitrify saves successful response bytes unchanged. The requested format does
not guarantee the endpoint returns that media type; use the recorded
`Content-Type` to identify the response.

A non-success HTTP response returns a nonzero exit status and saves the failed
retrieval in the [RO-Crate metadata](outputs/ro-crate/index.md), including its
error and duration.
