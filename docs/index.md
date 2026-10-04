---
hide: [navigation, toc]
---

<h1><img src="images/logo.png" alt="Vitrify" width="360"></h1>

Vitrify saves SPARQL results with the query and retrieval evidence.

## Install

Install from crates.io:

```sh
cargo install vitrify
```

## One retrieval, three local artifacts

<div class="grid cards vitrify-workflow" markdown>

-   :material-database: **SPARQL endpoint**

    Send the exact query to Wikidata's mutable endpoint.

    `https://query.wikidata.org/sparql`

    <span class="vitrify-workflow-arrow" aria-hidden="true">:material-arrow-right:</span>

-   :material-console: **Vitrify command**

    ```sh
    --8<-- "docs/examples/basic-example/input/retrieve.sh"
    ```

    <span class="vitrify-workflow-arrow" aria-hidden="true">:material-arrow-right:</span>

-   :material-folder-open: **RO-Crate directory**

    The ordinary response file is kept with the exact query and RO-Crate
    evidence.

    :material-file-document-outline: [`query.rq`](examples/basic-example/output/query.rq)  
    :material-table: [`results.csv`](examples/basic-example/output/results.csv)  
    :material-code-json: [`ro-crate-metadata.json`](examples/basic-example/output/ro-crate-metadata.json)

</div>

[Full stdin example](examples/stdin.md).

## Inspect the capture

=== "Results CSV"

{{ read_csv('docs/examples/basic-example/output/results.csv') | add_indentation(spaces=4) }}

=== "RO-Crate metadata"

    ```json
    [
      // Result file
    --8<-- "docs/examples/basic-example/output/ro-crate-metadata.json:37:42"
      // … retrieval record follows; other crate entities are omitted
    --8<-- "docs/examples/basic-example/output/ro-crate-metadata.json:62:85"
    ]
    ```
