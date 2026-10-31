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

  SELECT ?metaclass ?metaclassLabel ?instanceCount WHERE {
    {
      SELECT ?metaclass (COUNT(DISTINCT ?instance) AS ?instanceCount) WHERE {
        {
          SELECT DISTINCT ?metaclass WHERE {
            ?metaclass wdt:P31/wdt:P279* wd:Q19478619 .
          }
        }
        ?instance wdt:P31 ?metaclass .
      }
      GROUP BY ?metaclass
      ORDER BY DESC(?instanceCount) ?metaclass
    }
    OPTIONAL {
      ?metaclass rdfs:label ?englishLabel .
      FILTER(LANG(?englishLabel) = "en")
    }
    BIND(COALESCE(?englishLabel, STRAFTER(STR(?metaclass), "entity/")) AS ?metaclassLabel)
  }
  ORDER BY DESC(?instanceCount) ?metaclass
---

# :material-sort-numeric-descending: Metaclasses by instance count

The query ranks metaclasses in Wikidata by their number of
distinct direct `instance of` (P31) statements. Candidates are explicitly typed
metaclasses: they have an
`instance of` type equal to [metaclass](https://www.wikidata.org/wiki/Q19478619)
or one of its subclasses, such as second-order class. This follows recorded
types, rather than checking that each instance is itself a class. The counts
use truthy P31 values and do not include instances inherited
through subclasses. Ties are resolved by item URI.
