echo 'SELECT ?label WHERE { ?country wdt:P463 wd:Q458; wdt:P36 ?capital . ?capital rdfs:label ?label . FILTER(LANG(?label) = "en") } ORDER BY ?label LIMIT 5' |
  vitrify sparql \
  --endpoint https://query.wikidata.org/sparql \
  --query - \
  --format csv \
  --to eu-capitals
