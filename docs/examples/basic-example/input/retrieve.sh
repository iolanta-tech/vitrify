vitrify sparql \
  --endpoint https://query.wikidata.org/sparql \
  --query - \
  --format csv \
  --to output <<'SPARQL'
SELECT ?label WHERE { wd:Q42 rdfs:label ?label . FILTER(LANG(?label) = "en") }
SPARQL
