vitrify sparql \
  --endpoint https://query.wikidata.org/sparql \
  --query - \
  --format csv \
  --to . <<'SPARQL'
SELECT ?person ?personLabel WHERE {
  ?person wdt:P166 wd:Q37922 ;  # award received: Nobel Prize in Literature
          wdt:P21 wd:Q6581072 . # sex or gender: female
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
ORDER BY ?person
LIMIT 5
SPARQL
