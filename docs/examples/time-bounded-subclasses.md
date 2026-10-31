---
"@context": urn:vitrify:examples
hide: [toc]
endpoints:
  - https://query.wikidata.org/sparql
  - https://qlever.dev/api/wikidata
format: json
query: |
  PREFIX p: <http://www.wikidata.org/prop/>
  PREFIX ps: <http://www.wikidata.org/prop/statement/>
  PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
  PREFIX wdt: <http://www.wikidata.org/prop/direct/>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

  PREFIX wd: <http://www.wikidata.org/entity/>
  SELECT DISTINCT ?subclass ?subclassName ?superclass ?superclassName ?start ?end WHERE {
    ?subclass p:P279 ?subclassStatement .
    ?subclassStatement ps:P279 ?superclass ;
                       pq:P580 ?start ;
                       pq:P582 ?end .

    FILTER NOT EXISTS {
      ?subclass wdt:P31/wdt:P279* wd:Q22938576 .   # not a race (competition)
    }

    FILTER NOT EXISTS {
      ?subclass wdt:P31/wdt:P279* wd:Q3139516 .  # not an abbot or other church official
    }

    ?subclass rdfs:label ?subclassName .
    ?superclass rdfs:label ?superclassName .
    FILTER(LANG(?subclassName) = "en")
    FILTER(LANG(?superclassName) = "en")
  }
  ORDER BY ?subclassName ?start ?end
---

# :material-clock-outline: Time-bounded subclasses

This Wikidata query finds subclass statements with start and end qualifiers,
then returns their English labels as SPARQL Results JSON.
