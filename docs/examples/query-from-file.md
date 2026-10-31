---
hide: [toc]
---

# :material-file-document-outline: Query from a file

{{ history_chart('eu-capitals') }}

## :material-file-document-edit-outline: Save as `query.rq`

```sparql
{{ query_text('eu-capitals') }}
```

## :material-console: Run the query

```bash
{{ retrieval_command('eu-capitals', query_file='query.rq') }}
```

This runs the same query as [EU capitals](eu-capitals.md) and writes a new capture.

{{ capture_notice('eu-capitals') }}

{{ directory_preview('eu-capitals') }}

{{ file_tabs('eu-capitals') }}
