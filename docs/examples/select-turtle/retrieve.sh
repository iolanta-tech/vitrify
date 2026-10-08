echo 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?person ?personName WHERE {
  ?person rdfs:label ?personName .
  FILTER(LANG(?personName) = "en")
}
LIMIT 3' |
  vitrify sparql \
  --endpoint https://qlever.dev/api/wikidata \
  --query - \
  --format turtle \
  --to select-turtle
