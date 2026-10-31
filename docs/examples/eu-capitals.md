---
"@context": urn:vitrify:examples
hide: [toc]
endpoints:
  - https://query.wikidata.org/sparql
  - https://qlever.dev/api/wikidata
format: csv
query: |
  PREFIX wd: <http://www.wikidata.org/entity/>
  PREFIX wdt: <http://www.wikidata.org/prop/direct/>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

  SELECT ?label
  WHERE {
    ?country wdt:P463 wd:Q458 ;
             wdt:P36 ?capital .
    ?capital rdfs:label ?label .
    FILTER(LANG(?label) = "en")
  }
  ORDER BY ?label
---

# :material-earth: EU capitals

This Wikidata query returns EU-capital labels in English.
