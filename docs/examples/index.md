---
icon: material/book-open-variant
---

# :material-book-open-variant: Examples

## :material-database-search: SPARQL

Each example shows a saved SPARQL query, a preview of its response, and the
files Vitrify wrote. Open a file link in the directory preview to inspect the
captured source, response, or [RO-Crate](https://www.researchobject.org/ro-crate/)
metadata.

[Query from a file](query-from-file.md) is probably the most production-ready
approach: the query can be versioned and reused in a pipeline. The other
examples use `printf` and standard input to keep their commands self-contained.

<div class="grid cards" markdown>

{{ examples_index() }}

-   :material-file-document-outline: **[Query from a file](query-from-file.md)**

</div>

## :material-code-braces: Context

Each example fetches one remote context and saves the JSON-LD and YAML-LD
documents `vitrify context` wrote.

<div class="grid cards" markdown>

{{ context_examples_index() }}

</div>

[Add an example](authoring.md).
