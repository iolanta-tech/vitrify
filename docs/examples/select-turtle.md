---
hide: [toc]
---

# :material-code-json: SELECT with Turtle requested

{{ history_chart('select-turtle') }}

This example requests Turtle for a `SELECT` query. The endpoint may return
another response format or reject the request. Vitrify records the actual
response type and chooses the filename extension from it, falling back to
`.ttl` if the response media type is missing or unrecognized.

The saved captures below were created by an earlier version that used the
requested extension, so their XML or JSON responses retain the `results.ttl`
filename.

```bash
{{ retrieval_command('select-turtle') }}
```

{{ directory_preview('select-turtle') }}

{{ file_tabs('select-turtle') }}
