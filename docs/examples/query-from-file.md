---
hide: [toc]
---

# :material-file-document-outline: Query from a file

Create a file named `query.rq` in your working directory with this content:

```sparql
--8<-- "docs/examples/basic-example/eu-capitals/query.rq"
```

From the same directory, run:

```bash
vitrify sparql \
  --endpoint https://query.wikidata.org/sparql \
  --query query.rq \
  --format csv \
  --to eu-capitals
```

This runs the same query as [EU capitals](eu-capitals.md) and writes the
capture shown below.

{{ directory_preview('basic-example') }}

{{ file_tabs('basic-example') }}
