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

  SELECT DISTINCT ?class ?classLabel WHERE {
    ?class wdt:P31/wdt:P279* wd:Q24027474 .
    OPTIONAL {
      ?class rdfs:label ?englishLabel .
      FILTER(LANG(?englishLabel) = "en")
    }
    BIND(COALESCE(?englishLabel, STRAFTER(STR(?class), "entity/")) AS ?classLabel)
  }
  ORDER BY ?classLabel ?class
---

# :material-layers: Fourth-order classes

The query lists all items in Wikidata whose recorded
`instance of` (P31) type is
[fourth-order class](https://www.wikidata.org/wiki/Q24027474) or a subclass
of that type, ordered by English label and item URI. A fourth-order class has
third-order classes as its instances. This query selects recorded types;
it does not check the order of every instance.
