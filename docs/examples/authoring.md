---
hide: [toc]
---

# :material-file-document-edit-outline: Add an example

Create a Markdown page under `docs/examples/`. Its frontmatter supplies the
SPARQL query, endpoint URLs, and optional requested format:

````markdown
---
"@context": urn:vitrify:examples
endpoints:
  - https://query.wikidata.org/sparql
  - https://qlever.dev/api/wikidata
format: csv
query: |
  PREFIX wd: <http://www.wikidata.org/entity/>
  PREFIX wdt: <http://www.wikidata.org/prop/direct/>

  SELECT ?person WHERE {
    ?person wdt:P31 wd:Q5 .
  }
---

# Humans

Retrieve all items classified as humans.
````

Use a descriptive filename and one level-one heading. Keep benchmark queries
complete; result previews show only the first five rows. Omit `format` to let
the endpoint choose its response type. The [CLI reference](../cli.md) lists
accepted format names.

The page appears automatically in the examples index and navigation. Its command,
endpoint tabs, history, and saved-file previews use a shared layout. The
`urn:vitrify:examples` context and its local registration share one YAML-LD file:
`docs/contexts/examples.yamlld`.

From the repository root, activate the project environment and check the catalog:

```sh
source .venv/bin/activate
j lint
```

Preview the site with `j serve`. Building or serving the documentation reads
saved captures. To deliberately retrieve every example from every configured
endpoint, build Vitrify and run:

```sh
cargo build
j examples
```

Each attempt is saved in a new timestamped directory beside its example.
Failures remain part of the history. Requests retain the CLI's 120-second
timeout and 1 GiB response limit.

Keep the page filename when you want to retain its capture association. When
renaming a page, move its capture directory and preserve published routes.
