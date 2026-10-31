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

  SELECT ?metaclass ?metaclassLabel ?instanceCount ?exampleInstance ?exampleInstanceLabel WHERE {
    {
      SELECT ?metaclass (COUNT(DISTINCT ?instance) AS ?instanceCount)
             (MIN(STR(?instance)) AS ?exampleInstanceIRI) WHERE {
        {
          SELECT DISTINCT ?metaclass WHERE {
            ?metaclass wdt:P31/wdt:P279* wd:Q19478619 .
          }
        }
        ?instance wdt:P31 ?metaclass .
        FILTER NOT EXISTS {
          ?counterexample wdt:P31 ?metaclass .
          FILTER NOT EXISTS {
            ?counterexample wdt:P31/wdt:P279* wd:Q19478619 .
          }
        }
      }
      GROUP BY ?metaclass
      ORDER BY DESC(?instanceCount) ?metaclass
    }
    BIND(IRI(?exampleInstanceIRI) AS ?exampleInstance)
    OPTIONAL {
      ?metaclass rdfs:label ?englishLabel .
      FILTER(LANG(?englishLabel) = "en")
    }
    OPTIONAL {
      ?exampleInstance rdfs:label ?exampleEnglishLabel .
      FILTER(LANG(?exampleEnglishLabel) = "en")
    }
    BIND(COALESCE(?englishLabel, STRAFTER(STR(?metaclass), "entity/")) AS ?metaclassLabel)
    BIND(COALESCE(?exampleEnglishLabel, STRAFTER(STR(?exampleInstance), "entity/")) AS ?exampleInstanceLabel)
  }
  ORDER BY DESC(?instanceCount) ?metaclass
---

# :material-layers-triple: Metaclasses of metaclasses

The query finds explicitly typed metaclasses in Wikidata
whose recorded direct instances are all explicitly typed metaclasses too.
It requires at least one instance, ranks matches by distinct
instance count, and shows one example instance per match. Metaclass typing
uses `instance of` (P31), followed by the type's `subclass of` (P279) hierarchy
to [metaclass](https://www.wikidata.org/wiki/Q19478619).

Wikidata calls a class of second-order classes a
[third-order class](https://www.wikidata.org/wiki/Q24017465).
The query also allows mixed or higher orders. It checks recorded truthy P31
values; missing metaclass typing excludes a candidate, and unrecorded
instances cannot be checked. Ties and example instances are selected by URI.
