---
icon: material/database-search
---

# :material-database-search: sparql

`sparql` sends one query to a SPARQL endpoint and saves the response body in an
output directory.

```sh
vitrify sparql \
  --endpoint https://query.wikidata.org/sparql \
  --query docs/examples/female-persons/query.rq \
  --format csv \
  --to female-persons
```

## :material-format-list-bulleted: Arguments

{{ cli_arguments('sparql') }}

The query must not be empty. Standard input is read only when `--query -` is
specified. Vitrify saves the query text it sends as `query.rq` in the output
directory.

## :material-file-document-multiple: Formats { #formats }

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
