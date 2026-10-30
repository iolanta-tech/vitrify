---
icon: material/package-variant-closed
---

# :material-package-variant-closed: RO-Crate

`vitrify sparql --to DIRECTORY` writes the result and two evidence files into
the directory:

```text
female-persons/
  query.rq
  results.csv
  ro-crate-metadata.json
```

`results.<extension>` is the ordinary response body, stored unchanged. Its
extension comes from a recognized response `Content-Type`. If that media type
is missing or unrecognized, Vitrify falls back to `--format`, then to `.dat`
when no format was requested.

`query.rq` contains the exact query text sent to the endpoint. It is included
even when the query was read from standard input.

`ro-crate-metadata.json` is an [RO-Crate](https://www.researchobject.org/ro-crate/)
1.3 JSON-LD document describing the
retrieval. It links the result and query files and records their byte sizes and
SHA-256 checksums, the result media type when provided, the endpoint, response
status, final URL, requested `Accept` value when one was sent, and retrieval
times. The retrieval action has a completed or failed status. Linked `PropertyValue`
entities record retrieval duration in seconds. Duration covers the
request, redirects, and response download; it excludes final metadata writing.

The result media type describes the received response and can differ
from the requested format.

The root dataset's license text says that Vitrify does not assert a license
for retrieved data. Check the source endpoint's terms before reusing that data.

Open the complete example metadata file:

[RO-Crate metadata for the Wikidata example](../../examples/female-persons/ro-crate-metadata.json)

## :material-folder-refresh: Reusing an output directory

A successful retrieval into an existing directory overwrites `query.rq`, the
result file with the selected extension, and `ro-crate-metadata.json`. Result
files with other extensions remain: receiving JSON after a previous CSV
response leaves both `results.json` and `results.csv`, while the new
metadata describes only `results.json`. Use a new directory or preserve the
existing capture in version control before retrieving again.

Vitrify initializes the query and metadata before requesting the endpoint. It
replaces the metadata atomically when the retrieval finishes. A network or HTTP
failure records the error and duration and returns a nonzero exit status. A
streaming failure can leave a partial response, identified as incomplete in the
metadata rather than linked as a successful result. An interrupted process can
leave an active action; treat that capture as incomplete.

Invalid inputs fail before retrieval initialization. If the output directory
cannot be written, the CLI reports the filesystem error; a saved attempt may
not be available.

## :material-chart-bar: Example history

Each example has WDQS and QLever tabs, each with its own command, saved files,
and response-size history.
Select a bar to open that attempt's permanent page. The newest attempt is
selected by default, including failures. Hover or focus a bar for its timestamp,
outcome, byte count, and duration. A hollow `?` marker indicates an unavailable
size; bar height represents the saved response size in bytes. Duration appears beneath each
bar. Older captures use estimated durations derived from their recorded
timestamps, marked with `≈`.

From the repository root, with the project environment activated, append a new
capture for every example on its configured endpoints:

```sh
cargo build
j examples
```

The runner uses the local debug build when available, otherwise `vitrify` from
`PATH`. It discovers Markdown-LD example pages and runs their endpoint variants sequentially in temporary directories and saves
Vitrify's output in new timestamped directories. Earlier captures stay intact.
It continues after individual failures, validates saved crates against RO-Crate
1.3, and exits nonzero if any retrieval or validation failed. Validation results
appear in the terminal. Documentation builds read saved captures.
