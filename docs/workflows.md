# Local workflows

Treat a Vitrify result as a local input. Keep retrieval as an explicit step and
let analysis targets depend on the saved result file.

For example, from the Vitrify repository root:

```make
QUERY := docs/examples/female-persons/query.rq
CRATE := female-persons
RESULT := $(CRATE)/results.csv

.PHONY: materialize
materialize:
	vitrify sparql \
	  --endpoint https://query.wikidata.org/sparql \
	  --query $(QUERY) \
	  --format csv \
	  --to $(CRATE)

names.txt: $(RESULT)
	cut -d, -f2 $< | tail -n +2 > $@
```

Run `make materialize` when you intend to contact Wikidata and retrieve a new
result. The `names.txt` target reads the existing CSV and does not contact the
endpoint. Use the same pattern with other local tools, including
[sparqld](https://sparqld.iolanta.tech).

See the [command reference](command.md) for query input and output format
options.
