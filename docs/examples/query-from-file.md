---
hide: [toc]
---

# :material-file-document-outline: Query from a file

{{ history_chart('basic-example') }}

## :material-file-document-edit-outline: Save as `query.rq`

```sparql
--8<-- "docs/examples/basic-example/input/query.rq"
```

## :material-console: Run the query

```bash
vitrify sparql \
  --endpoint {{ query_endpoint() }} \
  --query query.rq \
  --format csv \
  --to eu-capitals
```

This runs the same query as [EU capitals](eu-capitals.md) and writes the
capture shown below.

{{ directory_preview('basic-example') }}

{{ file_tabs('basic-example') }}
