---
icon: material/code-braces
---

# :material-code-braces: vitrify context

`vitrify context` GETs one absolute HTTP(S) URL. The
[dollar-convenience context](../examples/dollar-convenience.md) is a small
example.

{{ context_retrieval('dollar-convenience') }}

## :material-format-list-bulleted: Arguments

{{ cli_arguments('context') }}

A failed fetch, a non-success status, or a body that is not a context returns a
nonzero exit status and prints nothing to standard output.

The document keeps the fetched `@context` unchanged and has no `@id`.
`contentUrl` is the final URL. The request records the URL that was asked for.
Vitrify also records the byte size, SHA-256 of the downloaded bytes, media
type, response headers, and the time of the retrieval.
Metadata keys are absolute IRIs. Literals are JSON-LD value objects, so a
term's type, language, and direction do not apply to them. A processor
rejects the document when a context term maps one of those IRIs to a
different IRI. `@container` on a term whose name is one of those IRIs
applies to the literal. `@list` wraps it in an RDF list.

A remote `@context` URL or `@import` is not fetched again. Vitrify prints a
warning on standard error and copies that reference as it is.
