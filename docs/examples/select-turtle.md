---
hide: [toc]
---

# :material-code-json: SELECT with Turtle requested

{{ history_chart('select-turtle') }}

This example requests Turtle for a `SELECT` query. The endpoint may return
another response format or reject the request. Vitrify records the actual
response type and chooses the filename extension from it — for example
`results.xml` or `results.json` — falling back to `.ttl` only if that media
type is missing or unrecognized. Older history entries still use
`results.ttl` from before that naming rule.

```bash
{{ retrieval_command('select-turtle') }}
```

{{ directory_preview('select-turtle') }}

{{ file_tabs('select-turtle') }}
