---
"@context": urn:vitrify:pages
hide: [toc]
audience: user
---

# :material-file-document-edit-outline: Add an example

Add a Markdown page under `docs/examples/`. Its frontmatter supplies the
SPARQL query, the endpoint URL, and an optional requested format:

````markdown
---
"@context": urn:vitrify:examples
endpoints:
  - https://query.wikidata.org/sparql
format: csv
query: |
  PREFIX wd: <http://www.wikidata.org/entity/>
  PREFIX wdt: <http://www.wikidata.org/prop/direct/>

  SELECT ?person WHERE {
    ?person wdt:P31 wd:Q5 .
  }
  LIMIT 5
---

# Five humans

Retrieve five items classified as humans.
````

Use a descriptive filename and one level-one heading. Keep the query complete.
The result preview shows the first five rows. Omit `format` to let the endpoint
choose its response type. The [sparql command](sparql.md) lists accepted format
names.

A context example records a remote JSON-LD context instead of a SPARQL query:

````markdown
---
"@context": urn:vitrify:examples
context: https://www.w3.org/ns/anno.jsonld
---

# Web Annotation
````

Open a pull request that includes the new page.
