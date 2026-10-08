# :material-flask: Examples

Each example shows a saved SPARQL query, a preview of its response, and the
files Vitrify wrote. Open a file link in the directory preview to inspect the
captured source, response, or [RO-Crate](https://www.researchobject.org/ro-crate/)
metadata.

[Query from a file](query-from-file.md) is probably the most production-ready
approach: the query can be versioned and reused in a pipeline. The other
examples use `echo` and standard input to keep their commands self-contained.

- [Female Nobel laureates](female-persons.md) — a CSV result table from
  Wikidata.
- [EU capitals](eu-capitals.md) — five English capital labels in CSV.
- [Query from a file](query-from-file.md) — save the EU-capitals query, then
  run it with `--query query.rq`.
- [Time-bounded subclasses](time-bounded-subclasses.md) — a JSON result table
  with subclass intervals.
- [SELECT response returned as JSON](select-turtle.md) — a format negotiation
  example where the endpoint returned JSON despite a Turtle request.
