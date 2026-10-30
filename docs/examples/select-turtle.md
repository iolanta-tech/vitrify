---
"@context": urn:vitrify:examples
hide: [toc]
endpoints:
  - https://query.wikidata.org/sparql
  - https://qlever.dev/api/wikidata
format: turtle
query: |
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

  SELECT ?person ?personName WHERE {
    ?person rdfs:label ?personName .
    FILTER(LANG(?personName) = "en")
  }
  LIMIT 5
---

# :material-code-json: SELECT with Turtle requested

This example requests Turtle for a `SELECT` query. The endpoint may return
another response format or reject the request. Vitrify records the actual
response type and chooses the filename extension from it — for example
`results.xml` or `results.json` — falling back to `.ttl` only if that media
type is missing or unrecognized. Older history entries still use
`results.ttl` from before that naming rule.
