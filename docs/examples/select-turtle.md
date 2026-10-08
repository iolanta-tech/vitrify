---
hide: [toc]
---

# :material-code-json: SELECT response returned as JSON

This example asks QLever for Turtle while running a `SELECT` query. The
endpoint returns SPARQL Results JSON, and Vitrify records that actual response
type even though the requested format determines the `results.ttl` filename.

```bash
--8<-- "docs/examples/select-turtle/retrieve.sh"
```

{{ directory_preview('select-turtle') }}

{{ file_tabs('select-turtle') }}
